"""
app/utils/llm_client.py — Gemini API Wrapper
=============================================
Single place for ALL LLM calls in the project.
Swap the model or provider here without touching any other file.
"""

from google import genai
from google.genai import types

from app.config import settings


def _get_client() -> genai.Client:
    """Lazily configure and return a Gemini GenAI Client instance."""
    if not settings.GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY is not set. "
            "Copy .env.example → .env and add your key."
        )
    return genai.Client(api_key=settings.GEMINI_API_KEY)


def generate_text(prompt: str, temperature: float = 0.2) -> str:
    """
    Send a prompt to Gemini and return the plain text response.

    Args:
        prompt:      The full prompt string.
        temperature: Lower = more deterministic. Use 0.2 for code summaries.

    Returns:
        The model's text response as a string.

    Raises:
        ValueError: If GEMINI_API_KEY is missing.
        RuntimeError: If the API call fails.
    """
    try:
        client = _get_client()
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=temperature),
        )
        return response.text.strip()
    except Exception as e:
        raise RuntimeError(f"LLM call failed: {e}") from e


def count_tokens(text: str) -> int:
    """
    Estimate token count for a given text string.
    Used for transparency reporting in ChatResponse.

    Returns:
        Approximate token count (Gemini tokenizer).
    """
    try:
        client = _get_client()
        result = client.models.count_tokens(
            model=settings.GEMINI_MODEL,
            contents=text,
        )
        return result.total_tokens
    except Exception:
        # Fallback: rough estimation (1 token ≈ 4 chars)
        return len(text) // 4


def check_connectivity() -> dict:
    """
    Ping the Gemini API with a minimal prompt to verify connectivity.
    Used by the /health endpoint.

    Returns:
        {"status": "ok", "model": "gemini-1.5-flash"} on success.
        {"status": "error", "message": "..."} on failure.
    """
    try:
        response = generate_text("Say 'ok' and nothing else.", temperature=0.0)
        return {
            "status": "ok",
            "model": settings.GEMINI_MODEL,
            "response_preview": response[:50],
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
