"""
app/utils/file_utils.py — Safe File I/O Helpers
================================================
All file reading/writing in the project goes through these helpers.
They handle encoding, path safety, and error normalisation consistently.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


def safe_read(path: Path | str, encoding: str = "utf-8") -> Optional[str]:
    """
    Read a file and return its content as a string.
    Returns None (instead of raising) if the file doesn't exist.

    Args:
        path:     Absolute or relative path to the file.
        encoding: Text encoding to use (default utf-8).

    Returns:
        File content string, or None if the file is missing.
    """
    path = Path(path)
    if not path.exists():
        return None
    try:
        return path.read_text(encoding=encoding, errors="replace")
    except Exception as e:
        raise IOError(f"Failed to read {path}: {e}") from e


def safe_write(path: Path | str, content: str, encoding: str = "utf-8") -> Path:
    """
    Write content to a file, creating parent directories if needed.

    Args:
        path:     Target file path.
        content:  String content to write.
        encoding: Text encoding to use.

    Returns:
        The resolved Path that was written.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding=encoding)
    return path


def list_files(
    directory: Path | str,
    extensions: Optional[list[str]] = None,
    recursive: bool = True,
) -> list[Path]:
    """
    List files in a directory, optionally filtered by extension.

    Args:
        directory:  Root directory to search.
        extensions: e.g. [".py", ".js"]. None means all files.
        recursive:  If True, walk subdirectories too.

    Returns:
        Sorted list of Path objects.
    """
    directory = Path(directory)
    if not directory.is_dir():
        return []

    if recursive:
        all_files = [p for p in directory.rglob("*") if p.is_file()]
    else:
        all_files = [p for p in directory.iterdir() if p.is_file()]

    if extensions:
        # Normalise extensions — ensure they start with '.'
        normalised = {
            ext if ext.startswith(".") else f".{ext}"
            for ext in extensions
        }
        all_files = [f for f in all_files if f.suffix.lower() in normalised]

    return sorted(all_files)


def get_file_size_mb(path: Path | str) -> float:
    """Return the size of a file in megabytes."""
    return Path(path).stat().st_size / (1024 * 1024)


def get_dir_size_mb(directory: Path | str) -> float:
    """Return the total size of a directory (recursive) in megabytes."""
    total = sum(
        f.stat().st_size
        for f in Path(directory).rglob("*")
        if f.is_file()
    )
    return total / (1024 * 1024)


def ensure_dir(path: Path | str) -> Path:
    """Create a directory (and parents) if it doesn't exist. Returns Path."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def delete_dir(path: Path | str) -> None:
    """Recursively delete a directory and all its contents."""
    import shutil
    path = Path(path)
    if path.exists():
        shutil.rmtree(path)


def relative_to_project(path: Path | str) -> str:
    """
    Convert an absolute path to a project-relative string for clean display.
    Falls back to the absolute path string if relativisation fails.
    """
    try:
        return str(Path(path).relative_to(Path.cwd()))
    except ValueError:
        return str(path)
