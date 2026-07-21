"""
app/core/agent/retriever.py — Selective Context Retriever
==========================================================
The core OKF "selective retrieval" algorithm.

Given a user question and a list of OKF file metadata, scores each file
for relevance and returns only the top N most relevant files.

This is what makes OKF cost-efficient:
  - Scan metadata of ALL files  → cheap (no LLM, no full reads)
  - Fetch ONLY top N files      → targeted (low token cost)

Scoring strategy (keyword overlap — no embeddings required for v1):
  1. Tokenise the question into keywords
  2. Score each file: keyword hits in title + tags + description
  3. Rank by score, return top N
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.agent.metadata_scanner import scan_all_metadata
from app.core.bundle.manager import get_file_detail
from app.models.bundle import OKFFileMeta, OKFFileDetail


# ── Stop words to ignore during keyword matching ──────────────────────────────
_STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "how", "what", "where",
    "when", "why", "who", "which", "this", "that", "these", "those",
    "it", "its", "in", "on", "at", "to", "for", "of", "and", "or",
    "not", "with", "from", "by", "about", "work", "works", "does", "me",
    "tell", "show", "explain", "describe",
}

# Field weights — how much each metadata field contributes to the score
_WEIGHTS = {
    "title": 3.0,
    "tags": 2.5,
    "key_functions": 4.0,   # Highest weight: exact function/class name match
    "description": 1.5,
    "type": 1.0,
    "filename": 0.5,
}


@dataclass
class ScoredFile:
    """A metadata file paired with its relevance score."""
    meta: OKFFileMeta
    score: float


def retrieve_relevant_files(
    repo_name: str,
    question: str,
    max_files: int = 5,
    min_score: float = 0.0,
) -> list[tuple[OKFFileDetail, float]]:
    """
    Score all OKF files in a bundle against the user's question and return
    the most relevant ones with their full content loaded.

    Args:
        repo_name: Bundle slug.
        question:  The user's natural language question.
        max_files: Maximum number of files to return.
        min_score: Minimum relevance score threshold (0.0 = no filter).

    Returns:
        List of (OKFFileDetail, score) tuples, sorted by score descending.
        Only files above min_score are included, capped at max_files.
    """
    # Step 1: Get all metadata (fast — no full reads)
    all_meta = scan_all_metadata(repo_name)

    # Filter out log files but keep index.md if we need it
    all_meta = [m for m in all_meta if m.filename not in ("log.md",)]

    if not all_meta:
        return []

    # Step 2: Score each file against the question
    keywords = _extract_keywords(question)
    scored = [
        ScoredFile(meta=m, score=_score_file(m, keywords))
        for m in all_meta if m.filename != "index.md" # Don't score index.md directly to avoid bias
    ]

    # Step 3: Sort by score descending, apply min_score filter
    scored.sort(key=lambda s: s.score, reverse=True)
    filtered = [s for s in scored if s.score > min_score]

    # If no specific files match (e.g. global question like "what is this project about"), 
    # explicitly fallback to the Master Index instead of random files!
    if not filtered:
        # Create a dummy ScoredFile for index.md
        index_meta = OKFFileMeta(
            filename="index.md",
            title="Master Project Index",
            description="Global overview of all files in the project",
            type="index",
            tags=["global", "overview", "project"]
        )
        filtered = [ScoredFile(meta=index_meta, score=0.1)]

    top = filtered[:max_files]

    # Step 4: Fetch full content of ONLY the selected files
    results: list[tuple[OKFFileDetail, float]] = []
    for s in top:
        try:
            detail = get_file_detail(repo_name, s.meta.filename)
            results.append((detail, round(s.score, 4)))
        except Exception:
            continue  # Skip if file was deleted between scan and fetch

    return results


def _extract_keywords(text: str) -> set[str]:
    """
    Tokenise a question into meaningful keywords.
    Lowercases, removes punctuation, strips stop words.
    """
    tokens = re.findall(r"\b\w+\b", text.lower())
    return {t for t in tokens if t not in _STOP_WORDS and len(t) > 2}


def _score_file(meta: OKFFileMeta, keywords: set[str]) -> float:
    """
    Compute a relevance score for an OKF file against a set of keywords.

    Score = sum of weighted keyword hits across each metadata field.
    Normalised to [0, 1] range against the MAX ACTUAL score, not theoretical max,
    preventing multi-keyword bias.
    """
    if not keywords:
        return 0.0

    raw_score = 0.0

    # Title
    title_words = set(meta.title.lower().split())
    raw_score += len(keywords & title_words) * _WEIGHTS["title"]

    # Tags (exact match bonus)
    tag_words = {t.lower() for t in meta.tags}
    tag_hits = len(keywords & tag_words)
    raw_score += tag_hits * _WEIGHTS["tags"]

    # Key functions — highest priority (direct function/class name match)
    if meta.key_functions:
        kf_words = {fn.lower() for fn in meta.key_functions}
        # Check both exact match and partial substring match for function names
        kf_hits = sum(1 for kw in keywords if any(kw in fn.lower() or fn.lower() in kw for fn in kf_words))
        raw_score += kf_hits * _WEIGHTS["key_functions"]

    # Description
    if meta.description:
        desc_words = set(re.findall(r"\b\w+\b", meta.description.lower()))
        raw_score += len(keywords & desc_words) * _WEIGHTS["description"]

    # Type (e.g. "api", "database")
    if meta.type.lower() in keywords:
        raw_score += _WEIGHTS["type"]

    # Filename
    filename_words = set(re.findall(r"\b\w+\b", meta.filename.lower()))
    raw_score += len(keywords & filename_words) * _WEIGHTS["filename"]

    # FIX: Normalize against max score any single keyword could contribute,
    # multiplied by number of actual hits (not total keywords).
    # This prevents long queries from always scoring lower.
    max_single = max(_WEIGHTS.values())  # 4.0 (key_functions)
    max_possible = len(keywords) * max_single
    normalised = raw_score / max_possible if max_possible > 0 else 0.0

    return min(normalised, 1.0)
