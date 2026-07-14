"""
app/core/agent/agent_router.py — Intent-First Query Router
===========================================================
Classifies any user question into one of three routing paths
BEFORE performing any expensive work.

Paths:
  PATH_1_DIRECT   → General/overview question → Use index.md only (cheapest)
  PATH_2_RAG      → Specific keyword question → 1-shot retrieval (current behavior)
  PATH_3_AGENTIC  → Relational/complex question → Full agent tool loop (most powerful)

Design principle: The VAST majority of queries (Path 1 + 2) should
never enter the agentic loop. Agentify ONLY when required.
"""

from __future__ import annotations

import re
from enum import Enum


class RoutePath(str, Enum):
    DIRECT = "direct"     # Use index.md, no search
    RAG = "rag"           # Standard 1-shot keyword retrieval
    AGENTIC = "agentic"   # Full multi-step tool loop


# ── Trigger Keywords ──────────────────────────────────────────────────────────

# Questions that always suggest relational traversal / multi-hop reasoning
_AGENTIC_TRIGGERS = [
    r"\bhow does .+ (call|use|connect|relate|depend|link|import|interact)\b",
    r"\bwhat (calls|imports|uses|inherits from|depends on)\b",
    r"\btrace (the )?(flow|execution|call|path)\b",
    r"\bfollow (the )?(import|dependency|call)\b",
    r"\bwhere is .+ (defined|called|used|imported)\b",
    r"\bconnection between\b",
    r"\brelationship between\b",
    r"\bend[- ]to[- ]end\b",
    r"\bpipeline\b.{0,30}\bhow\b",
    r"\bstep by step\b",
    r"\bwalk me through\b",
    r"\bexplain the full flow\b",
]

# Questions that are clearly overview/general
_DIRECT_TRIGGERS = [
    r"\bwhat (is|does|are) (this|the) (project|repo|codebase|system|app)\b",
    r"\bgive me an? (overview|summary|intro)\b",
    r"\bwhat('s| is) the (architecture|structure|purpose)\b",
    r"\blist (all|the) (modules|files|components)\b",
    r"\bproject overview\b",
    r"\bwhat can (this|it|the system) do\b",
    r"\btell me about (this|the) repo\b",
]


def classify_query(question: str) -> RoutePath:
    """
    Classify a user question into the cheapest routing path that can answer it.

    Args:
        question: The raw user question string.

    Returns:
        RoutePath enum value (DIRECT, RAG, or AGENTIC).
    """
    q_lower = question.lower().strip()

    # Check agentic triggers first — these REQUIRE multi-hop reasoning
    for pattern in _AGENTIC_TRIGGERS:
        if re.search(pattern, q_lower):
            return RoutePath.AGENTIC

    # Check if it's a high-level overview question — cheapest path
    for pattern in _DIRECT_TRIGGERS:
        if re.search(pattern, q_lower):
            return RoutePath.DIRECT

    # Default: standard 1-shot RAG
    return RoutePath.RAG


def should_escalate_to_agentic(retrieval_scores: list[float], threshold: float = 0.15) -> bool:
    """
    After a standard RAG retrieval, check if results are too weak.
    If all scores are below threshold, escalate to agentic loop for retry.

    Args:
        retrieval_scores: List of relevance scores from the initial search.
        threshold:        Minimum acceptable score for a confident retrieval.

    Returns:
        True if the agentic loop should be used to find better context.
    """
    if not retrieval_scores:
        return True  # Nothing was found — definitely escalate
    return max(retrieval_scores) < threshold
