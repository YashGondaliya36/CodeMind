"""
app/core/agent/responder.py — Context Assembly + LLM Response
==============================================================
Final step of the agent pipeline:
  1. Retrieve relevant OKF files (via retriever.py)
  2. Assemble a structured context prompt
  3. Call the LLM with the question + context
  4. Return the answer + full transparency (which files were used, token count)
"""

from __future__ import annotations

from app.core.agent.retriever import retrieve_relevant_files
from app.config import settings
from app.models.chat import ChatRequest, ChatResponse, SourceFile
from app.utils.llm_client import generate_text, count_tokens


def answer_question(request: ChatRequest) -> ChatResponse:
    """
    Core agent entrypoint — takes a ChatRequest, runs the full
    selective retrieval pipeline, and returns a grounded answer.

    Args:
        request: ChatRequest with repo_name, question, and max_files.

    Returns:
        ChatResponse with the answer, sources used, and transparency metadata.

    Raises:
        FileNotFoundError: If the bundle doesn't exist.
        RuntimeError: If the LLM call fails.
    """
    # ── Step 1: Retrieve relevant OKF files ────────────────────────────────────
    retrieved = retrieve_relevant_files(
        repo_name=request.repo_name,
        question=request.question,
        max_files=request.max_files,
        min_score=settings.AGENT_MIN_RELEVANCE_SCORE,
    )

    # Track how many files were scanned (for transparency display)
    from app.core.agent.metadata_scanner import scan_all_metadata
    all_meta = scan_all_metadata(request.repo_name)
    files_scanned = len(all_meta)

    # ── Step 2: Assemble context ───────────────────────────────────────────────
    if not retrieved:
        # No relevant files found — answer without context (best effort)
        answer = _answer_without_context(request.question, request.repo_name)
        return ChatResponse(
            answer=answer,
            sources_used=[],
            files_scanned=files_scanned,
            tokens_used=None,
            repo_name=request.repo_name,
            question=request.question,
        )

    context_block = _build_context_block(retrieved, request.repo_name)
    prompt = _build_answer_prompt(request.question, request.repo_name, context_block)

    # ── Step 3: Call LLM ───────────────────────────────────────────────────────
    answer = generate_text(prompt, temperature=0.3)
    tokens_used = count_tokens(prompt + answer)

    # ── Step 4: Build SourceFile list for transparency ─────────────────────────
    sources = [
        SourceFile(
            filename=detail.filename,
            title=detail.title,
            relevance_score=score,
            tags=detail.tags,
        )
        for detail, score in retrieved
    ]

    return ChatResponse(
        answer=answer,
        sources_used=sources,
        files_scanned=files_scanned,
        tokens_used=tokens_used,
        repo_name=request.repo_name,
        question=request.question,
    )


def _build_context_block(
    retrieved: list[tuple],
    repo_name: str,
) -> str:
    """
    Format the retrieved OKF files into a clean context block for the prompt.
    Each file is clearly delimited so the LLM can reference them separately.
    """
    blocks = []
    for idx, (detail, score) in enumerate(retrieved, start=1):
        # Increased to ~15000 chars to avoid aggressively truncating deep technical details
        markdown_body = f"{detail.content[:15000]}"
        
        # Optionally inject the RAW source code so the LLM can read exact math/logic 
        # (which might have been skipped by the high-level markdown summarizer)
        raw_code_block = ""
        if detail.resource:
            from pathlib import Path
            from app.utils.file_utils import safe_read
            source_path = settings.clone_path / repo_name / detail.resource
            if source_path.exists():
                raw_code = safe_read(source_path)
                if raw_code:
                    raw_code_block = f"\n\n--- ORIGINAL SOURCE CODE ---\n```\n{raw_code[:15000]}\n```\n"

        block = (
            f"--- Knowledge File {idx}: {detail.title} ---\n"
            f"File: {detail.filename}\n"
            f"Tags: {', '.join(detail.tags)}\n"
            f"Relevance: {score:.2f}\n\n"
            f"{markdown_body}"
            f"{raw_code_block}"
        )
        blocks.append(block)
    return "\n\n".join(blocks)


def _build_answer_prompt(question: str, repo_name: str, context: str) -> str:
    """Build the final LLM prompt with injected OKF context."""
    return f"""You are CodeMind, an expert AI developer assistant with deep knowledge of the '{repo_name}' codebase.

You have been given structured knowledge files (OKF format) that describe specific modules and concepts in this codebase. Use ONLY this provided context to answer the question. If the answer is not covered in the context, say so clearly — do NOT hallucinate.

## Knowledge Context (from OKF Bundle)

{context}

---

## Developer's Question

{question}

---

## Instructions
- Answer clearly and directly.
- Reference specific function names, class names, or file paths from the context when relevant.
- Use markdown formatting (headers, code blocks, bullet points) for clarity.
- If the context is insufficient, say: "The available knowledge files don't fully cover this. Based on what I can see: [partial answer]"
- Do NOT make up information that isn't in the context.

## Answer:
"""


def _answer_without_context(question: str, repo_name: str) -> str:
    """Fallback: answer when no relevant OKF files were found."""
    prompt = f"""You are CodeMind, an AI developer assistant for the '{repo_name}' codebase.

No relevant knowledge files were found for this question in the OKF bundle.
This may mean:
1. The relevant module hasn't been analysed yet
2. The question is about something not in the codebase
3. The keywords in the question don't match the current bundle's tags

Question: {question}

Please acknowledge that the knowledge base doesn't have sufficient context for this specific question, and suggest what the user could do (e.g., re-run analysis, check the bundle explorer, or rephrase with different keywords).
"""
    return generate_text(prompt, temperature=0.1)
