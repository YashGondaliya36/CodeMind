"""
app/api/routes/health.py — Health Check Endpoint
=================================================
GET /health — Used by monitoring tools, Docker HEALTHCHECK, and the
frontend to verify the backend + Gemini API are both reachable.
"""

import platform
import sys
from datetime import datetime, timezone

from fastapi import APIRouter

from app.config import settings
from app.utils.llm_client import check_connectivity

router = APIRouter()


@router.get("/health", summary="Health check")
async def health_check():
    """
    Returns the status of the server and its external dependencies.

    Response includes:
    - Server uptime metadata
    - Gemini API connectivity status
    - Current configuration summary
    """
    gemini_status = check_connectivity()

    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "server": {
            "python_version": sys.version.split()[0],
            "platform": platform.system(),
            "environment": settings.APP_ENV,
        },
        "gemini": gemini_status,
        "config": {
            "model": settings.GEMINI_MODEL,
            "bundles_dir": settings.OKF_BUNDLES_DIR,
            "max_context_files": settings.AGENT_MAX_CONTEXT_FILES,
        },
    }
