"""
app/utils/git_utils.py — Git & Repository Helpers
===================================================
Handles cloning GitHub repos and validating repo sources.
All Git operations are isolated here so the Producer stays clean.
"""

from __future__ import annotations

import re
from pathlib import Path

import git

from app.config import settings
from app.utils.file_utils import delete_dir, ensure_dir, get_dir_size_mb


# ── Constants ─────────────────────────────────────────────────────────────────
GITHUB_URL_PATTERN = re.compile(
    r"^https?://github\.com/[\w.\-]+/[\w.\-]+(\.git)?/?$",
    re.IGNORECASE,
)

# File extensions we consider "source code" worth analysing
SUPPORTED_EXTENSIONS = {".py", ".js", ".ts", ".jsx", ".tsx"}


# ── Validation ────────────────────────────────────────────────────────────────
def is_github_url(source: str) -> bool:
    """Return True if the source string looks like a valid GitHub repo URL."""
    return bool(GITHUB_URL_PATTERN.match(source.strip()))


def is_local_path(source: str) -> bool:
    """Return True if the source string is an existing local directory."""
    return Path(source).is_dir()


def validate_source(source: str) -> str:
    """
    Validate the repo source and return its type.

    Returns:
        "github" | "local"

    Raises:
        ValueError: If source is neither a valid GitHub URL nor a local directory.
    """
    if is_github_url(source):
        return "github"
    if is_local_path(source):
        return "local"
    raise ValueError(
        f"Invalid source '{source}'. "
        "Provide a valid GitHub URL (https://github.com/owner/repo) "
        "or an existing local directory path."
    )


# ── Cloning ───────────────────────────────────────────────────────────────────
def clone_repo(github_url: str, repo_name: str) -> Path:
    """
    Clone a GitHub repository into the temp clone directory.

    Args:
        github_url: Full GitHub HTTPS URL (e.g. https://github.com/owner/repo)
        repo_name:  Slug used as the local folder name.

    Returns:
        Path to the cloned repository root.

    Raises:
        ValueError: If the repo exceeds the configured size limit after cloning.
        RuntimeError: If the Git clone operation fails.
    """
    clone_root = ensure_dir(settings.clone_path / repo_name)

    # If already cloned, just pull latest
    if (clone_root / ".git").exists():
        try:
            repo = git.Repo(clone_root)
            repo.remotes.origin.pull()
            return clone_root
        except Exception:
            # If pull fails, wipe and re-clone
            delete_dir(clone_root)
            clone_root = ensure_dir(settings.clone_path / repo_name)

    try:
        git.Repo.clone_from(github_url, clone_root, depth=1)  # shallow clone
    except git.exc.GitCommandError as e:
        raise RuntimeError(f"Failed to clone '{github_url}': {e}") from e

    # Size guard
    size_mb = get_dir_size_mb(clone_root)
    if size_mb > settings.MAX_REPO_SIZE_MB:
        delete_dir(clone_root)
        raise ValueError(
            f"Repository is too large ({size_mb:.1f} MB > "
            f"{settings.MAX_REPO_SIZE_MB} MB limit)."
        )

    return clone_root


def get_repo_path(source: str, repo_name: str) -> Path:
    """
    Resolve the local filesystem path for a repo source.

    - If source is a GitHub URL  → clone (or pull) and return clone path.
    - If source is a local path  → return as-is.
    """
    source_type = validate_source(source)
    if source_type == "github":
        return clone_repo(source, repo_name)
    return Path(source)


# ── Metadata ──────────────────────────────────────────────────────────────────
def extract_repo_name_from_url(url: str) -> str:
    """
    Extract a clean repo name from a GitHub URL.
    e.g. https://github.com/openai/gpt-2.git → gpt-2
    """
    name = url.rstrip("/").rstrip(".git").split("/")[-1]
    return name or "unknown-repo"


def count_source_files(repo_path: Path) -> int:
    """Count how many analysable source files exist in the repository."""
    from app.utils.file_utils import list_files
    return len(list_files(repo_path, extensions=list(SUPPORTED_EXTENSIONS)))
