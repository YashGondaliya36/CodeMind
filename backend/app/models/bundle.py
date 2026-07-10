"""
app/models/bundle.py — OKF Bundle Pydantic Schemas
====================================================
Request and response models for the /bundle endpoints.
"""

from typing import Optional
from pydantic import BaseModel, Field


class OKFFileMeta(BaseModel):
    """
    The parsed YAML frontmatter of one OKF concept file.
    Mirrors the OKF spec fields exactly.
    """

    filename: str                           # e.g. "modules/auth-module.md"
    type: str                               # e.g. "module" | "architecture" | "concept"
    title: str
    description: Optional[str] = None
    tags: list[str] = []
    depends_on: list[str] = []             # Other OKF file slugs this one references
    resource: Optional[str] = None         # Path to the actual source file
    timestamp: Optional[str] = None        # ISO date string


class OKFFileDetail(OKFFileMeta):
    """OKFFileMeta + the full Markdown body content."""

    content: str                            # Full Markdown body (after frontmatter)
    raw: str                                # Complete raw file (frontmatter + body)


class BundleIndex(BaseModel):
    """Response for GET /bundle/{repo_name}/files"""

    repo_name: str
    total_files: int
    files: list[OKFFileMeta]
    index_md_exists: bool


class GraphNode(BaseModel):
    """One node in the knowledge graph."""

    id: str         # Filename used as unique node ID
    label: str      # Display name (title)
    type: str       # Node colour/shape category
    tags: list[str] = []


class GraphEdge(BaseModel):
    """One directed edge between two OKF files."""

    source: str     # Filename of the file that contains the link
    target: str     # Filename of the linked file


class BundleGraph(BaseModel):
    """Response for GET /bundle/{repo_name}/graph"""

    repo_name: str
    nodes: list[GraphNode]
    edges: list[GraphEdge]
