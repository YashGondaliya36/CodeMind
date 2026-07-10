"""
app/core/producer/okf_writer.py — OKF Markdown File Writer
===========================================================
Takes a ModuleSummary and a ParsedFile and writes a properly formatted
OKF concept file (.md with YAML frontmatter) to the bundle directory.

This is the final step of the Producer pipeline:
  crawl → parse → summarize → [write OKF file] ← here
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from app.config import settings
from app.core.producer.parser import ParsedFile
from app.core.producer.summarizer import ModuleSummary
from app.utils.file_utils import safe_write


def write_okf_file(
    repo_name: str,
    parsed: ParsedFile,
    summary: ModuleSummary,
) -> Path:
    """
    Write a single OKF concept file for a source module.

    The output path mirrors the source file's relative path but
    lives inside the OKF bundle directory.

    Example:
      Source:  <repo>/src/auth/auth.py
      OKF:     okf_bundles/<repo_name>/modules/src-auth-auth.md

    Args:
        repo_name: Bundle slug.
        parsed:    Static analysis result from parser.py.
        summary:   LLM-generated summary from summarizer.py.

    Returns:
        Absolute Path of the written OKF file.
    """
    bundle_root = settings.bundles_path / repo_name / "modules"

    # Convert relative file path to a safe filename slug
    # "src/auth/auth.py" → "src-auth-auth.md"
    slug = parsed.file_path.replace("/", "-").replace("\\", "-").replace("_", "-")
    slug = slug.rsplit(".", 1)[0] + ".md"   # replace extension with .md

    output_path = bundle_root / slug

    content = _render_okf_file(parsed, summary)
    safe_write(output_path, content)

    return output_path


def _render_okf_file(parsed: ParsedFile, summary: ModuleSummary) -> str:
    """
    Render the full OKF Markdown file content.
    Structure: YAML frontmatter + rich Markdown body.
    """
    today = date.today().isoformat()

    # ── YAML Frontmatter ──────────────────────────────────────────────────────
    tags_yaml = "\n".join(f"  - {tag}" for tag in summary.tags)
    depends_yaml = (
        "\n".join(f"  - {dep}" for dep in summary.key_functions[:3])
        if summary.key_functions else "  []"
    )

    frontmatter = f"""---
type: {summary.type}
title: {summary.title}
description: {summary.description}
resource: {parsed.file_path}
tags:
{tags_yaml if tags_yaml else "  []"}
timestamp: {today}
---"""

    # ── Markdown Body ─────────────────────────────────────────────────────────
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

    # Functions section
    if parsed.functions:
        body_lines.append("### Functions")
        body_lines.append("")
        for fn in parsed.functions[:10]:
            async_tag = "⚡ async " if fn.is_async else ""
            args_str = ", ".join(fn.args[:5])
            body_lines.append(f"#### `{async_tag}{fn.name}({args_str})`")
            if fn.docstring:
                body_lines.append(f"{fn.docstring[:200]}")
            body_lines.append("")

    # Classes section
    if parsed.classes:
        body_lines.append("### Classes")
        body_lines.append("")
        for cls in parsed.classes[:5]:
            bases = f" ← `{', '.join(cls.base_classes)}`" if cls.base_classes else ""
            body_lines.append(f"#### `{cls.name}`{bases}")
            if cls.docstring:
                body_lines.append(f"{cls.docstring[:200]}")
            if cls.methods:
                method_names = ", ".join(f"`{m.name}`" for m in cls.methods[:6])
                body_lines.append(f"**Methods:** {method_names}")
            body_lines.append("")

    # Dependencies section
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

    # Agent navigation hint
    body_lines += [
        "---",
        "",
        "## 🤖 Agent Navigation Hints",
        "",
        "_Use these tags to find related concept files:_",
        "",
        " · ".join(f"`{t}`" for t in summary.tags),
        "",
    ]

    body = "\n".join(body_lines)
    return f"{frontmatter}\n\n{body}"
