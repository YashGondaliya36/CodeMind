"""
app/core/bundle/manager.py — OKF Bundle CRUD
=============================================
Reads, lists, and manages OKF concept files for a given repo bundle.
This is the "data access layer" for OKF files — no LLM calls here.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import frontmatter  # python-frontmatter parses YAML + Markdown body

from app.config import settings
from app.models.bundle import OKFFileMeta, OKFFileDetail, BundleIndex
from app.utils.file_utils import list_files, safe_read


def get_bundle_path(repo_name: str) -> Path:
    """Return the root Path of a repo's OKF bundle directory."""
    return settings.bundles_path / repo_name


def bundle_exists(repo_name: str) -> bool:
    """Return True if an OKF bundle exists for the given repo."""
    return get_bundle_path(repo_name).is_dir()


def _parse_okf_file(file_path: Path, bundle_root: Path) -> Optional[OKFFileMeta]:
    """
    Parse a single OKF Markdown file and return its frontmatter as OKFFileMeta.
    Returns None if the file cannot be parsed (malformed YAML, missing type, etc.).
    """
    raw = safe_read(file_path)
    if raw is None:
        return None

    try:
        post = frontmatter.loads(raw)
        meta = post.metadata

        # Relative filename from bundle root (used as unique ID)
        rel_path = str(file_path.relative_to(bundle_root)).replace("\\", "/")

        # Provide explicit metadata defaults for system files (index.md, log.md)
        fname_lower = file_path.name.lower()
        default_type = "index" if fname_lower == "index.md" else ("changelog" if fname_lower == "log.md" else "unknown")
        default_title = "Master Project Index" if fname_lower == "index.md" else ("Bundle Audit Log" if fname_lower == "log.md" else file_path.stem)
        default_desc = "Table of contents for the knowledge bundle." if fname_lower == "index.md" else ("History log of bundle generation." if fname_lower == "log.md" else None)

        return OKFFileMeta(
            filename=rel_path,
            type=str(meta.get("type") or default_type),
            title=str(meta.get("title") or default_title),
            description=meta.get("description") or default_desc,
            tags=list(meta.get("tags", [])) or ([default_type] if default_type != "unknown" else []),
            depends_on=list(meta.get("depends_on", [])),
            resource=meta.get("resource"),
            timestamp=str(meta.get("timestamp")) if meta.get("timestamp") else None,
        )
    except Exception:
        return None  # Skip malformed files silently


def _parse_okf_file_detail(file_path: Path, bundle_root: Path) -> Optional[OKFFileDetail]:
    """Parse a single OKF file and return both frontmatter + full body content."""
    raw = safe_read(file_path)
    if raw is None:
        return None

    try:
        post = frontmatter.loads(raw)
        meta = post.metadata
        rel_path = str(file_path.relative_to(bundle_root)).replace("\\", "/")

        fname_lower = file_path.name.lower()
        default_type = "index" if fname_lower == "index.md" else ("changelog" if fname_lower == "log.md" else "unknown")
        default_title = "Master Project Index" if fname_lower == "index.md" else ("Bundle Audit Log" if fname_lower == "log.md" else file_path.stem)
        default_desc = "Table of contents for the knowledge bundle." if fname_lower == "index.md" else ("History log of bundle generation." if fname_lower == "log.md" else None)

        return OKFFileDetail(
            filename=rel_path,
            type=str(meta.get("type") or default_type),
            title=str(meta.get("title") or default_title),
            description=meta.get("description") or default_desc,
            tags=list(meta.get("tags", [])) or ([default_type] if default_type != "unknown" else []),
            depends_on=list(meta.get("depends_on", [])),
            resource=meta.get("resource"),
            timestamp=str(meta.get("timestamp")) if meta.get("timestamp") else None,
            content=post.content,   # Markdown body only
            raw=raw,                # Full file (frontmatter + body)
        )
    except Exception:
        return None


def list_bundle_files(repo_name: str) -> BundleIndex:
    """
    List all OKF files in a bundle and return their metadata.

    Args:
        repo_name: The bundle slug.

    Returns:
        BundleIndex with all parsed OKF file metadata.

    Raises:
        FileNotFoundError: If no bundle exists for this repo.
    """
    bundle_root = get_bundle_path(repo_name)
    if not bundle_root.is_dir():
        raise FileNotFoundError(f"No OKF bundle found for repo '{repo_name}'.")

    md_files = list_files(bundle_root, extensions=[".md"])
    parsed = []

    for f in md_files:
        meta = _parse_okf_file(f, bundle_root)
        if meta:
            parsed.append(meta)

    return BundleIndex(
        repo_name=repo_name,
        total_files=len(parsed),
        files=parsed,
        index_md_exists=(bundle_root / "index.md").exists(),
    )


def get_file_detail(repo_name: str, filename: str) -> OKFFileDetail:
    """
    Retrieve the full content + metadata of one OKF file.

    Args:
        repo_name: Bundle slug.
        filename:  Relative path within the bundle (e.g. "modules/auth-module.md").

    Returns:
        OKFFileDetail with frontmatter + Markdown body.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        ValueError:        If the file cannot be parsed.
    """
    bundle_root = get_bundle_path(repo_name)
    file_path = bundle_root / filename

    if not file_path.exists():
        raise FileNotFoundError(
            f"File '{filename}' not found in bundle '{repo_name}'."
        )

    detail = _parse_okf_file_detail(file_path, bundle_root)
    if detail is None:
        raise ValueError(f"Could not parse OKF file '{filename}'.")

    return detail


def get_all_metadata(repo_name: str) -> list[OKFFileMeta]:
    """
    Return frontmatter metadata for ALL files in a bundle.
    Used by the agent's metadata scanner for fast relevance scoring.
    This is intentionally cheap — NO full file reads.
    """
    bundle_root = get_bundle_path(repo_name)
    if not bundle_root.is_dir():
        return []

    md_files = list_files(bundle_root, extensions=[".md"])
    result = []
    for f in md_files:
        meta = _parse_okf_file(f, bundle_root)
        if meta:
            result.append(meta)
    return result


def list_repos() -> list[dict]:
    """
    Enumerate all repo bundles that exist in the bundles directory.

    Returns:
        List of dicts with repo_name, bundle_path, total_okf_files, last_updated.
    """
    bundles_root = settings.bundles_path
    if not bundles_root.is_dir():
        return []

    repos = []
    for d in sorted(bundles_root.iterdir()):
        if not d.is_dir():
            continue
        md_files = list_files(d, extensions=[".md"])
        # Get last modified time from the most recently updated file
        last_updated = None
        if md_files:
            latest_mtime = max(f.stat().st_mtime for f in md_files)
            last_updated = datetime.fromtimestamp(
                latest_mtime, tz=timezone.utc
            ).isoformat()

        repos.append({
            "repo_name": d.name,
            "bundle_path": str(d),
            "total_okf_files": len(md_files),
            "last_updated": last_updated,
        })

    return repos


def delete_bundle(repo_name: str) -> bool:
    """
    Delete an entire OKF bundle.

    Returns:
        True if deleted, False if it didn't exist.
    """
    from app.utils.file_utils import delete_dir
    bundle_root = get_bundle_path(repo_name)
    if not bundle_root.exists():
        return False
    delete_dir(bundle_root)
    return True
