"""
app/api/routes/repo.py — Repository Analysis Endpoints
=======================================================
Orchestrates the full Producer pipeline:
  1. Clone / locate repo
  2. Crawl source files
  3. Parse each file (AST)
  4. Summarize with LLM
  5. Write OKF files
  6. Build index.md + log.md

Uses FastAPI BackgroundTasks so the HTTP response returns immediately
with a job_id while the analysis runs in the background.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.core.bundle.index_builder import append_to_log, build_index
from app.core.bundle.graph_builder import build_graph
from app.core.bundle.manager import delete_bundle, list_repos
from app.core.producer.crawler import crawl_repo
from app.core.producer.okf_writer import write_okf_file
from app.core.producer.parser import parse_file
from app.core.producer.summarizer import summarize_file
from app.core.producer.template_summarizer import summarize_file_fast
from app.models.repo import AnalyzeRequest, JobStatus, RepoListResponse, RepoSummary
from app.utils.git_utils import get_repo_path

router = APIRouter()

# ── In-memory job store ───────────────────────────────────────────────────────
# Simple dict keyed by job_id. In production, swap for Redis.
_jobs: dict[str, dict[str, Any]] = {}


def _update_job(job_id: str, **kwargs: Any) -> None:
    """Merge kwargs into the job state dict."""
    if job_id in _jobs:
        _jobs[job_id].update(kwargs)


# ── Background Task ───────────────────────────────────────────────────────────

def _run_analysis(job_id: str, request: AnalyzeRequest) -> None:
    """
    The full Producer pipeline — runs in the background.
    Updates _jobs[job_id] at each step so the frontend can poll progress.
    """
    try:
        # ── Step 1: Clone / locate repo ───────────────────────────────────────
        _update_job(job_id, status="cloning", message="Cloning / locating repository…", progress=5)
        repo_path = get_repo_path(request.source, request.repo_name)

        # ── Step 2: Crawl source files ────────────────────────────────────────
        _update_job(job_id, status="crawling", message="Crawling source files…", progress=15)
        crawl_result = crawl_repo(repo_path, request.languages)

        if crawl_result.total_files == 0:
            _update_job(
                job_id,
                status="error",
                message="No analysable source files found.",
                progress=0,
                error_detail=(
                    f"Scanned {crawl_result.total_scanned} files but found none matching "
                    f"languages {request.languages}. Check the repo structure."
                ),
            )
            return

        total = crawl_result.total_files
        _update_job(job_id, total_files=total)

        # ── Steps 3+4+5: Parse → Summarize → Write (per file) ────────────────
        _update_job(
            job_id,
            status="parsing",
            message=f"Analysing {total} source files…",
            progress=20,
        )

        for idx, crawled_file in enumerate(crawl_result.files, start=1):
            try:
                # Parse
                parsed = parse_file(
                    crawled_file.path,
                    crawled_file.relative_path,
                    crawled_file.language,
                )

                # Summarize
                mode_label = "AST Fast Mode" if request.fast_mode else "LLM Deep Mode"
                _update_job(
                    job_id,
                    status="summarizing",
                    message=f"Summarizing ({mode_label}): {crawled_file.relative_path}",
                    progress=20 + int(70 * idx / total),
                    files_processed=idx,
                )
                
                if request.fast_mode:
                    summary = summarize_file_fast(parsed)
                else:
                    summary = summarize_file(parsed)

                # Write OKF file
                write_okf_file(request.repo_name, parsed, summary)

            except Exception as e:
                # Don't abort the whole job for one bad file — log and continue
                print(f"[WARN] Skipping {crawled_file.relative_path}: {e}")

        # ── Step 6: Build index.md + graph.json + log entry ───────────────────────────────
        _update_job(job_id, status="indexing", message="Building index.md and graph.json…", progress=92)
        build_index(request.repo_name)
        build_graph(request.repo_name)
        append_to_log(
            request.repo_name,
            f"Bundle created from `{request.source}` "
            f"({total} files, languages: {request.languages})",
        )

        from app.config import settings
        bundle_path = str(settings.bundles_path / request.repo_name)

        _update_job(
            job_id,
            status="done",
            message=f"Done! {total} OKF files generated.",
            progress=100,
            bundle_path=bundle_path,
        )

    except Exception as e:
        _update_job(
            job_id,
            status="error",
            message="Analysis failed.",
            error_detail=str(e),
            progress=0,
        )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/analyze",
    response_model=JobStatus,
    status_code=202,
    summary="Analyze a repository and generate an OKF bundle",
)
async def analyze_repo(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    """
    Submit a repository for analysis. Returns immediately with a `job_id`.
    Poll `GET /repo/status/{job_id}` to track progress.

    The pipeline: clone → crawl → parse → summarize (LLM) → write OKF files → index
    """
    job_id = str(uuid.uuid4())

    _jobs[job_id] = {
        "job_id": job_id,
        "repo_name": request.repo_name,
        "status": "queued",
        "progress": 0,
        "message": "Job queued. Starting shortly…",
        "files_processed": 0,
        "total_files": 0,
        "error_detail": None,
        "bundle_path": None,
    }

    background_tasks.add_task(_run_analysis, job_id, request)

    return JobStatus(**_jobs[job_id])


@router.get(
    "/status/{job_id}",
    response_model=JobStatus,
    summary="Poll analysis job status",
)
async def get_job_status(job_id: str):
    """
    Returns the current status and progress of a background analysis job.
    Poll this every 2–3 seconds from the frontend.
    """
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    return JobStatus(**job)


@router.get(
    "/list",
    response_model=RepoListResponse,
    summary="List all analyzed repositories",
)
async def list_analyzed_repos():
    """Returns all repos that have a generated OKF bundle on disk."""
    repos_raw = list_repos()
    repos = [RepoSummary(**r) for r in repos_raw]
    return RepoListResponse(repos=repos, total=len(repos))


@router.delete(
    "/{repo_name}",
    summary="Delete a repository's OKF bundle",
)
async def delete_repo_bundle(repo_name: str):
    """Permanently deletes the OKF bundle for the given repo."""
    deleted = delete_bundle(repo_name)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"No bundle found for repo '{repo_name}'.",
        )
    return {"message": f"Bundle '{repo_name}' deleted successfully."}
