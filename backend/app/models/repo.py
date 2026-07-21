"""
app/models/repo.py — Repository Pydantic Schemas
=================================================
Request and response models for the /repo endpoints.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator
import re


class AnalyzeRequest(BaseModel):
    """Body for POST /repo/analyze"""

    source: str = Field(
        ...,
        description="GitHub URL (https://github.com/owner/repo) or absolute local path.",
        examples=["https://github.com/tiangolo/fastapi"],
    )
    repo_name: str = Field(
        ...,
        description="Unique slug for this repo's OKF bundle (lowercase, hyphens ok).",
        examples=["fastapi-core"],
        min_length=1,
        max_length=80,
    )
    languages: list[str] = Field(
        default=["python"],
        description="Languages to parse. Supported: python, javascript, typescript.",
        examples=[["python", "javascript"]],
    )
    fast_mode: bool = Field(
        default=True,
        description="If True, bypasses LLM and generates OKF instantly via AST templates.",
    )

    @field_validator("repo_name")
    @classmethod
    def slugify_name(cls, v: str) -> str:
        """Ensure repo_name is a clean slug."""
        slug = re.sub(r"[^a-zA-Z0-9\-_]", "-", v).lower().strip("-")
        if not slug:
            raise ValueError("repo_name must contain at least one alphanumeric character.")
        return slug

    @field_validator("languages")
    @classmethod
    def validate_languages(cls, v: list[str]) -> list[str]:
        supported = {"python", "javascript", "typescript"}
        invalid = set(v) - supported
        if invalid:
            raise ValueError(f"Unsupported languages: {invalid}. Choose from {supported}")
        return [lang.lower() for lang in v]


class JobStatus(BaseModel):
    """Response for GET /repo/status/{job_id}"""

    job_id: str
    repo_name: str
    status: Literal["queued", "cloning", "crawling", "parsing", "summarizing", "indexing", "done", "error"]
    progress: int = Field(ge=0, le=100, description="Completion percentage 0–100")
    message: str = Field(description="Human-readable description of current step")
    files_processed: int = 0
    total_files: int = 0
    current_file: Optional[str] = None  # The file currently being processed
    error_detail: Optional[str] = None
    bundle_path: Optional[str] = None   # Set when status == "done"


class RepoSummary(BaseModel):
    """One entry in GET /repo/list"""

    repo_name: str
    bundle_path: str
    total_okf_files: int
    last_updated: Optional[str] = None  # ISO timestamp


class RepoListResponse(BaseModel):
    """Response for GET /repo/list"""

    repos: list[RepoSummary]
    total: int
