"""
codemind_okf/core/writer.py — OKF Markdown File Writer
========================================================
Writes a ModuleSummary + ParsedFile to a .okf/modules/*.md file.
Output always goes to <project_root>/.okf/ — never inside app.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from codemind_okf.core.parser import ParsedFile
from codemind_okf.core.summarizer import ModuleSummary
from codemind_okf.core.file_utils import safe_write


def write_okf_file(
    bundle_root: Path,
    parsed: ParsedFile,
    summary: ModuleSummary,
) -> Path:
    """
    Write a single OKF concept file to the bundle's modules/ directory.

    Source: my-project/src/auth/auth_router.py
    Output: my-project/.okf/modules/src-auth-auth-router.md
    """
    modules_dir = bundle_root / "modules"

    # Slug: "src/auth/auth_router.py" → "src-auth-auth-router.md"
    slug = (
        parsed.file_path
        .replace("/", "-").replace("\\", "-").replace("_", "-")
    )
    slug = slug.rsplit(".", 1)[0] + ".md"

    output_path = modules_dir / slug
    safe_write(output_path, _render(parsed, summary))
    return output_path


def _sanitize_yaml_str(text: str, max_len: int = 500) -> str:
    """Collapse multi-line text to a single quoted YAML value safe string."""
    # Take first meaningful paragraph, strip =====/----- underlines
    lines = [l for l in text.strip().splitlines() if not set(l.strip()) <= {"=", "-", "#"}]
    single = " ".join(l.strip() for l in lines if l.strip())
    single = single[:max_len]
    # Escape internal double-quotes for YAML double-quote wrapping
    single = single.replace('"', "'")
    return single


def _sanitize_yaml_item(val: str) -> str:
    """Sanitize and quote YAML list items that contain reserved characters like @, :, #, etc."""
    val = str(val).strip().replace('"', "'")
    if not val:
        return '""'
    if any(c in val for c in (":", "@", "#", "{", "}", "[", "]", ",", "&", "*", "!", "|", ">", "%", " ", "-")):
        return f'"{val}"'
    return val


def _render(parsed: ParsedFile, summary: ModuleSummary) -> str:
    """Render the full OKF Markdown file with YAML frontmatter."""
    today = date.today().isoformat()

    tags_yaml = "\n".join(f"  - {_sanitize_yaml_item(t)}" for t in summary.tags)
    key_funcs_yaml = (
        "\n".join(f"  - {_sanitize_yaml_item(fn)}" for fn in summary.key_functions)
        if summary.key_functions else "  []"
    )

    # CRITICAL: description and title MUST be safe YAML strings
    safe_title = _sanitize_yaml_item(summary.title)
    safe_description = _sanitize_yaml_str(summary.description)

    frontmatter = f"""---
type: {summary.type}
title: {safe_title}
description: "{safe_description}"
resource: {parsed.file_path}
tags:
{tags_yaml if tags_yaml else "  []"}
key_functions:
{key_funcs_yaml}
timestamp: {today}
---"""

    body_lines = [
        f"# {summary.title}",
        "",
        f"> **File:** `{parsed.file_path}`  ",
        f"> **Language:** {parsed.language}  ",
        f"> **Lines:** {parsed.line_count}",
        "",
        "---",
        "",
        "## 📋 Purpose",
        "",
        summary.purpose or summary.description,
        "",
        "## 🔧 Key Components",
        "",
    ]

    if parsed.functions:
        body_lines.append("### Functions")
        body_lines.append("")
        for fn in parsed.functions[:10]:
            async_tag = "⚡ async " if fn.is_async else ""
            args_str = ", ".join(fn.args[:5])
            body_lines.append(f"#### `{async_tag}{fn.name}({args_str})`")
            if fn.docstring:
                # Expanded to 400 chars for richer AI context
                body_lines.append(fn.docstring.strip()[:400])
            body_lines.append("")

    if parsed.classes:
        body_lines.append("### Classes")
        body_lines.append("")
        for cls in parsed.classes[:5]:
            bases = f" ← `{', '.join(cls.base_classes)}`" if cls.base_classes else ""
            body_lines.append(f"#### `{cls.name}`{bases}")
            if cls.docstring:
                body_lines.append(cls.docstring.strip()[:400])
            if cls.methods:
                method_names = ", ".join(f"`{m.name}`" for m in cls.methods[:8])
                body_lines.append(f"**Methods:** {method_names}")
            body_lines.append("")

    if parsed.imports:
        body_lines += [
            "## 🔗 Dependencies",
            "",
            summary.depends_on_notes,
            "",
            "**Key imports:**",
        ]
        for imp in parsed.imports[:8]:
            body_lines.append(f"- `{imp}`")
        body_lines.append("")

    body_lines += [
        "---",
        "",
        "## 🤖 AI Navigation Hints",
        "",
        "_Tags for AI IDE context retrieval:_",
        "",
        " · ".join(f"`{t}`" for t in summary.tags),
        "",
    ]

    return f"{frontmatter}\n\n" + "\n".join(body_lines)
