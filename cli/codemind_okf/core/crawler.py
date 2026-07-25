"""
codemind_okf/core/crawler.py — Repository File Crawler
========================================================
Walks a local directory and returns all analysable source files.
Standalone — no FastAPI dependency.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from codemind_okf.core.file_utils import list_files


# ── Supported languages ───────────────────────────────────────────────────────
LANGUAGE_EXTENSIONS: dict[str, list[str]] = {
    "python":     [".py"],
    "javascript": [".js", ".jsx"],
    "typescript": [".ts", ".tsx"],
}

ALL_EXTENSIONS: list[str] = [ext for exts in LANGUAGE_EXTENSIONS.values() for ext in exts]

# ── Noise filters ─────────────────────────────────────────────────────────────
SKIP_DIRS = {
    ".git", ".github", "__pycache__", "node_modules", ".venv", "venv",
    "env", ".env", "dist", "build", ".next", ".nuxt", "coverage",
    ".pytest_cache", ".mypy_cache", "eggs", ".tox", ".okf",
    "htmlcov", ".cache", "tmp", "temp", "logs",
}

SKIP_FILENAMES = {
    "setup.py", "conftest.py", "manage.py", "__init__.py",
}

MIN_FILE_SIZE_BYTES = 100


import hashlib
import json
from codemind_okf.core.file_utils import safe_write


@dataclass
class CrawledFile:
    """Represents a single source file ready for analysis."""
    path: Path
    relative_path: str
    language: str
    size_bytes: int
    extension: str
    sha256: str = ""


@dataclass
class CrawlResult:
    """Full result of crawling a directory."""
    root: Path
    files: list[CrawledFile] = field(default_factory=list)
    skipped_count: int = 0
    total_scanned: int = 0

    @property
    def total_files(self) -> int:
        return len(self.files)


def compute_file_hash(path: Path) -> str:
    """Compute SHA-256 hash of a file's raw content."""
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except Exception:
        return ""


def load_checksums(bundle_root: Path) -> dict[str, str]:
    """Load cached checksum map from .okf/.checksums.json."""
    cache_file = bundle_root / ".checksums.json"
    if cache_file.exists():
        try:
            return json.loads(cache_file.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_checksums(bundle_root: Path, checksums: dict[str, str]) -> None:
    """Save updated checksum map to .okf/.checksums.json."""
    cache_file = bundle_root / ".checksums.json"
    safe_write(cache_file, json.dumps(checksums, indent=2))


def crawl(root: Path, languages: list[str] | None = None) -> CrawlResult:
    """
    Walk a directory and collect all analysable source files.

    Args:
        root:      Absolute path to the project root.
        languages: Languages to include. None = all supported.

    Returns:
        CrawlResult with filtered CrawledFile objects.
    """
    if languages:
        extensions = []
        for lang in languages:
            extensions.extend(LANGUAGE_EXTENSIONS.get(lang.lower(), []))
    else:
        extensions = ALL_EXTENSIONS

    if not extensions:
        return CrawlResult(root=root)

    result = CrawlResult(root=root)
    all_files = list_files(root, extensions=extensions, recursive=True)
    result.total_scanned = len(all_files)

    for file_path in all_files:
        if _is_in_skip_dir(file_path, root):
            result.skipped_count += 1
            continue

        if file_path.name in SKIP_FILENAMES:
            result.skipped_count += 1
            continue

        size = file_path.stat().st_size
        if size < MIN_FILE_SIZE_BYTES:
            result.skipped_count += 1
            continue

        lang = _extension_to_language(file_path.suffix)
        rel = str(file_path.relative_to(root)).replace("\\", "/")

        sha = compute_file_hash(file_path)

        result.files.append(CrawledFile(
            path=file_path,
            relative_path=rel,
            language=lang,
            size_bytes=size,
            extension=file_path.suffix,
            sha256=sha,
        ))

    return result


def _is_in_skip_dir(file_path: Path, repo_root: Path) -> bool:
    """Check if file resides in a skip directory, site-packages, or virtual environment."""
    try:
        rel_parts = file_path.relative_to(repo_root).parts
    except ValueError:
        return False

    # Check directory parts leading up to the file
    for i, part in enumerate(rel_parts[:-1]):
        lower = part.lower()

        # Fixed skip dir list or egg-info
        if lower in SKIP_DIRS or lower.endswith(".egg-info"):
            return True

        # Common package/vendor dirs
        if lower in ("site-packages", "dist-packages", "node_modules", "vendor", ".okf"):
            return True

        # Smart VirtualEnv check: if directory contains 'pyvenv.cfg' or 'activate_this.py'
        dir_path = repo_root.joinpath(*rel_parts[:i+1])
        if (dir_path / "pyvenv.cfg").exists() or (dir_path / "Scripts" / "activate").exists() or (dir_path / "bin" / "activate").exists():
            return True

    return False


def _extension_to_language(ext: str) -> str:
    for lang, exts in LANGUAGE_EXTENSIONS.items():
        if ext.lower() in exts:
            return lang
    return "unknown"
