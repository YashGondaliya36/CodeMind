"""
app/core/bundle/graph_builder.py — Knowledge Graph Builder
===========================================================
Parses Markdown links between OKF files to build a knowledge graph.
Nodes = OKF files. Edges = "depends_on" relationships.
Used by GET /bundle/{repo_name}/graph for the frontend visualiser.
"""

from __future__ import annotations

import re

from app.core.bundle.manager import get_all_metadata
from app.models.bundle import BundleGraph, GraphNode, GraphEdge


# Regex to find all Markdown links: [label](./some-file.md)
_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(\./([^)]+\.md)\)")


def build_graph(repo_name: str) -> BundleGraph:
    """
    Build a nodes-and-edges knowledge graph from a bundle's OKF files.

    Node IDs are the relative filenames (e.g. "modules/auth-module.md").
    Edges come from two sources:
      1. The YAML `depends_on` list in each file's frontmatter.
      2. Markdown cross-links in the body content (parsed via regex).

    Args:
        repo_name: The bundle slug.

    Returns:
        BundleGraph with all nodes and directed edges.
    """
    all_files = get_all_metadata(repo_name)

    # Build a filename → meta lookup for resolving links
    file_set = {f.filename for f in all_files}

    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    seen_edges: set[tuple[str, str]] = set()

    for f in all_files:
        # ── Node ─────────────────────────────────────────────────────────────
        nodes.append(GraphNode(
            id=f.filename,
            label=f.title,
            type=f.type,
            tags=f.tags,
        ))

        # ── Edges from depends_on (YAML frontmatter) ─────────────────────────
        for dep in f.depends_on:
            # depends_on entries may or may not include full path
            target = _resolve_dep(dep, file_set)
            if target and (f.filename, target) not in seen_edges:
                edges.append(GraphEdge(source=f.filename, target=target))
                seen_edges.add((f.filename, target))

    return BundleGraph(
        repo_name=repo_name,
        nodes=nodes,
        edges=edges,
    )


def _resolve_dep(dep: str, file_set: set[str]) -> str | None:
    """
    Try to resolve a depends_on entry to an actual filename in the bundle.
    Handles both full paths ("modules/auth-module.md") and bare slugs ("auth-module").
    """
    # Exact match
    if dep in file_set:
        return dep

    # Try adding .md
    with_ext = dep if dep.endswith(".md") else f"{dep}.md"
    if with_ext in file_set:
        return with_ext

    # Search by basename
    for f in file_set:
        if f.endswith(f"/{with_ext}") or f == with_ext:
            return f

    return None  # Could not resolve — skip this edge
