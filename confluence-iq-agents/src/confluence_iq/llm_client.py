"""httpx-based client for the internal Ollama-backed LLM endpoint (api.iamtzar.com)."""

import httpx
from pydantic import BaseModel

from .config import LLM_BASE_URL, LLM_MODEL


def call_llm(
    system_prompt: str,
    user_content: str,
    output_schema: type[BaseModel],
    model: str = LLM_MODEL,
) -> tuple[BaseModel, str]:
    """Call POST /api/chat and return (parsed_output, thinking_text)."""
    response = httpx.post(
        f"{LLM_BASE_URL}/api/chat",
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "stream": False,
            "format": output_schema.model_json_schema(),
        },
        timeout=120.0,
    )
    response.raise_for_status()
    data = response.json()
    message = data["message"]
    output = output_schema.model_validate_json(message["content"])
    thinking = message.get("thinking", "")
    return output, thinking
