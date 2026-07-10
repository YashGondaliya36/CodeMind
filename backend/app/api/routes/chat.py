"""
app/api/routes/chat.py — Chat Agent Endpoint
=============================================
POST /chat/ask — The main developer-facing endpoint.
Delegates entirely to core/agent/responder.py
"""

from fastapi import APIRouter, HTTPException

from app.core.agent.responder import answer_question
from app.core.bundle.manager import bundle_exists
from app.models.chat import ChatRequest, ChatResponse

router = APIRouter()


@router.post(
    "/ask",
    response_model=ChatResponse,
    summary="Ask a question about a codebase",
)
async def ask(request: ChatRequest):
    """
    Ask a natural language question about any analyzed repository.

    **How it works (the OKF selective retrieval pipeline):**
    1. Scans frontmatter of ALL OKF files in the bundle (fast, cheap)
    2. Scores each file's relevance to your question (keyword overlap)
    3. Fetches full content of ONLY the top N relevant files
    4. Injects selected files into LLM context
    5. Returns the grounded answer + which sources were used

    The response includes `sources_used` — every answer is fully transparent
    about which OKF knowledge files backed it.
    """
    if not bundle_exists(request.repo_name):
        raise HTTPException(
            status_code=404,
            detail=(
                f"No OKF bundle found for repo '{request.repo_name}'. "
                f"Run POST /repo/analyze first to generate the knowledge bundle."
            ),
        )

    try:
        return answer_question(request)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=f"LLM error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {e}")
