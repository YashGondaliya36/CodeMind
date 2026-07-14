"""
app/core/producer/parser.py — Source Code AST Parser
======================================================
Extracts structured information from source files WITHOUT calling the LLM.
This is pure static analysis — fast, deterministic, and free.

Extracted info feeds the summarizer prompt, giving the LLM structured
input instead of raw source code (saves tokens, improves quality).
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path

from app.utils.file_utils import safe_read

try:
    from tree_sitter import Language, Parser
    import tree_sitter_javascript as tsjavascript
    import tree_sitter_typescript as tstypescript
    TS_AVAILABLE = True
except ImportError:
    TS_AVAILABLE = False



@dataclass
class FunctionInfo:
    """Represents a parsed function or method."""
    name: str
    docstring: str | None
    args: list[str]
    is_async: bool
    line_number: int
    decorators: list[str] = field(default_factory=list)


@dataclass
class ClassInfo:
    """Represents a parsed class definition."""
    name: str
    docstring: str | None
    base_classes: list[str]
    methods: list[FunctionInfo]
    line_number: int


@dataclass
class ParsedFile:
    """
    Structured representation of a source file after static analysis.
    This is passed to the summarizer to build the LLM prompt.
    """
    file_path: str          # Relative path (for display)
    language: str
    module_docstring: str | None
    imports: list[str]      # What this file depends on
    functions: list[FunctionInfo]
    classes: list[ClassInfo]
    line_count: int
    parse_error: str | None = None  # Set if parsing failed


def parse_file(file_path: Path, relative_path: str, language: str) -> ParsedFile:
    """
    Parse a source file and extract structured information.

    Args:
        file_path:     Absolute path to the source file.
        relative_path: Relative path from repo root (for display only).
        language:      "python" | "javascript" | "typescript"

    Returns:
        ParsedFile with all extracted information.
    """
    source = safe_read(file_path)
    if source is None:
        return ParsedFile(
            file_path=relative_path,
            language=language,
            module_docstring=None,
            imports=[],
            functions=[],
            classes=[],
            line_count=0,
            parse_error="File could not be read.",
        )

    line_count = source.count("\n") + 1

    if language == "python":
        return _parse_python(source, relative_path, line_count)
    else:
        # For JS/TS: use lightweight regex-based extraction
        return _parse_js_ts(source, relative_path, language, line_count)


# ── Python Parser (AST-based) ─────────────────────────────────────────────────

def _parse_python(source: str, file_path: str, line_count: int) -> ParsedFile:
    """Parse Python source using the built-in `ast` module."""
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return ParsedFile(
            file_path=file_path,
            language="python",
            module_docstring=None,
            imports=[],
            functions=[],
            classes=[],
            line_count=line_count,
            parse_error=f"SyntaxError: {e}",
        )

    module_docstring = ast.get_docstring(tree)
    imports = _extract_python_imports(tree)
    functions = []
    classes = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Only top-level functions (not methods — those go under classes)
            if isinstance(node.col_offset, int) and node.col_offset == 0:
                functions.append(_extract_python_function(node))

        elif isinstance(node, ast.ClassDef):
            classes.append(_extract_python_class(node))

    return ParsedFile(
        file_path=file_path,
        language="python",
        module_docstring=module_docstring,
        imports=imports,
        functions=functions,
        classes=classes,
        line_count=line_count,
    )


def _get_node_name(node: ast.expr) -> str:
    """Helper to safely extract a readable name from an AST node."""
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Attribute):
        if hasattr(node.value, "id"):
            return f"{node.value.id}.{node.attr}"
        return node.attr
    return "unknown"


def _extract_python_function(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> FunctionInfo:
    args = [arg.arg for arg in node.args.args]
    decorators = [_get_node_name(dec) for dec in node.decorator_list]

    return FunctionInfo(
        name=node.name,
        docstring=ast.get_docstring(node),
        args=args,
        is_async=isinstance(node, ast.AsyncFunctionDef),
        line_number=node.lineno,
        decorators=decorators,
    )


def _extract_python_class(node: ast.ClassDef) -> ClassInfo:
    bases = [_get_node_name(base) for base in node.bases]

    methods = []
    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            methods.append(_extract_python_function(item))

    return ClassInfo(
        name=node.name,
        docstring=ast.get_docstring(node),
        base_classes=bases,
        methods=methods,
        line_number=node.lineno,
    )


def _extract_python_imports(tree: ast.AST) -> list[str]:
    """Extract all import statements from a Python AST."""
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            imports.append(module)
    return sorted(set(imports))


# ── JavaScript / TypeScript Parser (Regex-based) ─────────────────────────────

def _parse_js_ts(
    source: str, file_path: str, language: str, line_count: int
) -> ParsedFile:
    """
    Parse JS/TS files using Tree-sitter if available, otherwise fallback to Regex.
    """
    if not TS_AVAILABLE:
        functions = _extract_js_functions_regex(source)
        classes = _extract_js_classes_regex(source)
        imports = _extract_js_imports_regex(source)
        return ParsedFile(
            file_path=file_path, language=language, module_docstring=None,
            imports=imports, functions=functions, classes=classes, line_count=line_count,
        )

    # Initialize language based on file extension
    if file_path.endswith(".ts"):
        lang = Language(tstypescript.language_typescript())
    elif file_path.endswith(".tsx"):
        lang = Language(tstypescript.language_tsx())
    else:
        lang = Language(tsjavascript.language())

    parser = Parser(lang)
    tree = parser.parse(source.encode("utf8"))

    # Define queries
    import_query = lang.query("(import_statement source: (string) @import)")
    
    function_query = lang.query("""
        (function_declaration name: (identifier) @name parameters: (formal_parameters) @params)
        (lexical_declaration (variable_declarator name: (identifier) @name value: (arrow_function parameters: (formal_parameters) @params)))
        (lexical_declaration (variable_declarator name: (identifier) @name value: (function parameters: (formal_parameters) @params)))
    """)
    
    class_query = lang.query("""
        (class_declaration name: (identifier) @name)
    """)

    imports = []
    for match in import_query.matches(tree.root_node):
        for node in match[1].values():
            if isinstance(node, list):
                node = node[0]
            val = node.text.decode("utf8")
            imports.append(val.strip("'\""))
    imports = sorted(set(imports))

    functions = []
    for match in function_query.matches(tree.root_node):
        nodes = match[1]
        name_node = nodes.get("name")
        params_node = nodes.get("params")
        if isinstance(name_node, list): name_node = name_node[0]
        if isinstance(params_node, list): params_node = params_node[0]
        
        if name_node and params_node:
            name = name_node.text.decode("utf8")
            params = params_node.text.decode("utf8").strip("()").split(",")
            params = [p.strip() for p in params if p.strip()]
            
            # Simple async check on the raw text
            is_async = b"async" in source[:name_node.start_byte][-20:].lower()
            
            functions.append(FunctionInfo(
                name=name, docstring=None, args=params, 
                is_async=is_async, line_number=name_node.start_point[0] + 1
            ))

    classes = []
    for match in class_query.matches(tree.root_node):
        nodes = match[1]
        name_node = nodes.get("name")
        if isinstance(name_node, list): name_node = name_node[0]
        if name_node:
            classes.append(ClassInfo(
                name=name_node.text.decode("utf8"), docstring=None, 
                base_classes=[], methods=[], line_number=name_node.start_point[0] + 1
            ))

    return ParsedFile(
        file_path=file_path, language=language, module_docstring=None,
        imports=imports, functions=functions, classes=classes, line_count=line_count,
    )


def _extract_js_functions_regex(source: str) -> list[FunctionInfo]:
    patterns = [
        r"(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)",
        r"(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s+)?\(([^)]*)\)\s*=>",
        r"(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s+)?function\s*\(([^)]*)\)",
    ]
    functions = []
    for pattern in patterns:
        for match in re.finditer(pattern, source):
            name = match.group(1)
            args_str = match.group(2)
            args = [a.strip() for a in args_str.split(",") if a.strip()]
            functions.append(FunctionInfo(
                name=name, docstring=None, args=args,
                is_async="async" in match.group(0),
                line_number=source[: match.start()].count("\n") + 1,
            ))
    return functions


def _extract_js_classes_regex(source: str) -> list[ClassInfo]:
    pattern = r"(?:export\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?"
    classes = []
    for match in re.finditer(pattern, source):
        classes.append(ClassInfo(
            name=match.group(1), docstring=None,
            base_classes=[match.group(2)] if match.group(2) else [],
            methods=[], line_number=source[: match.start()].count("\n") + 1,
        ))
    return classes


def _extract_js_imports_regex(source: str) -> list[str]:
    imports = set()
    for match in re.finditer(r"import\s+.*?\s+from\s+['\"]([^'\"]+)['\"]", source):
        imports.add(match.group(1))
    for match in re.finditer(r"require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)", source):
        imports.add(match.group(1))
    return sorted(imports)
