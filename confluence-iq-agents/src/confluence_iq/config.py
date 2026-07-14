"""Internal LLM endpoint configuration (api.iamtzar.com — no API key required)."""

import os
from dotenv import load_dotenv

load_dotenv()

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.iamtzar.com")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen3.5:397b-cloud")
LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "240.0"))
