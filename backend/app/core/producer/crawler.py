"""
app/core/producer/crawler.py — Repository File Crawler
========================================================
Walks a local repository directory and returns a structured list
of all source files worth analysing. Applies smart filtering to
skip noise (vendored libs, build artifacts, test fixtures, etc.)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app.utils.file_utils import list_files


# ── Language → Extensions mapping ─────────────────────────────────────────────
LANGUAGE_EXTENSIONS: dict[str, list[str]] = {
    "python":     [".py"],
    "javascript": [".js", ".jsx"],
    "typescript": [".ts", ".tsx"],
}

# ── Directories to always skip ────────────────────────────────────────────────
SKIP_DIRS = {
    ".git", ".github", "__pycache__", "node_modules", ".venv", "venv",
    "env", ".env", "dist", "build", ".next", ".nuxt", "coverage",
    ".pytest_cache", ".mypy_cache", "eggs", "*.egg-info", ".tox",
    "htmlcov", ".cache", "tmp", "temp", "logs",
}

# ── Files to always skip ──────────────────────────────────────────────────────
SKIP_FILENAMES = {
    "setup.py", "conftest.py", "manage.py",      # boilerplate
    "__init__.py",                                 # often empty
}

# Files smaller than this (bytes) are likely empty or trivial
MIN_FILE_SIZE_BYTES = 100


@dataclass
class CrawledFile:
    """Represents a single source file found during crawling."""
    path: Path                       # Absolute path
    relative_path: str               # Relative to repo root (for display)
    language: str                    # "python" | "javascript" | "typescript"
    size_bytes: int
    extension: str


@dataclass
class CrawlResult:
    """Result of crawling a full repository."""
    repo_path: Path
    files: list[CrawledFile] = field(default_factory=list)
    skipped_count: int = 0
    total_scanned: int = 0

    @property
    def total_files(self) -> int:
        return len(self.files)


def crawl_repo(repo_path: Path, languages: list[str]) -> CrawlResult:
    """
    Walk a repository and collect all analysable source files.

    Args:
        repo_path: Absolute path to the cloned/local repository root.
        languages: List of languages to include (e.g. ["python", "javascript"]).

    Returns:
        CrawlResult containing all filtered CrawledFile objects.
    """
    # Resolve which extensions to collect
    extensions = []
    for lang in languages:
        extensions.extend(LANGUAGE_EXTENSIONS.get(lang.lower(), []))

    if not extensions:
        return CrawlResult(repo_path=repo_path)

    result = CrawlResult(repo_path=repo_path)
    all_files = list_files(repo_path, extensions=extensions, recursive=True)
    result.total_scanned = len(all_files)

    for file_path in all_files:
        # ── Skip-dir check ────────────────────────────────────────────────────
        if _is_in_skip_dir(file_path, repo_path):
            result.skipped_count += 1
            continue

        # ── Skip-filename check ───────────────────────────────────────────────
        if file_path.name in SKIP_FILENAMES:
            result.skipped_count += 1
            continue

        # ── Size check ────────────────────────────────────────────────────────
        size = file_path.stat().st_size
        if size < MIN_FILE_SIZE_BYTES:
            result.skipped_count += 1
            continue

        # ── Determine language ────────────────────────────────────────────────
        lang = _extension_to_language(file_path.suffix)

        rel = str(file_path.relative_to(repo_path)).replace("\\", "/")

        result.files.append(CrawledFile(
            path=file_path,
            relative_path=rel,
            language=lang,
            size_bytes=size,
            extension=file_path.suffix,
        ))

    return result


def _is_in_skip_dir(file_path: Path, repo_root: Path) -> bool:
    """Return True if any part of the file's path is a skip directory."""
    try:
        parts = file_path.relative_to(repo_root).parts
    except ValueError:
        return False
    return any(part in SKIP_DIRS or part.endswith(".egg-info") for part in parts)


def _extension_to_language(ext: str) -> str:
    """Map a file extension back to its language name."""
    for lang, exts in LANGUAGE_EXTENSIONS.items():
        if ext.lower() in exts:
            return lang
    return "unknown"
