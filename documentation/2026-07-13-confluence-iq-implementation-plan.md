# Confluence IQ Agents Implementation Plan

> **Status (2026-07-13): COMPLETE.** All 15 tasks below were executed via `superpowers:subagent-driven-development`, each with an independent task-level review, plus a final whole-branch review. Merged into `main`. The checkboxes below are left unchecked as originally written (historical record of the plan as authored on 2026-07-11) — treat this file as "what was planned," not "current status"; see `documentation/2026-07-13-confluence-iq-methodology-design.md` for the as-implemented architecture.
>
> **4 unplanned additions surfaced during execution, not in the task list below:**
> - **Task 11.5** (before Task 12): `call_llm()` needed a retry-with-correction loop — live testing found `qwen3.5:397b-cloud` doesn't always conform to Ollama's `format` schema constraint on the first attempt.
> - **Task 12.5** (after Task 12's review): the verifier didn't check `unanswered_buyer_questions` for grounding, and `call_llm`'s retries weren't logged — both closed.
> - **Task 16** (after the final whole-branch review): the verifier only checked Agent 3's output, not Agent 1/2's own numbers — added `verify_agent1_output`/`verify_agent2_output` so all three agents' output is grounded, not just the last one.
> - **Task 17** (after the final whole-branch review): `run.py` had no error handling around the live LLM call — added a broad `try/except` at that single outermost boundary so a live failure degrades cleanly instead of crashing.
>
> Full task-by-task ledger with review outcomes: `confluence-iq-agents/.superpowers/sdd/progress.md` (git-ignored; reconstruct from `git log` if ever lost).

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the `confluence-iq-agents` skeleton into a working Challenge 2 submission that passes all three PRD acceptance criteria, per the finalized design in `documentation/2026-07-13-confluence-iq-methodology-design.md`.

**Architecture:** LangGraph `StateGraph` with 5 nodes: `data_synthesizer` and `competitor_analyst` (parallel) → `content_strategist` → `verify` (deterministic claim-checking, no LLM) → `report_writer`. Each agent calls the internal Ollama-backed endpoint via a shared `httpx`-based `call_llm()` helper.

**Tech Stack:** Python 3.11+ (repo currently running 3.14.5), LangGraph, Pydantic v2, `httpx`, stdlib `logging` and `difflib`/regex for the verifier. No new dependencies beyond what's already in `requirements.txt`.

## Global Constraints

- Single command trigger: `python run.py` (no arguments — holistic report mode, not query-driven).
- Agents must visibly show context passing — console (INFO+) in real time and `output/transcript.log` (DEBUG+) as permanent record.
- Final report must contain: unanswered buyer questions, a specific content gap analysis, and opportunity prioritization.
- No hallucinations — enforced by a deterministic (non-LLM) verifier; unsourced claims are stripped and flagged, the pipeline still completes.
- LLM endpoint: `https://api.iamtzar.com/api/chat`, model `qwen3.5:397b-cloud`, no authentication, `"stream": false` required, response text at `response["message"]["content"]`.
- Out of scope: query-driven mode, RAG/vector DB, dashboard/RBAC, live scraping during demo (pre-scraped `.txt` files already committed).

---

## File Structure

**Create:**
- `confluence-iq-agents/pyproject.toml` — makes `src/` importable for both `python run.py` and `pytest`, no install step required
- `confluence-iq-agents/src/confluence_iq/logging_setup.py` — dual console/file logger
- `confluence-iq-agents/src/confluence_iq/llm_client.py` — `call_llm()` httpx helper
- `confluence-iq-agents/src/confluence_iq/verifier.py` — claim-level fact-checking
- `confluence-iq-agents/src/confluence_iq/prompts/data_synthesizer.md`
- `confluence-iq-agents/src/confluence_iq/prompts/competitor_analyst.md`
- `confluence-iq-agents/src/confluence_iq/prompts/content_strategist.md`
- `confluence-iq-agents/scripts/__init__.py` — empty, makes `scripts` importable in tests
- `confluence-iq-agents/tests/test_llm_client.py`
- `confluence-iq-agents/tests/test_verifier.py`
- `confluence-iq-agents/tests/test_markdown_report.py`
- `confluence-iq-agents/tests/test_graph_integration.py`
- `confluence-iq-agents/tests/test_scrape_basil_ford.py`

**Modify:**
- `confluence-iq-agents/run.py`
- `confluence-iq-agents/src/confluence_iq/config.py`
- `confluence-iq-agents/src/confluence_iq/schemas.py`
- `confluence-iq-agents/src/confluence_iq/graph.py`
- `confluence-iq-agents/src/confluence_iq/tools/loaders.py`
- `confluence-iq-agents/src/confluence_iq/report/markdown_report.py`
- `confluence-iq-agents/src/confluence_iq/agents/data_synthesizer.py`
- `confluence-iq-agents/src/confluence_iq/agents/competitor_analyst.py`
- `confluence-iq-agents/src/confluence_iq/agents/content_strategist.py`
- `confluence-iq-agents/scripts/scrape_basil_ford.py`
- `confluence-iq-agents/.env.example`
- `confluence-iq-agents/tests/test_data_synthesizer.py`
- `confluence-iq-agents/tests/test_competitor_analyst.py`
- `confluence-iq-agents/tests/test_content_strategist.py`

---

### Task 1: Fix broken package imports

**Files:**
- Create: `confluence-iq-agents/pyproject.toml`
- Modify: `confluence-iq-agents/run.py`

**Interfaces:**
- Produces: `src/` importable as `confluence_iq` from both `python run.py` (run from `confluence-iq-agents/`) and `pytest` — every later task depends on this.

- [ ] **Step 1: Confirm the current failure**

Run: `cd confluence-iq-agents && python run.py`
Expected: `ModuleNotFoundError: No module named 'confluence_iq'`

Run: `cd confluence-iq-agents && python -m pytest tests/ -v`
Expected: 3 collection errors, same `ModuleNotFoundError`.

- [ ] **Step 2: Create `pyproject.toml`**

```toml
[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

- [ ] **Step 3: Fix `run.py`'s import path**

Replace the full contents of `confluence-iq-agents/run.py`:

```python
"""Single entrypoint — builds and runs the Confluence IQ agent graph."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "src"))

from confluence_iq.graph import build_graph  # noqa: E402


def main() -> None:
    graph = build_graph()
    final_state = graph.invoke({})
    print(f"Report written to {final_state['report_path']}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Verify both entrypoints work**

Run: `cd confluence-iq-agents && python run.py`
Expected: no import error; the (still-stub) pipeline runs to completion and prints `Report written to output/report_<timestamp>.md`.

Run: `cd confluence-iq-agents && python -m pytest tests/ -v`
Expected: 3 tests collected and passing (stub agents still return hardcoded data at this point — that's expected, later tasks change this).

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml run.py
git commit -m "fix: make confluence_iq importable for run.py and pytest"
```

---

### Task 2: Add dual-output logging

**Files:**
- Create: `confluence-iq-agents/src/confluence_iq/logging_setup.py`
- Modify: `confluence-iq-agents/run.py`

**Interfaces:**
- Produces: `setup_logging() -> logging.Logger`, root logger name `"confluence_iq"`. All later agent/verifier/graph modules use `logging.getLogger("confluence_iq.<component>")` as children of this logger.

- [ ] **Step 1: Create `logging_setup.py`**

```python
"""Dual-output logging: console (INFO+) and output/transcript.log (DEBUG+)."""

import logging
import pathlib

OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent.parent / "output"


def setup_logging() -> logging.Logger:
    logger = logging.getLogger("confluence_iq")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(console)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(OUTPUT_DIR / "transcript.log", mode="w", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(name)s] %(levelname)s %(message)s")
    )
    logger.addHandler(file_handler)

    return logger
```

- [ ] **Step 2: Wire into `run.py`**

Replace the full contents of `confluence-iq-agents/run.py`:

```python
"""Single entrypoint — builds and runs the Confluence IQ agent graph."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "src"))

from confluence_iq.graph import build_graph  # noqa: E402
from confluence_iq.logging_setup import setup_logging  # noqa: E402


def main() -> None:
    logger = setup_logging()
    logger.info("Confluence IQ Agents — starting pipeline")
    graph = build_graph()
    final_state = graph.invoke({})
    logger.info("Report written to %s", final_state["report_path"])


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Verify logging output**

Run: `cd confluence-iq-agents && python run.py`
Expected: console prints `Confluence IQ Agents — starting pipeline` then `Report written to ...`; `output/transcript.log` is created and contains timestamped lines with the same messages.

- [ ] **Step 4: Commit**

```bash
git add src/confluence_iq/logging_setup.py run.py
git commit -m "feat: add dual console/transcript.log logging"
```

---

### Task 3: Simplify config for the internal endpoint

**Files:**
- Modify: `confluence-iq-agents/src/confluence_iq/config.py`
- Modify: `confluence-iq-agents/.env.example`

**Interfaces:**
- Produces: `LLM_BASE_URL: str`, `LLM_MODEL: str` module-level constants in `confluence_iq.config`. Consumed by Task 5's `llm_client.py`.
- Removes: `LLM_PROVIDER`, `LLM_API_KEY`, `resolve_model()` — no longer needed, the project targets exactly one endpoint per the PRD.

- [ ] **Step 1: Confirm nothing else references the old names**

Run: `cd confluence-iq-agents && grep -rn "LLM_PROVIDER\|LLM_API_KEY\|resolve_model" src/ tests/ run.py`
Expected: only matches inside `src/confluence_iq/config.py` itself.

- [ ] **Step 2: Replace `config.py`**

```python
"""Internal LLM endpoint configuration (api.iamtzar.com — no API key required)."""

import os
from dotenv import load_dotenv

load_dotenv()

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.iamtzar.com")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen3.5:397b-cloud")
```

- [ ] **Step 3: Update `.env.example`**

```
# Internal MIH hackathon LLM endpoint — no API key required
LLM_BASE_URL=https://api.iamtzar.com
LLM_MODEL=qwen3.5:397b-cloud
```

- [ ] **Step 4: Verify config imports cleanly**

Run: `cd confluence-iq-agents && python -c "from confluence_iq.config import LLM_BASE_URL, LLM_MODEL; print(LLM_BASE_URL, LLM_MODEL)"`
Expected: `https://api.iamtzar.com qwen3.5:397b-cloud`

- [ ] **Step 5: Commit**

```bash
git add src/confluence_iq/config.py .env.example
git commit -m "refactor: simplify config to the single internal LLM endpoint"
```

---

### Task 4: Enrich Pydantic schemas

**Files:**
- Modify: `confluence-iq-agents/src/confluence_iq/schemas.py`
- Test: `confluence-iq-agents/tests/test_schemas.py`

**Interfaces:**
- Produces: `CustomerSegment`, `Agent1Output`, `KeywordOpportunity`, `Agent2Output`, `ContentGap`, `Opportunity`, `Agent3Output` — these exact names/fields are used by every later task (agents, verifier, report writer).

- [ ] **Step 1: Write the failing test**

Create `confluence-iq-agents/tests/test_schemas.py`:

```python
"""Tests for enriched agent output schemas."""

import pytest
from pydantic import ValidationError

from confluence_iq.schemas import (
    Agent1Output,
    Agent2Output,
    Agent3Output,
    ContentGap,
    CustomerSegment,
    KeywordOpportunity,
    Opportunity,
)


def test_agent1_output_requires_customer_segments():
    output = Agent1Output(
        business_name="Basil Ford",
        location="Cheektowaga, NY",
        customer_segments=[
            CustomerSegment(name="Commuters", pain_points=["wait times"], faqs=["How long?"])
        ],
        key_insights=["insight one"],
        recommended_channels=["Google Ads"],
    )
    assert output.customer_segments[0].name == "Commuters"


def test_agent2_output_keyword_opportunity_fields():
    output = Agent2Output(
        site_summary={"basilford.com": "covers new/used inventory"},
        keyword_opportunities=[
            KeywordOpportunity(term="used cars niagara falls", volume=1900, difficulty=44, relevance="underrepresented")
        ],
        competitor_weaknesses=["low domain authority"],
        observed_content_gaps=["no FAQ page"],
    )
    assert output.keyword_opportunities[0].volume == 1900


def test_agent3_output_requires_three_report_elements():
    output = Agent3Output(
        unanswered_buyer_questions=["Does Basil Ford offer EV charging installation?"],
        content_gaps=[
            ContentGap(gap="No EV FAQ", site="basilford.com", severity="medium", evidence="some evidence")
        ],
        opportunity_prioritization=[
            Opportunity(rank=1, recommendation="Add EV FAQ", rationale="some rationale", effort="low")
        ],
    )
    assert len(output.unanswered_buyer_questions) == 1
    assert output.content_gaps[0].site == "basilford.com"
    assert output.opportunity_prioritization[0].rank == 1


def test_content_gap_missing_field_raises():
    with pytest.raises(ValidationError):
        ContentGap(gap="No EV FAQ", site="basilford.com", severity="medium")  # missing evidence
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd confluence-iq-agents && python -m pytest tests/test_schemas.py -v`
Expected: FAIL — `ImportError: cannot import name 'CustomerSegment'` (schemas.py doesn't have the new classes yet).

- [ ] **Step 3: Replace `schemas.py`**

```python
"""Pydantic models for the output of each agent node."""

from pydantic import BaseModel, Field


class CustomerSegment(BaseModel):
    name: str
    pain_points: list[str]
    faqs: list[str]


class Agent1Output(BaseModel):
    """Agent 1 — Data Synthesizer: structured summary of customer data."""
    business_name: str
    location: str
    customer_segments: list[CustomerSegment]
    key_insights: list[str]
    recommended_channels: list[str]


class KeywordOpportunity(BaseModel):
    term: str
    volume: int
    difficulty: int
    relevance: str = Field(..., description="e.g. 'well covered', 'underrepresented', 'not covered'")


class Agent2Output(BaseModel):
    """Agent 2 — Competitor Analyst: SEO / competitive landscape."""
    site_summary: dict[str, str] = Field(..., description="{domain: summary of what the site covers}")
    keyword_opportunities: list[KeywordOpportunity]
    competitor_weaknesses: list[str]
    observed_content_gaps: list[str]


class ContentGap(BaseModel):
    gap: str
    site: str
    severity: str = Field(..., description="'high' | 'medium' | 'low'")
    evidence: str = Field(..., description="Must trace to Agent1/Agent2 output or source data")


class Opportunity(BaseModel):
    rank: int
    recommendation: str
    rationale: str = Field(..., description="Must trace to Agent1/Agent2 output or source data")
    effort: str = Field(..., description="'low' | 'medium' | 'high'")


class Agent3Output(BaseModel):
    """Agent 3 — Content Strategist: content-gap analysis + prioritization."""
    unanswered_buyer_questions: list[str]
    content_gaps: list[ContentGap]
    opportunity_prioritization: list[Opportunity]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd confluence-iq-agents && python -m pytest tests/test_schemas.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add src/confluence_iq/schemas.py tests/test_schemas.py
git commit -m "feat: enrich agent output schemas for content-gap analysis"
```

---

### Task 5: LLM client (`call_llm`)

**Files:**
- Create: `confluence-iq-agents/src/confluence_iq/llm_client.py`
- Test: `confluence-iq-agents/tests/test_llm_client.py`

**Interfaces:**
- Consumes: `confluence_iq.config.LLM_BASE_URL`, `LLM_MODEL` (Task 3).
- Produces: `call_llm(system_prompt: str, user_content: str, output_schema: type[BaseModel], model: str = LLM_MODEL) -> tuple[BaseModel, str]` — returns `(parsed_output, thinking_text)`. Used by every agent in Tasks 7–9.

- [ ] **Step 1: Write the failing test**

Create `confluence-iq-agents/tests/test_llm_client.py`:

```python
"""Tests for the internal LLM client (HTTP layer mocked — no live network calls)."""

from unittest.mock import MagicMock, patch

from confluence_iq.llm_client import call_llm
from confluence_iq.schemas import Agent1Output, CustomerSegment


def _fake_agent1_output() -> Agent1Output:
    return Agent1Output(
        business_name="Basil Ford",
        location="Cheektowaga, NY",
        customer_segments=[
            CustomerSegment(name="Commuters", pain_points=["wait times"], faqs=["How long is a service visit?"])
        ],
        key_insights=["insight"],
        recommended_channels=["Google Ads"],
    )


@patch("confluence_iq.llm_client.httpx.post")
def test_call_llm_parses_message_content_and_thinking(mock_post):
    fake_output = _fake_agent1_output()
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "message": {
            "role": "assistant",
            "content": fake_output.model_dump_json(),
            "thinking": "reasoning trace",
        },
        "done": True,
    }
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    output, thinking = call_llm(
        system_prompt="system prompt",
        user_content="user content",
        output_schema=Agent1Output,
    )

    assert output.business_name == "Basil Ford"
    assert thinking == "reasoning trace"


@patch("confluence_iq.llm_client.httpx.post")
def test_call_llm_hits_correct_route_with_structured_format(mock_post):
    fake_output = _fake_agent1_output()
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "message": {"role": "assistant", "content": fake_output.model_dump_json(), "thinking": ""},
        "done": True,
    }
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    call_llm(system_prompt="sys", user_content="usr", output_schema=Agent1Output, model="qwen3.5:397b-cloud")

    call_url = mock_post.call_args[0][0]
    call_kwargs = mock_post.call_args[1]
    assert call_url.endswith("/api/chat")
    assert call_kwargs["json"]["model"] == "qwen3.5:397b-cloud"
    assert call_kwargs["json"]["stream"] is False
    assert call_kwargs["json"]["format"] == Agent1Output.model_json_schema()
    assert call_kwargs["json"]["messages"] == [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "usr"},
    ]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd confluence-iq-agents && python -m pytest tests/test_llm_client.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'confluence_iq.llm_client'`.

- [ ] **Step 3: Create `llm_client.py`**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd confluence-iq-agents && python -m pytest tests/test_llm_client.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add src/confluence_iq/llm_client.py tests/test_llm_client.py
git commit -m "feat: add httpx-based call_llm client for api.iamtzar.com"
```

---

### Task 6: Prompts and loader helpers

**Files:**
- Create: `confluence-iq-agents/src/confluence_iq/prompts/data_synthesizer.md`
- Create: `confluence-iq-agents/src/confluence_iq/prompts/competitor_analyst.md`
- Create: `confluence-iq-agents/src/confluence_iq/prompts/content_strategist.md`
- Modify: `confluence-iq-agents/src/confluence_iq/tools/loaders.py`
- Test: `confluence-iq-agents/tests/test_loaders.py`

**Interfaces:**
- Produces: `load_prompt(name: str) -> str`, `load_raw_corpus_text() -> str` in `confluence_iq.tools.loaders`. Used by Tasks 7–9 (`load_prompt`) and Task 12's `verify` node (`load_raw_corpus_text`).

- [ ] **Step 1: Write the failing test**

Create `confluence-iq-agents/tests/test_loaders.py`:

```python
"""Tests for data/prompt loaders."""

from confluence_iq.tools.loaders import load_prompt, load_raw_corpus_text


def test_load_prompt_returns_grounding_rule():
    prompt = load_prompt("data_synthesizer")
    assert "GROUNDING RULE" in prompt


def test_load_raw_corpus_text_includes_customer_and_site_data():
    corpus = load_raw_corpus_text()
    assert "Basil Ford" in corpus
    assert "trade-in" in corpus.lower() or "trade-in value" in corpus
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd confluence-iq-agents && python -m pytest tests/test_loaders.py -v`
Expected: FAIL — `ImportError: cannot import name 'load_prompt'`.

- [ ] **Step 3: Create the 3 prompt files**

Create `confluence-iq-agents/src/confluence_iq/prompts/data_synthesizer.md`:

```markdown
You are a marketing data analyst for a Ford dealership. You will be given raw first-party customer data as JSON.

Your task:
1. Identify each customer segment described in the data.
2. For each segment, list its pain points (use the data's own wording where possible) and infer 2-3 realistic FAQs that segment would ask a dealership, grounded in those pain points.
3. Identify 2-4 key insights from the data as a whole (e.g. patterns across segments, revenue mix implications).
4. Recommend marketing channels based on the data's current_marketing_channels field.

GROUNDING RULE: Use ONLY the customer data provided below. Do not invent segments, pain points, or statistics that are not present in or directly inferable from the data. Do not use external knowledge about Ford dealerships in general.

Respond with valid JSON matching the required schema exactly.
```

Create `confluence-iq-agents/src/confluence_iq/prompts/competitor_analyst.md`:

```markdown
You are an SEO and competitive-intelligence analyst. You will be given SEO keyword trend data and scraped text from two dealership websites (Basil Ford, Basil Ford of Niagara Falls) as JSON.

Your task:
1. Summarize what each site's scraped text actually covers, one summary string per domain.
2. Identify keyword opportunities: for each keyword in the trend data, note its term, volume, difficulty, and how relevant it is to the scraped site content (e.g. "well covered", "underrepresented", "not covered").
3. Identify competitor weaknesses based on the domain authority figures in the trend data.
4. List specific content gaps: topics implied by the keyword data that are missing or thin in the scraped site text.

GROUNDING RULE: Use ONLY the SEO trends and site text provided below. Every keyword, volume, and difficulty score you report must come directly from the provided data — do not invent search volumes or difficulty scores. Do not use external knowledge about SEO best practices beyond what's needed to structure your answer.

Respond with valid JSON matching the required schema exactly.
```

Create `confluence-iq-agents/src/confluence_iq/prompts/content_strategist.md`:

```markdown
You are a senior content strategist for a Ford dealership group. You will be given two prior analyses as JSON: Agent 1's customer insights (segments, pain points, FAQs, key insights) and Agent 2's competitive analysis (site summaries, keyword opportunities, competitor weaknesses, content gaps).

Your task:
1. List unanswered buyer questions: specific questions from Agent 1's FAQs that are not addressed by Agent 2's site summaries or content gap findings.
2. Identify content gaps: for each gap, name the specific missing content (gap), which site it affects (site), a severity ("high"/"medium"/"low"), and evidence — a short justification that quotes or closely paraphrases a specific fact from Agent 1's or Agent 2's output.
3. Prioritize opportunities: rank recommendations by impact, each with a rationale that must quote or closely paraphrase a specific fact from Agent 1's or Agent 2's output, and an effort estimate ("low"/"medium"/"high").

GROUNDING RULE: Every "evidence" and "rationale" field must be traceable to a specific fact in Agent 1's or Agent 2's output provided below. Do not fabricate statistics, quotes, or facts not present in the provided JSON. Do not use external knowledge about Ford dealerships, Basil Ford, or SEO trends beyond what's in the provided JSON.

Respond with valid JSON matching the required schema exactly.
```

- [ ] **Step 4: Add loader functions**

Add to the end of `confluence-iq-agents/src/confluence_iq/tools/loaders.py` (keep the existing `load_customer_data`, `load_seo_trends`, `load_site_texts` functions unchanged above this):

```python
PROMPTS_DIR = HERE.parent / "prompts"


def load_prompt(name: str) -> str:
    path = PROMPTS_DIR / f"{name}.md"
    return path.read_text(encoding="utf-8")


def load_raw_corpus_text() -> str:
    """Concatenate all raw source data into one text blob for the verifier."""
    import json

    customer_data = json.dumps(load_customer_data())
    seo_trends = json.dumps(load_seo_trends())
    site_texts = "\n".join(load_site_texts().values())
    return "\n".join([customer_data, seo_trends, site_texts])
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd confluence-iq-agents && python -m pytest tests/test_loaders.py -v`
Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add src/confluence_iq/prompts/ src/confluence_iq/tools/loaders.py tests/test_loaders.py
git commit -m "feat: add agent prompts and prompt/corpus loader helpers"
```

---

### Task 7: Agent 1 — Data Synthesizer (real LLM call)

**Files:**
- Modify: `confluence-iq-agents/src/confluence_iq/agents/data_synthesizer.py`
- Modify: `confluence-iq-agents/tests/test_data_synthesizer.py`

**Interfaces:**
- Consumes: `call_llm` (Task 5), `load_prompt`, `load_customer_data` (Task 6), `Agent1Output` (Task 4).
- Produces: `DataSynthesizerAgent.run(state: dict) -> dict` returning `{"agent1_output": dict}` — unchanged signature, consumed by Task 12's graph wiring.

- [ ] **Step 1: Write the failing test**

Replace the full contents of `confluence-iq-agents/tests/test_data_synthesizer.py`:

```python
"""Tests for Agent 1 — Data Synthesizer."""

from unittest.mock import patch

from confluence_iq.agents.data_synthesizer import DataSynthesizerAgent
from confluence_iq.schemas import Agent1Output, CustomerSegment


def _fake_agent1_output() -> Agent1Output:
    return Agent1Output(
        business_name="Basil Ford of Niagara Falls",
        location="Niagara Falls, ON",
        customer_segments=[
            CustomerSegment(
                name="Local commuters",
                pain_points=["trade-in value transparency"],
                faqs=["How is my trade-in value calculated?"],
            )
        ],
        key_insights=["New vehicle sales make up 45% of revenue"],
        recommended_channels=["Google Ads", "Facebook"],
    )


@patch("confluence_iq.agents.data_synthesizer.call_llm")
def test_run_returns_valid_agent1_output(mock_call_llm):
    mock_call_llm.return_value = (_fake_agent1_output(), "reasoning text")

    result = DataSynthesizerAgent.run({})

    assert "agent1_output" in result
    output = Agent1Output(**result["agent1_output"])
    assert len(output.customer_segments) > 0
    assert all(seg.name for seg in output.customer_segments)


@patch("confluence_iq.agents.data_synthesizer.call_llm")
def test_run_passes_real_customer_data_to_llm(mock_call_llm):
    mock_call_llm.return_value = (_fake_agent1_output(), "reasoning text")

    DataSynthesizerAgent.run({})

    _, kwargs = mock_call_llm.call_args
    assert "Basil Ford" in kwargs["user_content"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd confluence-iq-agents && python -m pytest tests/test_data_synthesizer.py -v`
Expected: FAIL — the current stub ignores `call_llm` entirely, so `mock_call_llm.call_args` is `None` (`AttributeError`) on the second test; the first test fails schema validation since the stub still returns the old sparse shape.

- [ ] **Step 3: Replace `data_synthesizer.py`**

```python
"""Agent 1 — Data Synthesizer: ground customer data into structured insights."""

import json
import logging

from ..llm_client import call_llm
from ..schemas import Agent1Output
from ..tools.loaders import load_customer_data, load_prompt

logger = logging.getLogger("confluence_iq.agent1")


class DataSynthesizerAgent:

    @staticmethod
    def run(state: dict) -> dict:
        logger.info("=== Agent 1: Data Synthesizer ===")
        data = load_customer_data()
        logger.info(
            "Loaded customer data for %s (%d segments)",
            data["business_name"],
            len(data.get("customer_segments", [])),
        )

        prompt = load_prompt("data_synthesizer")
        output, thinking = call_llm(
            system_prompt=prompt,
            user_content=f"Customer data:\n{json.dumps(data, indent=2)}",
            output_schema=Agent1Output,
        )
        logger.debug("Agent 1 model reasoning: %s", thinking)
        logger.info(
            "Agent 1 found %d customer segments, %d key insights",
            len(output.customer_segments),
            len(output.key_insights),
        )
        logger.info("Agent 1 complete. Passing to Content Strategist.")

        return {"agent1_output": output.model_dump()}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd confluence-iq-agents && python -m pytest tests/test_data_synthesizer.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add src/confluence_iq/agents/data_synthesizer.py tests/test_data_synthesizer.py
git commit -m "feat: Agent 1 calls the real LLM instead of returning hardcoded data"
```

---

### Task 8: Agent 2 — Competitor Analyst (real LLM call)

**Files:**
- Modify: `confluence-iq-agents/src/confluence_iq/agents/competitor_analyst.py`
- Modify: `confluence-iq-agents/tests/test_competitor_analyst.py`

**Interfaces:**
- Consumes: `call_llm`, `load_prompt`, `load_seo_trends`, `load_site_texts`, `Agent2Output`.
- Produces: `CompetitorAnalystAgent.run(state: dict) -> dict` returning `{"agent2_output": dict}`.

- [ ] **Step 1: Write the failing test**

Replace the full contents of `confluence-iq-agents/tests/test_competitor_analyst.py`:

```python
"""Tests for Agent 2 — Competitor Analyst."""

from unittest.mock import patch

from confluence_iq.agents.competitor_analyst import CompetitorAnalystAgent
from confluence_iq.schemas import Agent2Output, KeywordOpportunity


def _fake_agent2_output() -> Agent2Output:
    return Agent2Output(
        site_summary={"basilford_com": "covers new/used inventory and service"},
        keyword_opportunities=[
            KeywordOpportunity(term="used cars niagara falls ontario", volume=1900, difficulty=44, relevance="underrepresented")
        ],
        competitor_weaknesses=["low domain authority"],
        observed_content_gaps=["no EV charging FAQ"],
    )


@patch("confluence_iq.agents.competitor_analyst.call_llm")
def test_run_returns_valid_agent2_output(mock_call_llm):
    mock_call_llm.return_value = (_fake_agent2_output(), "reasoning text")

    result = CompetitorAnalystAgent.run({})

    assert "agent2_output" in result
    output = Agent2Output(**result["agent2_output"])
    assert len(output.keyword_opportunities) > 0


@patch("confluence_iq.agents.competitor_analyst.call_llm")
def test_run_passes_seo_trends_and_site_text_to_llm(mock_call_llm):
    mock_call_llm.return_value = (_fake_agent2_output(), "reasoning text")

    CompetitorAnalystAgent.run({})

    _, kwargs = mock_call_llm.call_args
    assert "niagara falls" in kwargs["user_content"].lower()
    assert "basilford_com" in kwargs["user_content"] or "Basil Ford" in kwargs["user_content"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd confluence-iq-agents && python -m pytest tests/test_competitor_analyst.py -v`
Expected: FAIL — stub doesn't call `call_llm` and returns the old sparse output shape.

- [ ] **Step 3: Replace `competitor_analyst.py`**

```python
"""Agent 2 — Competitor Analyst: SEO trends + site text analysis."""

import json
import logging

from ..llm_client import call_llm
from ..schemas import Agent2Output
from ..tools.loaders import load_prompt, load_seo_trends, load_site_texts

logger = logging.getLogger("confluence_iq.agent2")


class CompetitorAnalystAgent:

    @staticmethod
    def run(state: dict) -> dict:
        logger.info("=== Agent 2: Competitor Analyst ===")
        trends = load_seo_trends()
        site_texts = load_site_texts()
        logger.info(
            "Loaded SEO trends (%d keywords) and site text for %d domains",
            len(trends.get("keywords", [])),
            len(site_texts),
        )

        prompt = load_prompt("competitor_analyst")
        user_content = (
            f"SEO trends:\n{json.dumps(trends, indent=2)}\n\n"
            f"Scraped site text:\n{json.dumps(site_texts, indent=2)}"
        )
        output, thinking = call_llm(
            system_prompt=prompt,
            user_content=user_content,
            output_schema=Agent2Output,
        )
        logger.debug("Agent 2 model reasoning: %s", thinking)
        logger.info(
            "Agent 2 found %d keyword opportunities, %d content gaps",
            len(output.keyword_opportunities),
            len(output.observed_content_gaps),
        )
        logger.info("Agent 2 complete. Passing to Content Strategist.")

        return {"agent2_output": output.model_dump()}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd confluence-iq-agents && python -m pytest tests/test_competitor_analyst.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add src/confluence_iq/agents/competitor_analyst.py tests/test_competitor_analyst.py
git commit -m "feat: Agent 2 calls the real LLM instead of returning hardcoded data"
```

---

### Task 9: Agent 3 — Content Strategist (real LLM call, actually consumes state)

**Files:**
- Modify: `confluence-iq-agents/src/confluence_iq/agents/content_strategist.py`
- Modify: `confluence-iq-agents/tests/test_content_strategist.py`

**Interfaces:**
- Consumes: `call_llm`, `load_prompt`, `Agent3Output`. Consumes `state["agent1_output"]` and `state["agent2_output"]` (both guaranteed present by the graph's join edges — Task 12).
- Produces: `ContentStrategistAgent.run(state: dict) -> dict` returning `{"agent3_output": dict}`. **This fixes the bug where Agent 3 previously ignored `state` entirely** — the acceptance criterion "agents visibly show they're talking to each other" requires this to actually happen, not just be logged.

- [ ] **Step 1: Write the failing test**

Replace the full contents of `confluence-iq-agents/tests/test_content_strategist.py`:

```python
"""Tests for Agent 3 — Content Strategist."""

from unittest.mock import patch

from confluence_iq.agents.content_strategist import ContentStrategistAgent
from confluence_iq.schemas import Agent3Output, ContentGap, Opportunity


def _fake_agent3_output() -> Agent3Output:
    return Agent3Output(
        unanswered_buyer_questions=["Does Basil Ford offer EV charging installation?"],
        content_gaps=[
            ContentGap(
                gap="No EV charging FAQ page",
                site="basilford.com",
                severity="medium",
                evidence="Agent 1 found EV charging confusion among the tourist segment",
            )
        ],
        opportunity_prioritization=[
            Opportunity(
                rank=1,
                recommendation="Add an EV charging FAQ page",
                rationale="Matches Agent 2's underrepresented keyword gap",
                effort="low",
            )
        ],
    )


def _state_with_agent1_and_agent2() -> dict:
    return {
        "agent1_output": {
            "business_name": "Basil Ford of Niagara Falls",
            "location": "Niagara Falls, ON",
            "customer_segments": [],
            "key_insights": [],
            "recommended_channels": [],
        },
        "agent2_output": {
            "site_summary": {},
            "keyword_opportunities": [],
            "competitor_weaknesses": [],
            "observed_content_gaps": [],
        },
    }


@patch("confluence_iq.agents.content_strategist.call_llm")
def test_run_returns_valid_agent3_output(mock_call_llm):
    mock_call_llm.return_value = (_fake_agent3_output(), "reasoning text")

    result = ContentStrategistAgent.run(_state_with_agent1_and_agent2())

    assert "agent3_output" in result
    output = Agent3Output(**result["agent3_output"])
    assert len(output.content_gaps) > 0


@patch("confluence_iq.agents.content_strategist.call_llm")
def test_run_actually_consumes_agent1_and_agent2_state(mock_call_llm):
    """Regression test for the bug where Agent 3 ignored `state` entirely."""
    mock_call_llm.return_value = (_fake_agent3_output(), "reasoning text")

    ContentStrategistAgent.run(_state_with_agent1_and_agent2())

    _, kwargs = mock_call_llm.call_args
    assert "Niagara Falls" in kwargs["user_content"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd confluence-iq-agents && python -m pytest tests/test_content_strategist.py -v`
Expected: FAIL — the stub returns hardcoded `"Placeholder."` sections matching the old schema, and never calls `call_llm`.

- [ ] **Step 3: Replace `content_strategist.py`**

```python
"""Agent 3 — Content Strategist: synthesise agent 1 & 2 into a report draft."""

import json
import logging

from ..llm_client import call_llm
from ..schemas import Agent3Output
from ..tools.loaders import load_prompt

logger = logging.getLogger("confluence_iq.agent3")


class ContentStrategistAgent:

    @staticmethod
    def run(state: dict) -> dict:
        logger.info("=== Agent 3: Content Strategist ===")
        agent1_output = state["agent1_output"]
        agent2_output = state["agent2_output"]
        logger.info(
            "Received Agent 1 output (%d segments) and Agent 2 output (%d keyword opportunities)",
            len(agent1_output["customer_segments"]),
            len(agent2_output["keyword_opportunities"]),
        )

        prompt = load_prompt("content_strategist")
        user_content = (
            f"Agent 1 output (customer insights):\n{json.dumps(agent1_output, indent=2)}\n\n"
            f"Agent 2 output (competitive analysis):\n{json.dumps(agent2_output, indent=2)}"
        )
        output, thinking = call_llm(
            system_prompt=prompt,
            user_content=user_content,
            output_schema=Agent3Output,
        )
        logger.debug("Agent 3 model reasoning: %s", thinking)
        logger.info(
            "Agent 3 drafted %d unanswered questions, %d content gaps, %d opportunities",
            len(output.unanswered_buyer_questions),
            len(output.content_gaps),
            len(output.opportunity_prioritization),
        )
        logger.info("Agent 3 complete. Passing to Verifier.")

        return {"agent3_output": output.model_dump()}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd confluence-iq-agents && python -m pytest tests/test_content_strategist.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add src/confluence_iq/agents/content_strategist.py tests/test_content_strategist.py
git commit -m "fix: Agent 3 now actually consumes Agent 1/2 state instead of ignoring it"
```

---

### Task 10: Verifier — claim-level fact-checking

**Files:**
- Create: `confluence-iq-agents/src/confluence_iq/verifier.py`
- Test: `confluence-iq-agents/tests/test_verifier.py`

**Interfaces:**
- Consumes: `Agent3Output` (Task 4).
- Produces: `claim_is_grounded(claim: str, corpus: str, threshold: float = 0.6) -> bool` and `verify_agent3_output(agent3_output: Agent3Output, agent1_output: dict, agent2_output: dict, raw_corpus: str) -> tuple[Agent3Output, list[str]]`. Used by Task 12's `verify` graph node.
- Algorithm (concrete, not a placeholder): tokenize on `[a-z0-9]+` (lowercased), drop a fixed stopword list and any token shorter than 3 characters, compute `|claim_words ∩ corpus_words| / |claim_words|`; a claim with no significant words is vacuously grounded (returns `True`).

- [ ] **Step 1: Write the failing test**

Create `confluence-iq-agents/tests/test_verifier.py`:

```python
"""Tests for the deterministic claim verifier (no LLM involved)."""

from confluence_iq.schemas import Agent3Output, ContentGap, Opportunity
from confluence_iq.verifier import claim_is_grounded, verify_agent3_output


def test_claim_is_grounded_true_for_matching_text():
    corpus = "Local commuters reported trade-in value transparency concerns during service visits."
    claim = "trade-in value transparency"
    assert claim_is_grounded(claim, corpus) is True


def test_claim_is_grounded_false_for_fabricated_text():
    corpus = "Local commuters reported trade-in value transparency concerns during service visits."
    claim = "used cars niagara falls ontario gets 1900 monthly searches at 44 difficulty"
    assert claim_is_grounded(claim, corpus) is False


def test_verify_agent3_output_strips_unsourced_claims():
    agent3_output = Agent3Output(
        unanswered_buyer_questions=["Does Basil Ford offer EV charging installation?"],
        content_gaps=[
            ContentGap(
                gap="No EV FAQ", site="basilford.com", severity="medium",
                evidence="tourists reported EV charging confusion",
            ),
            ContentGap(
                gap="Fabricated gap", site="basilford.com", severity="high",
                evidence="internal survey shows 92 percent satisfaction rate",
            ),
        ],
        opportunity_prioritization=[
            Opportunity(
                rank=1, recommendation="Add EV FAQ",
                rationale="tourists reported EV charging confusion", effort="low",
            ),
        ],
    )
    corpus = "Tourists and seasonal visitors reported EV charging confusion and rental versus purchase questions."

    cleaned, flagged = verify_agent3_output(agent3_output, {}, {}, corpus)

    assert len(cleaned.content_gaps) == 1
    assert cleaned.content_gaps[0].gap == "No EV FAQ"
    assert len(cleaned.opportunity_prioritization) == 1
    assert len(flagged) == 1
    assert "Fabricated gap" in flagged[0]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd confluence-iq-agents && python -m pytest tests/test_verifier.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'confluence_iq.verifier'`.

- [ ] **Step 3: Create `verifier.py`**

```python
"""Deterministic (non-LLM) claim verifier — enforces the 'No Hallucinations' requirement."""

import json
import re

from .schemas import Agent3Output

_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "is", "are", "was", "were", "be", "been", "this", "that",
    "it", "as", "by", "from", "has", "have", "had", "not", "no",
}


def _significant_words(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w for w in words if w not in _STOPWORDS and len(w) >= 3}


def claim_is_grounded(claim: str, corpus: str, threshold: float = 0.6) -> bool:
    """Deterministic keyword-overlap check — no LLM call."""
    claim_words = _significant_words(claim)
    if not claim_words:
        return True
    corpus_words = _significant_words(corpus)
    overlap = claim_words & corpus_words
    return (len(overlap) / len(claim_words)) >= threshold


def verify_agent3_output(
    agent3_output: Agent3Output,
    agent1_output: dict,
    agent2_output: dict,
    raw_corpus: str,
) -> tuple[Agent3Output, list[str]]:
    """Strip content gaps / opportunities whose evidence/rationale isn't grounded in source data."""
    corpus = " ".join([json.dumps(agent1_output), json.dumps(agent2_output), raw_corpus])
    flagged: list[str] = []

    kept_gaps = []
    for gap in agent3_output.content_gaps:
        if claim_is_grounded(gap.evidence, corpus):
            kept_gaps.append(gap)
        else:
            flagged.append(f'Content gap "{gap.gap}" — unsourced evidence: "{gap.evidence}"')

    kept_opportunities = []
    for opp in agent3_output.opportunity_prioritization:
        if claim_is_grounded(opp.rationale, corpus):
            kept_opportunities.append(opp)
        else:
            flagged.append(f'Opportunity "{opp.recommendation}" — unsourced rationale: "{opp.rationale}"')

    cleaned = agent3_output.model_copy(update={
        "content_gaps": kept_gaps,
        "opportunity_prioritization": kept_opportunities,
    })
    return cleaned, flagged
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd confluence-iq-agents && python -m pytest tests/test_verifier.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add src/confluence_iq/verifier.py tests/test_verifier.py
git commit -m "feat: add deterministic claim verifier enforcing no-hallucinations rule"
```

---

### Task 11: Report writer — render full report + flagged claims

**Files:**
- Modify: `confluence-iq-agents/src/confluence_iq/report/markdown_report.py`
- Test: `confluence-iq-agents/tests/test_markdown_report.py`

**Interfaces:**
- Consumes: `Agent1Output`, `Agent2Output`, `Agent3Output` (Task 4).
- Produces: `write_report(agent1_output: Agent1Output, agent2_output: Agent2Output, agent3_output: Agent3Output, flagged_claims: list[str]) -> str` (returns the written file path). **Signature change from the current `write_report(output: Agent3Output) -> str`** — Task 12's `report_writer` node passes all three outputs so the report can render Customer Insights / Competitive Landscape sections directly from Agent 1/2 data without needing extra LLM-authored fields.

- [ ] **Step 1: Write the failing test**

Create `confluence-iq-agents/tests/test_markdown_report.py`:

```python
"""Tests for the markdown report writer."""

from confluence_iq.report.markdown_report import write_report
from confluence_iq.schemas import (
    Agent1Output, Agent2Output, Agent3Output,
    ContentGap, CustomerSegment, KeywordOpportunity, Opportunity,
)


def _agent1() -> Agent1Output:
    return Agent1Output(
        business_name="Basil Ford of Niagara Falls",
        location="Niagara Falls, ON",
        customer_segments=[
            CustomerSegment(name="Local commuters", pain_points=["trade-in value transparency"], faqs=["How is my trade-in value calculated?"])
        ],
        key_insights=["New vehicle sales make up 45% of revenue"],
        recommended_channels=["Google Ads"],
    )


def _agent2() -> Agent2Output:
    return Agent2Output(
        site_summary={"basilford_com": "covers new/used inventory"},
        keyword_opportunities=[
            KeywordOpportunity(term="used cars niagara falls", volume=1900, difficulty=44, relevance="underrepresented")
        ],
        competitor_weaknesses=["low domain authority"],
        observed_content_gaps=["no EV FAQ"],
    )


def _agent3() -> Agent3Output:
    return Agent3Output(
        unanswered_buyer_questions=["Does Basil Ford offer EV charging installation?"],
        content_gaps=[
            ContentGap(gap="No EV FAQ", site="basilford.com", severity="medium", evidence="tourists reported EV charging confusion")
        ],
        opportunity_prioritization=[
            Opportunity(rank=1, recommendation="Add EV FAQ", rationale="matches keyword gap", effort="low")
        ],
    )


def test_write_report_includes_required_sections(tmp_path, monkeypatch):
    import confluence_iq.report.markdown_report as mr
    monkeypatch.setattr(mr, "OUTPUT_DIR", tmp_path)

    path = write_report(_agent1(), _agent2(), _agent3(), [])

    text = mr.pathlib.Path(path).read_text(encoding="utf-8")
    assert "## Unanswered Buyer Questions" in text
    assert "## Content Gap Analysis" in text
    assert "## Opportunity Prioritization" in text
    assert "Does Basil Ford offer EV charging installation?" in text
    assert "⚠ Flagged Claims" not in text


def test_write_report_shows_flagged_claims_when_present(tmp_path, monkeypatch):
    import confluence_iq.report.markdown_report as mr
    monkeypatch.setattr(mr, "OUTPUT_DIR", tmp_path)

    path = write_report(_agent1(), _agent2(), _agent3(), ["Fabricated claim example"])

    text = mr.pathlib.Path(path).read_text(encoding="utf-8")
    assert "⚠ Flagged Claims" in text
    assert "Fabricated claim example" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd confluence-iq-agents && python -m pytest tests/test_markdown_report.py -v`
Expected: FAIL — `write_report()` currently takes a single `Agent3Output` argument (`TypeError: write_report() takes 1 positional argument but 4 were given`).

- [ ] **Step 3: Replace `markdown_report.py`**

```python
"""Agent 1/2/3 outputs → final .md file in output/."""

import pathlib
from datetime import datetime

from ..schemas import Agent1Output, Agent2Output, Agent3Output

OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent.parent.parent / "output"


def write_report(
    agent1_output: Agent1Output,
    agent2_output: Agent2Output,
    agent3_output: Agent3Output,
    flagged_claims: list[str],
) -> str:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = OUTPUT_DIR / f"report_{timestamp}.md"

    lines = ["# Confluence IQ Market Intelligence Report — Basil Ford\n"]

    lines.append("## Executive Summary\n")
    lines.append(
        f"Analysis of {agent1_output.business_name} ({agent1_output.location}) covering "
        f"{len(agent1_output.customer_segments)} customer segment(s), "
        f"{len(agent2_output.keyword_opportunities)} keyword opportunity/ies, "
        f"{len(agent3_output.content_gaps)} content gap(s), and "
        f"{len(agent3_output.opportunity_prioritization)} prioritized recommendation(s).\n"
    )

    lines.append("## Customer Insights (Agent 1)\n")
    for segment in agent1_output.customer_segments:
        lines.append(f"### {segment.name}")
        lines.append("**Pain points:** " + ", ".join(segment.pain_points))
        lines.append("**FAQs:** " + ", ".join(segment.faqs))
        lines.append("")
    if agent1_output.key_insights:
        lines.append("**Key insights:**")
        for insight in agent1_output.key_insights:
            lines.append(f"- {insight}")
        lines.append("")

    lines.append("## Competitive Landscape (Agent 2)\n")
    for domain, summary in agent2_output.site_summary.items():
        lines.append(f"**{domain}:** {summary}")
    lines.append("")
    if agent2_output.keyword_opportunities:
        lines.append("**Keyword opportunities:**")
        for kw in agent2_output.keyword_opportunities:
            lines.append(f"- {kw.term} (volume: {kw.volume}, difficulty: {kw.difficulty}, relevance: {kw.relevance})")
        lines.append("")
    if agent2_output.competitor_weaknesses:
        lines.append("**Competitor weaknesses:**")
        for weakness in agent2_output.competitor_weaknesses:
            lines.append(f"- {weakness}")
        lines.append("")

    lines.append("## Unanswered Buyer Questions\n")
    for question in agent3_output.unanswered_buyer_questions:
        lines.append(f"- {question}")
    lines.append("")

    lines.append("## Content Gap Analysis\n")
    lines.append("| Gap | Site | Severity | Evidence |")
    lines.append("|---|---|---|---|")
    for gap in agent3_output.content_gaps:
        lines.append(f"| {gap.gap} | {gap.site} | {gap.severity} | {gap.evidence} |")
    lines.append("")

    lines.append("## Opportunity Prioritization\n")
    lines.append("| Rank | Recommendation | Rationale | Effort |")
    lines.append("|---|---|---|---|")
    for opp in sorted(agent3_output.opportunity_prioritization, key=lambda o: o.rank):
        lines.append(f"| {opp.rank} | {opp.recommendation} | {opp.rationale} | {opp.effort} |")
    lines.append("")

    if flagged_claims:
        lines.append("## ⚠ Flagged Claims (Unverified)\n")
        for claim in flagged_claims:
            lines.append(f"- {claim}")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd confluence-iq-agents && python -m pytest tests/test_markdown_report.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add src/confluence_iq/report/markdown_report.py tests/test_markdown_report.py
git commit -m "feat: report writer renders full report from all 3 agent outputs + flagged claims"
```

---

### Task 12: Wire verify + report_writer nodes into the graph

**Files:**
- Modify: `confluence-iq-agents/src/confluence_iq/graph.py`
- Test: `confluence-iq-agents/tests/test_graph_integration.py`

**Interfaces:**
- Consumes: all agents (Tasks 7–9), `verify_agent3_output` (Task 10), `write_report` (Task 11), `load_raw_corpus_text` (Task 6).
- Produces: `build_graph() -> CompiledGraph` — `AgentState` gains a `flagged_claims: Optional[list]` field. This is the end-to-end integration point; its test is the strongest evidence the "agents visibly passing context" and "no hallucinations" criteria are actually met.

- [ ] **Step 1: Write the failing integration test**

Create `confluence-iq-agents/tests/test_graph_integration.py`:

```python
"""End-to-end integration test for the full graph (all LLM calls mocked)."""

from unittest.mock import patch

from confluence_iq.graph import build_graph
from confluence_iq.schemas import (
    Agent1Output, Agent2Output, Agent3Output,
    ContentGap, CustomerSegment, KeywordOpportunity, Opportunity,
)


def _agent1() -> Agent1Output:
    return Agent1Output(
        business_name="Basil Ford of Niagara Falls",
        location="Niagara Falls, ON",
        customer_segments=[
            CustomerSegment(name="Local commuters", pain_points=["trade-in value transparency"], faqs=["How is my trade-in value calculated?"])
        ],
        key_insights=["New vehicle sales make up 45% of revenue"],
        recommended_channels=["Google Ads"],
    )


def _agent2() -> Agent2Output:
    return Agent2Output(
        site_summary={"basilford_com": "covers new/used inventory"},
        keyword_opportunities=[
            KeywordOpportunity(term="used cars niagara falls", volume=1900, difficulty=44, relevance="underrepresented")
        ],
        competitor_weaknesses=["low domain authority"],
        observed_content_gaps=["no EV FAQ"],
    )


def _agent3_with_one_fabricated_claim() -> Agent3Output:
    return Agent3Output(
        unanswered_buyer_questions=["Does Basil Ford offer EV charging installation?"],
        content_gaps=[
            ContentGap(gap="No EV FAQ", site="basilford.com", severity="medium", evidence="trade-in value transparency was a commuter pain point"),
            ContentGap(gap="Fabricated gap", site="basilford.com", severity="high", evidence="completely made up statistic with no source"),
        ],
        opportunity_prioritization=[
            Opportunity(rank=1, recommendation="Add EV FAQ", rationale="used cars niagara falls is underrepresented", effort="low"),
        ],
    )


@patch("confluence_iq.agents.content_strategist.call_llm")
@patch("confluence_iq.agents.competitor_analyst.call_llm")
@patch("confluence_iq.agents.data_synthesizer.call_llm")
def test_full_pipeline_runs_and_strips_fabricated_claim(mock_ds_llm, mock_ca_llm, mock_cs_llm, tmp_path, monkeypatch):
    import confluence_iq.report.markdown_report as mr
    monkeypatch.setattr(mr, "OUTPUT_DIR", tmp_path)

    mock_ds_llm.return_value = (_agent1(), "thinking 1")
    mock_ca_llm.return_value = (_agent2(), "thinking 2")
    mock_cs_llm.return_value = (_agent3_with_one_fabricated_claim(), "thinking 3")

    graph = build_graph()
    final_state = graph.invoke({})

    assert final_state["report_path"]
    assert len(final_state["flagged_claims"]) == 1
    assert "Fabricated gap" in final_state["flagged_claims"][0]

    report_text = mr.pathlib.Path(final_state["report_path"]).read_text(encoding="utf-8")
    assert "No EV FAQ" in report_text
    assert "Fabricated gap" not in report_text.split("⚠ Flagged Claims")[0]
    assert "⚠ Flagged Claims" in report_text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd confluence-iq-agents && python -m pytest tests/test_graph_integration.py -v`
Expected: FAIL — `KeyError: 'flagged_claims'` (the graph doesn't have a verify node yet).

- [ ] **Step 3: Replace `graph.py`**

```python
"""LangGraph StateGraph — wires the 3 agent nodes + verifier + report writer, with logging."""

import logging
from typing import Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from .agents.competitor_analyst import CompetitorAnalystAgent
from .agents.content_strategist import ContentStrategistAgent
from .agents.data_synthesizer import DataSynthesizerAgent
from .report.markdown_report import write_report
from .schemas import Agent1Output, Agent2Output, Agent3Output
from .tools.loaders import load_raw_corpus_text
from .verifier import verify_agent3_output

logger = logging.getLogger("confluence_iq.graph")


class AgentState(TypedDict):
    agent1_output: Optional[dict]
    agent2_output: Optional[dict]
    agent3_output: Optional[dict]
    flagged_claims: Optional[list]
    report_path: Optional[str]


def verify_node(state: AgentState) -> dict:
    logger.info("=== Verifier ===")
    agent3_output = Agent3Output(**state["agent3_output"])
    corpus = load_raw_corpus_text()
    cleaned, flagged = verify_agent3_output(
        agent3_output, state["agent1_output"], state["agent2_output"], corpus
    )
    if flagged:
        for item in flagged:
            logger.warning("  Flagged: %s", item)
        logger.info("Verifier stripped %d unsourced claim(s).", len(flagged))
    else:
        logger.info("All claims verified against source data.")
    return {"agent3_output": cleaned.model_dump(), "flagged_claims": flagged}


def report_node(state: AgentState) -> dict:
    logger.info("=== Report Writer ===")
    agent1 = Agent1Output(**state["agent1_output"])
    agent2 = Agent2Output(**state["agent2_output"])
    agent3 = Agent3Output(**state["agent3_output"])
    path = write_report(agent1, agent2, agent3, state.get("flagged_claims") or [])
    logger.info("Report written to %s", path)
    return {"report_path": path}


def build_graph() -> StateGraph:
    builder = StateGraph(AgentState)

    builder.add_node("data_synthesizer", DataSynthesizerAgent.run)
    builder.add_node("competitor_analyst", CompetitorAnalystAgent.run)
    builder.add_node("content_strategist", ContentStrategistAgent.run)
    builder.add_node("verify", verify_node)
    builder.add_node("report_writer", report_node)

    builder.add_edge(START, "data_synthesizer")
    builder.add_edge(START, "competitor_analyst")   # parallel with agent 1
    builder.add_edge("data_synthesizer", "content_strategist")
    builder.add_edge("competitor_analyst", "content_strategist")
    builder.add_edge("content_strategist", "verify")
    builder.add_edge("verify", "report_writer")
    builder.add_edge("report_writer", END)

    return builder.compile()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd confluence-iq-agents && python -m pytest tests/test_graph_integration.py -v`
Expected: 1 passed.

- [ ] **Step 5: Run the full test suite**

Run: `cd confluence-iq-agents && python -m pytest tests/ -v`
Expected: all tests across all files pass.

- [ ] **Step 6: Verify the real end-to-end pipeline against the live endpoint**

Run: `cd confluence-iq-agents && python run.py`
Expected: completes without error, prints `Report written to output/report_<timestamp>.md`; `output/transcript.log` contains all 5 nodes' log lines including each agent's `thinking` at DEBUG level. Open the generated report and confirm it has all required sections with real (non-placeholder) content.

- [ ] **Step 7: Commit**

```bash
git add src/confluence_iq/graph.py tests/test_graph_integration.py
git commit -m "feat: wire verify + report_writer nodes; Agent 3 now provably consumes Agent 1/2 context"
```

---

### Task 13: Fix the scraper's dead fallback-function bug

**Files:**
- Modify: `confluence-iq-agents/scripts/scrape_basil_ford.py`
- Create: `confluence-iq-agents/scripts/__init__.py`
- Test: `confluence-iq-agents/tests/test_scrape_basil_ford.py`

**Interfaces:**
- Produces: `_scrape_site(site_key: str, site: dict, target_dir: pathlib.Path) -> tuple[int, int]` (returns `(live_count, skipped_count)`) — a new, independently testable extraction of the per-site scrape loop that previously lived inline in `scrape()`.
- Fixes: `_generate_fallback()` was commented out but still called at the original line `content = _generate_fallback(site_key, site, slug)`, which raises `NameError` the moment any page fails all 3 fetch backends. The fix removes the dead reference entirely rather than restoring fabricated fallback content — inventing placeholder dealership copy and feeding it downstream as if it were real site content would itself be a hallucination risk for Agent 2's analysis.

- [ ] **Step 1: Write the failing test**

Create `confluence-iq-agents/scripts/__init__.py` (empty file).

Create `confluence-iq-agents/tests/test_scrape_basil_ford.py`:

```python
"""Tests for the pre-scrape script's per-site loop and blocked-page handling."""

from unittest.mock import patch

from scripts.scrape_basil_ford import _scrape_site


@patch("scripts.scrape_basil_ford._write_page")
@patch("scripts.scrape_basil_ford._scrape_page")
def test_scrape_site_skips_blocked_pages_without_crashing(mock_scrape_page, mock_write_page, tmp_path):
    # First page blocked (returns None), remaining 8 succeed.
    mock_scrape_page.side_effect = [None] + ["page text"] * 8

    site = {"base_url": "https://example.com", "label": "Example", "location": "Test City"}
    live_count, skipped_count = _scrape_site("example_com", site, tmp_path)

    assert skipped_count == 1
    assert live_count == 8
    assert mock_write_page.call_count == 8
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd confluence-iq-agents && python -m pytest tests/test_scrape_basil_ford.py -v`
Expected: FAIL — `ImportError: cannot import name '_scrape_site'` (doesn't exist yet).

- [ ] **Step 3: Fix `scrape_basil_ford.py`**

Delete the dead commented-out block (find and remove these lines entirely):

```python
# ── Generate fallback page when site is blocked ───────────────────────────────


# def _generate_fallback(_site_key: str, site: dict, slug: str) -> str:
 #   """Return pre-written realistic dealership page content for *slug*."""
  #  pages = FALLBACK_PAGES.get(slug, {})
   # if _site_key in pages:
    #    return pages[_site_key]

    # Generic fallback for any undiscovered page path
   # base = site["base_url"]
    #return f"""{slug.replace('-', ' ').title()} — {site['label']}

# Visit {base} for more information about this page.
# {site['label']} is a Ford dealership serving the {site['location']} area.
# Contact the dealership directly for details about {slug.replace('-', ' ')}.
#""" 
```

Replace the `scrape()` function's body (everything from `total_live = 0` through the final `print(f"{'='*60}\n")`) with:

```python
def _scrape_site(site_key: str, site: dict, target_dir: pathlib.Path) -> tuple[int, int]:
    """Scrape every page for one site; return (live_count, skipped_count)."""
    target_dir.mkdir(parents=True, exist_ok=True)
    live_count = 0
    skipped_count = 0

    for slug, path in PAGE_PATHS:
        content = _scrape_page(site_key, site, slug, path)
        if content is None:
            print(f"    SKIPPED (blocked): {slug}")
            skipped_count += 1
            continue

        live_count += 1
        _write_page(target_dir, slug, content)

    return live_count, skipped_count


def scrape() -> None:
    print(f"Basil Ford Pre-Scrape Tool — {datetime.now():%Y-%m-%d %H:%M}")
    print(f"Output directory: {DATA_DIR}")

    backends = []
    if _check_playwright():
        backends.append("Playwright (Chromium)")
    try:
        import cloudscraper  # noqa: F401

        backends.append("cloudscraper")
    except ImportError:
        pass
    try:
        import requests  # noqa: F401

        backends.append("requests")
    except ImportError:
        pass
    print(f"Available backends: {', '.join(backends)}\n")

    total_live = 0
    total_skipped = 0
    total_pages = len(PAGE_PATHS) * len(SITES)

    for site_key, site in SITES.items():
        target_dir = DATA_DIR / site_key
        label = site["label"]
        print(f"\n{'='*60}")
        print(f"  {label}  ({site['location']})")
        print(f"{'='*60}")

        live_count, skipped_count = _scrape_site(site_key, site, target_dir)

        print(f"\n  {label}: {live_count} live, {skipped_count} skipped")
        total_live += live_count
        total_skipped += skipped_count

    print(f"\n{'='*60}")
    print(f"  Done — {total_live} live, {total_skipped} skipped of {total_pages} total")
    print(f"  Output: {DATA_DIR}")
    print(f"{'='*60}\n")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd confluence-iq-agents && python -m pytest tests/test_scrape_basil_ford.py -v`
Expected: 1 passed.

- [ ] **Step 5: Run the full test suite to confirm no regressions**

Run: `cd confluence-iq-agents && python -m pytest tests/ -v`
Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add scripts/scrape_basil_ford.py scripts/__init__.py tests/test_scrape_basil_ford.py
git commit -m "fix: remove dead _generate_fallback reference; skip blocked pages instead of crashing"
```

---

### Task 14: Update repo docs to point at the finalized design

**Files:**
- Modify: `confluence-iq-agents/docs/architecture.md`
- Modify: `confluence-iq-agents/docs/implementation-plan.md`

**Interfaces:** None — documentation only, no code interfaces.

- [ ] **Step 1: Mark the old plan as superseded**

At the very top of `confluence-iq-agents/docs/implementation-plan.md`, add:

```markdown
> **Superseded** — see `../../documentation/2026-07-13-confluence-iq-methodology-design.md` and `../../documentation/2026-07-13-confluence-iq-implementation-plan.md` at the repo root for the finalized, executed design. This file is kept for historical context only.

```

(Keep the rest of the file's existing content unchanged below this notice.)

- [ ] **Step 2: Update the architecture diagram**

At the very top of `confluence-iq-agents/docs/architecture.md`, add:

```markdown
> **Note:** this diagram predates the `verify` and `report_writer` nodes added in the finalized implementation. See `../../documentation/2026-07-13-confluence-iq-methodology-design.md` for the current 7-node architecture (data_synthesizer + competitor_analyst → verify_agent1 + verify_agent2 → content_strategist → verify → report_writer).

```

- [ ] **Step 3: Commit**

```bash
git add docs/architecture.md docs/implementation-plan.md
git commit -m "docs: point old architecture/plan docs at the finalized methodology"
```

---

### Task 15 (bonus, non-blocking): SKILL.md wrapper

**Files:**
- Create: `confluence-iq-agents/.claude/skills/confluence-iq-agents/SKILL.md`

**Interfaces:** None — this wraps the existing `python run.py` entrypoint for convenience inside Claude Code / OpenCode. Do not start this task until Tasks 1–14 are complete and verified; it is portfolio polish, not part of the graded pipeline.

- [ ] **Step 1: Create the skill wrapper**

Create `confluence-iq-agents/.claude/skills/confluence-iq-agents/SKILL.md`:

```markdown
---
name: confluence-iq-agents
description: Run the Confluence IQ Agents multi-agent market intelligence pipeline for Basil Ford dealerships and summarize the resulting report. Use when asked to run, trigger, or check the Confluence IQ pipeline, or to interpret its output/report/transcript.
---

# Confluence IQ Agents

Thin wrapper around the standalone pipeline in `confluence-iq-agents/`. This skill does not reimplement any agent logic — it documents how to trigger the real pipeline (which calls the internal `api.iamtzar.com` endpoint, model `qwen3.5:397b-cloud`) and how to read its output.

## Running the pipeline

```bash
cd confluence-iq-agents
python run.py
```

This is the single command that triggers all 3 agents (Data Synthesizer, Competitor Analyst, Content Strategist), the deterministic verifier, and the report writer. No arguments — it always produces one holistic report from the full mock dataset.

## Reading the output

- `output/report_<timestamp>.md` — the final Markdown report: Executive Summary, Customer Insights, Competitive Landscape, Unanswered Buyer Questions, Content Gap Analysis, Opportunity Prioritization, and (if the verifier caught anything) a Flagged Claims section.
- `output/transcript.log` — full DEBUG-level record of every agent's inputs, outputs, and model reasoning (`thinking` field), plus the verifier's pass/flag decisions. Use this to explain "how does it work" or to debug an unexpected report.

## Interpreting results for the user

When asked to summarize a run: report the counts (segments, keyword opportunities, content gaps, opportunities) from the Executive Summary line, call out anything in the Flagged Claims section explicitly (it means the verifier caught and stripped an unsourced claim — this is expected, working behavior, not a bug), and point to the specific report file path.
```

- [ ] **Step 2: Verify the skill file is discoverable**

Run: `ls confluence-iq-agents/.claude/skills/confluence-iq-agents/SKILL.md`
Expected: file exists at that path (project-local convention, matches the `dealer-site-seo-extract` pattern).

- [ ] **Step 3: Commit**

```bash
git add confluence-iq-agents/.claude/skills/
git commit -m "docs: add SKILL.md wrapper for the confluence-iq-agents pipeline"
```

---

## Final verification checklist

- [ ] `cd confluence-iq-agents && python -m pytest tests/ -v` — all tests pass.
- [ ] `cd confluence-iq-agents && python run.py` — single command, completes without error.
- [ ] `output/report_*.md` contains: Unanswered Buyer Questions, Content Gap Analysis, Opportunity Prioritization sections with real (non-placeholder) content.
- [ ] `output/transcript.log` shows each agent logging what it received and produced — visible evidence of context passing.
- [ ] Manually inject one fabricated claim (temporarily edit `content_strategist.py`'s prompt to ask for a fake statistic, or run the graph integration test) and confirm the verifier catches and flags it — proves "No Hallucinations" is enforced, not just claimed.
