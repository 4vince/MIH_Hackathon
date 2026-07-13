"""httpx-based client for the internal Ollama-backed LLM endpoint (api.iamtzar.com)."""

import logging

import httpx
from pydantic import BaseModel, ValidationError

from .config import LLM_BASE_URL, LLM_MODEL

logger = logging.getLogger("confluence_iq.llm_client")


def call_llm(
    system_prompt: str,
    user_content: str,
    output_schema: type[BaseModel],
    model: str = LLM_MODEL,
    max_retries: int = 2,
) -> tuple[BaseModel, str]:
    """Call POST /api/chat and return (parsed_output, thinking_text).

    Retries with a corrective follow-up message if the response doesn't
    conform to output_schema — Ollama's `format` constraint is not always
    strictly enforced by the model in practice.
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]
    last_error: ValidationError | None = None

    for attempt in range(max_retries + 1):
        response = httpx.post(
            f"{LLM_BASE_URL}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": False,
                "format": output_schema.model_json_schema(),
            },
            timeout=120.0,
        )
        response.raise_for_status()
        data = response.json()
        message = data["message"]
        thinking = message.get("thinking", "")

        try:
            output = output_schema.model_validate_json(message["content"])
            return output, thinking
        except ValidationError as exc:
            last_error = exc
            if attempt == max_retries:
                logger.warning(
                    "call_llm: %s failed schema validation on final attempt (%d/%d): %s",
                    output_schema.__name__, attempt + 1, max_retries + 1, exc,
                )
                break
            logger.warning(
                "call_llm: %s failed schema validation on attempt %d/%d, retrying with correction: %s",
                output_schema.__name__, attempt + 1, max_retries + 1, exc,
            )
            messages = messages + [
                {"role": "assistant", "content": message["content"]},
                {
                    "role": "user",
                    "content": (
                        "That response did not match the required schema. "
                        f"Validation error: {exc}\n\n"
                        "Respond again with ONLY valid JSON matching this exact schema:\n"
                        f"{output_schema.model_json_schema()}"
                    ),
                },
            ]

    raise last_error
