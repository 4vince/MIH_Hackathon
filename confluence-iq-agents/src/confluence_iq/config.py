"""Model name, API key, and provider loading."""

import os
from dotenv import load_dotenv

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL") or None  # None -> provider default

def resolve_model() -> str:
    """Return the model string to pass to the LLM constructor."""
    if LLM_MODEL:
        return LLM_MODEL
    defaults = {"openai": "gpt-4o", "anthropic": "claude-sonnet-5", "ollama": "llama3"}
    return defaults.get(LLM_PROVIDER, "gpt-4o")
