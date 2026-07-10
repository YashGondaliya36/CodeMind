"""
app/core/agent/metadata_scanner.py — Fast Frontmatter Scanner
==============================================================
Reads ONLY the YAML frontmatter of every OKF file in a bundle.
This is the first step of selective retrieval — cheap, no LLM needed.

The key insight of OKF:
  → Scan metadata of ALL files (tiny cost)
  → Fetch full content of ONLY relevant files (selective cost)
"""

from __future__ import annotations

from app.core.bundle.manager import get_all_metadata
from app.models.bundle import OKFFileMeta


def scan_all_metadata(repo_name: str) -> list[OKFFileMeta]:
    """
    Retrieve the YAML frontmatter of every OKF file in a bundle.

    This is intentionally a pure metadata read — NO file bodies are loaded.
    Each metadata object is tiny (a few hundred bytes) so scanning hundreds
    of files costs almost nothing.

    Args:
        repo_name: The bundle slug.

    Returns:
        List of OKFFileMeta objects (one per .md file in the bundle).
        Empty list if the bundle doesn't exist.
    """
    return get_all_metadata(repo_name)


def get_metadata_summary(repo_name: str) -> dict:
    """
    Return a high-level summary of the bundle for diagnostic purposes.
    Used by the agent to understand what it's working with.
    """
    all_meta = scan_all_metadata(repo_name)

    type_counts: dict[str, int] = {}
    all_tags: list[str] = []

    for m in all_meta:
        type_counts[m.type] = type_counts.get(m.type, 0) + 1
        all_tags.extend(m.tags)

    # Most common tags
    tag_freq: dict[str, int] = {}
    for tag in all_tags:
        tag_freq[tag] = tag_freq.get(tag, 0) + 1

    top_tags = sorted(tag_freq, key=lambda t: tag_freq[t], reverse=True)[:10]

    return {
        "total_files": len(all_meta),
        "types": type_counts,
        "top_tags": top_tags,
        "has_index": any(m.filename == "index.md" for m in all_meta),
    }
