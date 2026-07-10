"""
app/config.py — Centralised Application Settings
==================================================
Uses Pydantic-Settings to load from environment variables / .env file.
Every other module imports `settings` from here — never reads env vars directly.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    All configuration lives here. Pydantic-Settings will:
    1. Look for matching environment variables (case-insensitive).
    2. Fall back to the .env file if present.
    3. Use the default values below as last resort.
    """

    model_config = SettingsConfigDict(
        env_file=".env",          # Load from .env in the working directory
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",           # Silently ignore unknown env vars
    )

    # ── Gemini LLM ───────────────────────────────────────────────────────────
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # ── App ───────────────────────────────────────────────────────────────────
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    # ── Paths ─────────────────────────────────────────────────────────────────
    # Stored as strings so they work across OS; convert to Path when needed.
    OKF_BUNDLES_DIR: str = "okf_bundles"
    REPOS_CLONE_DIR: str = ".tmp_repos"

    # ── Repo Limits ───────────────────────────────────────────────────────────
    MAX_REPO_SIZE_MB: int = 500

    # ── Agent ─────────────────────────────────────────────────────────────────
    AGENT_MAX_CONTEXT_FILES: int = 5
    AGENT_MIN_RELEVANCE_SCORE: float = 0.1

    # ── Computed helpers ──────────────────────────────────────────────────────
    @property
    def bundles_path(self) -> Path:
        return Path(self.OKF_BUNDLES_DIR)

    @property
    def clone_path(self) -> Path:
        return Path(self.REPOS_CLONE_DIR)

    @property
    def is_dev(self) -> bool:
        return self.APP_ENV == "development"


# Singleton — import this everywhere
settings = Settings()
