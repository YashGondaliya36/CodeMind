"""
app/core/producer/template_summarizer.py — Fast AST-Based Module Summarizer
============================================================================
Takes a ParsedFile (structured static analysis output) and instantly generates
a ModuleSummary without calling an LLM.

This is the "Fast Mode" alternative to the LLM summarizer. It is 100x faster
and costs $0, but relies entirely on developer docstrings and file naming
heuristics for metadata.
"""

from __future__ import annotations

from pathlib import Path
from app.core.producer.parser import ParsedFile
from app.core.producer.summarizer import ModuleSummary


def summarize_file_fast(parsed: ParsedFile) -> ModuleSummary:
    """
    Generate a ModuleSummary deterministically from the AST without an LLM.
    """
    path_obj = Path(parsed.file_path)
    filename = path_obj.name
    
    # Title from filename (e.g. "auth_router.py" -> "Auth Router")
    title = filename.replace("_", " ").replace("-", " ").replace(".py", "").replace(".ts", "").replace(".js", "").replace(".tsx", "").replace(".jsx", "").title()
    
    # Determine type based on heuristics
    lower_path = parsed.file_path.lower()
    mod_type = "module"
    if "api" in lower_path or "route" in lower_path or "controller" in lower_path:
        mod_type = "api"
    elif "db" in lower_path or "database" in lower_path or "schema" in lower_path:
        mod_type = "database"
    elif "config" in lower_path or "env" in lower_path or "setting" in lower_path:
        mod_type = "config"
    elif "test" in lower_path:
        mod_type = "test"
    elif "component" in lower_path or "ui" in lower_path:
        mod_type = "concept"
    
    # Auto-generate tags
    tags = set()
    tags.add(mod_type)
    
    # Add parent folder name as a tag (ignore generic ones like src, app)
    if len(path_obj.parts) > 1:
        parent = path_obj.parts[-2].lower()
        if parent not in ("src", "app", "components", "pages", "lib", "core", "utils"):
            tags.add(parent)
    
    # Add top-level imports as tags (e.g. "fastapi", "react")
    for imp in parsed.imports[:5]:
        if not imp.startswith("."):
            base_module = imp.split(".")[0]
            if base_module not in ("os", "sys", "typing", "pathlib", "json", "datetime"):
                tags.add(base_module.lower())
            
    # Key functions from AST
    key_functions = []
    class_names = []
    for f in parsed.functions[:5]:
        key_functions.append(f.name)
    for c in parsed.classes[:3]:
        key_functions.append(c.name)
        class_names.append(c.name)
        
    # Auto-generate a smarter description if no docstring is present
    if not parsed.module_docstring:
        desc_parts = []
        if class_names:
            desc_parts.append(f"Contains definitions for {', '.join(class_names)}.")
        elif parsed.functions:
            func_names = [f.name for f in parsed.functions[:3]]
            desc_parts.append(f"Contains functions such as {', '.join(func_names)}.")
            
        if desc_parts:
            description = " ".join(desc_parts)
        else:
            description = "Structural module containing configuration, exports, or data schemas."
            
        purpose = f"Provides core logic and definitions for the {title} component."
    else:
        description = parsed.module_docstring.strip().split("\n\n")[0]
        if len(description) > 300:
            description = description[:297] + "..."
        purpose = f"This module provides functionality for {title.lower()}."
    
    return ModuleSummary(
        title=title,
        description=description,
        purpose=purpose,
        key_functions=key_functions,
        tags=list(tags)[:6],  # Max 6 tags
        type=mod_type,
        depends_on_notes="Dependencies extracted structurally via AST.",
        raw_llm_output="[FAST MODE - NO LLM OUTPUT]"
    )
