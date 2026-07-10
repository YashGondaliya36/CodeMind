"""
app/api/routes/bundle.py — OKF Bundle Endpoints
================================================
Thin HTTP layer — all logic delegates to core/bundle/
"""

from fastapi import APIRouter, HTTPException

from app.core.bundle.manager import (
    bundle_exists,
    list_bundle_files,
    get_file_detail,
    delete_bundle,
)
from app.core.bundle.graph_builder import build_graph
from app.models.bundle import BundleIndex, OKFFileDetail, BundleGraph

router = APIRouter()


@router.get(
    "/{repo_name}/files",
    response_model=BundleIndex,
    summary="List all OKF files in a bundle",
)
async def list_files(repo_name: str):
    """
    Returns metadata (frontmatter) for every OKF concept file in the bundle.
    Does NOT return file bodies — use /file/{filename} for that.
    This is intentionally lightweight so the frontend can render the file list quickly.
    """
    if not bundle_exists(repo_name):
        raise HTTPException(
            status_code=404,
            detail=f"No OKF bundle found for repo '{repo_name}'. "
                   f"Run POST /repo/analyze first.",
        )
    return list_bundle_files(repo_name)


@router.get(
    "/{repo_name}/file/{filename:path}",
    response_model=OKFFileDetail,
    summary="Get full content of a specific OKF file",
)
async def get_file(repo_name: str, filename: str):
    """
    Returns the complete content (frontmatter + Markdown body) of one OKF file.

    The `filename` parameter supports nested paths, e.g.:
    `GET /bundle/my-repo/file/modules/auth-module.md`
    """
    if not bundle_exists(repo_name):
        raise HTTPException(status_code=404, detail=f"Bundle '{repo_name}' not found.")
    try:
        return get_file_detail(repo_name, filename)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get(
    "/{repo_name}/index",
    summary="Get the bundle's index.md (the master map)",
)
async def get_index(repo_name: str):
    """
    Returns the index.md of the bundle — the auto-generated table of contents
    that the agent reads first when answering any question.
    """
    if not bundle_exists(repo_name):
        raise HTTPException(status_code=404, detail=f"Bundle '{repo_name}' not found.")
    try:
        detail = get_file_detail(repo_name, "index.md")
        return {"repo_name": repo_name, "content": detail.content, "raw": detail.raw}
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="index.md not found. The bundle may still be generating.",
        )


@router.get(
    "/{repo_name}/graph",
    response_model=BundleGraph,
    summary="Get the knowledge graph (nodes + edges)",
)
async def get_graph(repo_name: str):
    """
    Returns the OKF knowledge graph as a list of nodes and directed edges.
    Edges represent `depends_on` relationships between concept files.
    Use this to render the interactive graph visualiser on the frontend.
    """
    if not bundle_exists(repo_name):
        raise HTTPException(status_code=404, detail=f"Bundle '{repo_name}' not found.")
    return build_graph(repo_name)


@router.delete(
    "/{repo_name}",
    summary="Delete a repo's OKF bundle",
)
async def remove_bundle(repo_name: str):
    """
    Permanently deletes all OKF files for the given repo.
    The repo can be re-analyzed with POST /repo/analyze.
    """
    deleted = delete_bundle(repo_name)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Bundle '{repo_name}' not found.")
    return {"message": f"Bundle '{repo_name}' deleted successfully."}
