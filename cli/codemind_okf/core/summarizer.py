"""
codemind_okf/core/summarizer.py — Fast AST-Based Module Summarizer
====================================================================
Generates a ModuleSummary deterministically from AST output.
Zero LLM cost. Standalone.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from codemind_okf.core.parser import ParsedFile


# Tags from these stdlib/common modules are noise for AI retrieval — filter them out
_TAG_BLOCKLIST = {
    "__future__", "dataclasses", "pathlib", "os", "sys", "re", "abc",
    "typing", "collections", "functools", "itertools", "io", "enum",
    "json", "logging", "datetime", "time", "math", "copy", "shutil",
    "contextlib", "traceback", "inspect", "threading", "subprocess",
}


@dataclass
class ModuleSummary:
    """Full structured summary of a module."""
    title: str
    description: str
    purpose: str
    key_functions: list[str]
    tags: list[str]
    type: str
    depends_on_notes: str = "Dependencies extracted via AST."
    raw_llm_output: str = "[FAST MODE - NO LLM OUTPUT]"


def summarize_fast(parsed: ParsedFile) -> ModuleSummary:
    """
    Generate a ModuleSummary from AST output — fast, deterministic, $0 cost.
    """
    path_obj = Path(parsed.file_path)
    filename = path_obj.name
    stem = filename.rsplit(".", 1)[0]

    # Title: include parent folder for uniqueness — "Graph Page" not just "Page"
    parts = path_obj.parts
    if len(parts) >= 2:
        parent = parts[-2]
        # Skip generic folder names that add no meaning
        _SKIP_PARENTS = {"src", "app", "lib", "core", "pages", "components", "utils", "api"}
        if parent.lower() not in _SKIP_PARENTS:
            title = (
                f"{parent.replace('_', ' ').replace('-', ' ').title()} "
                f"{stem.replace('_', ' ').replace('-', ' ').title()}"
            ).strip()
        else:
            title = stem.replace("_", " ").replace("-", " ").title()
    else:
        title = stem.replace("_", " ").replace("-", " ").title()

    # Type via path heuristics
    lower_path = parsed.file_path.lower()
    mod_type = "module"
    if any(k in lower_path for k in ("api", "route", "controller", "router", "endpoint")):
        mod_type = "api"
    elif any(k in lower_path for k in ("db", "database", "schema", "model", "orm", "repo")):
        mod_type = "database"
    elif any(k in lower_path for k in ("config", "setting", "env", "conf")):
        mod_type = "config"
    elif "test" in lower_path:
        mod_type = "test"
    elif any(k in lower_path for k in ("component", "ui", "view", "page")):
        mod_type = "concept"

    # Build tags — filter out stdlib noise so only meaningful module-level tags remain
    tags: set[str] = {mod_type}
    if len(path_obj.parts) > 1:
        parent = path_obj.parts[-2].lower()
        if parent not in ("src", "app", "components", "pages", "lib", "core", "utils", "."):
            tags.add(parent)
    for imp in parsed.imports[:8]:
        if not imp.startswith("."):
            base = imp.split(".")[0].lower()
            if base not in _TAG_BLOCKLIST and len(base) > 2:
                tags.add(base)

    # Key functions & classes
    key_functions = [f.name for f in parsed.functions[:5]] + [c.name for c in parsed.classes[:3]]
    class_names = [c.name for c in parsed.classes[:3]]

    # Description & purpose
    if parsed.module_docstring:
        description = parsed.module_docstring.strip().split("\n\n")[0]
        # Remove === / --- underlines that break YAML
        desc_lines = [l for l in description.splitlines() if not set(l.strip()) <= {"=", "-"}]
        description = " ".join(l.strip() for l in desc_lines if l.strip())
        if len(description) > 500:
            description = description[:497] + "..."
        purpose = description
    else:
        if class_names:
            description = f"Contains {', '.join(class_names)} {'class' if len(class_names)==1 else 'classes'}."
        elif parsed.functions:
            func_names = [f.name for f in parsed.functions[:4]]
            description = f"Provides: {', '.join(func_names)}."
        else:
            description = f"Configuration or type definition module for {title}."
        purpose = description
    return ModuleSummary(
        title=title,
        description=description,
        purpose=purpose,
        key_functions=key_functions,
        tags=list(tags)[:6],
        type=mod_type,
    )
