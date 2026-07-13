> **Superseded** — see `../../documentation/2026-07-13-confluence-iq-methodology-design.md` and `../../documentation/2026-07-13-confluence-iq-implementation-plan.md` at the repo root for the finalized, executed design. This file is kept for historical context only.

# Plan: Confluence IQ Agents — Multi-Agent Orchestra (Challenge 2)

## Context

The project skeleton exists (structure, scraped data, LangGraph graph wiring, Pydantic schemas) but **agents return hardcoded data** — there is no real LLM integration, no visible agent communication, and the output schemas don't match the acceptance criteria. The challenge requires:

1. **Single-command trigger** — `python run.py` starts everything (already works)
2. **Visible agent communication** — agents must appear to "talk" or pass context
3. **Final Markdown report** containing:
   - Unanswered buyer questions
   - Specific content gap analysis for Basil Ford
   - Opportunity prioritization (what to create first)
4. **No hallucinations** — grounded only in provided data files

## Methodology

Three documented patterns from Anthropic's **"Building Effective Agents"** (Dec 2024):

1. **Parallelization (sectioning)** — Agent 1 (Data Synthesizer) and Agent 2 (Competitor Analyst) read independent, non-overlapping data sources and run concurrently. Neither needs the other's output. This is not an optimisation; it's a correctness property — they are genuinely independent analyses.

2. **Prompt chaining** — Agent 3 (Content Strategist) consumes both prior outputs as a serial next step. This is the "aggregation" half of the pattern. Each agent's output is a complete, validated structure before the next begins.

3. **Rule-based verification** — A deterministic check (schema compliance, field presence, length thresholds) before the report is considered final. This is **not** a second LLM pass grading the first — it's a hard check at the graph level.

These are not ad hoc shortcuts — they are documented practices for well-defined multi-step tasks. The architecture should name them explicitly.

**Logging** — Python `logging` module with dual output:
- Console handler (`INFO`+) — real-time agent communication
- File handler (`DEBUG`+) — `output/transcript.log`, permanent record for judges
This is the mechanism for the "agents visibly passing context" acceptance criterion.

---

## Files to modify (in order)

| # | File | What changes |
|---|------|-------------|
| 1 | `requirements.txt` | Add `langchain-openai` (and optionally `langchain-anthropic`) |
| 2 | `src/confluence_iq/schemas.py` | Enrich all 3 agent output schemas to match acceptance criteria |
| 3 | `src/confluence_iq/config.py` | Add `llm()` factory + `setup_logging()` with dual handlers |
| 4 | `src/confluence_iq/prompts/data_synthesizer.md` | Rewrite with extraction instructions + grounding rule |
| 5 | `src/confluence_iq/prompts/competitor_analyst.md` | Same — SEO + site text focus |
| 6 | `src/confluence_iq/prompts/content_strategist.md` | Same — gap analysis + prioritization focus |
| 7 | `src/confluence_iq/agents/data_synthesizer.py` | Real LLM via `llm().with_structured_output()`, `logger.info()` calls |
| 8 | `src/confluence_iq/agents/competitor_analyst.py` | Same pattern, loads SEO + site texts |
| 9 | `src/confluence_iq/agents/content_strategist.py` | Same pattern, takes Agent1 + Agent2 as context |
| 10 | `src/confluence_iq/graph.py` | `setup_logging()` at build time, logging in every node, verify node |
| 11 | `src/confluence_iq/report/markdown_report.py` | Render new schema fields (gaps, questions, priorities) |
| 12 | `run.py` | Call `setup_logging()` before building graph |
| 13 | `tests/test_data_synthesizer.py` | Schema-validity assertions, not hardcoded values |
| 14 | `tests/test_competitor_analyst.py` | Same |
| 15 | `tests/test_content_strategist.py` | Same |
| 16 | `docs/architecture.md` | Name the three Anthropic patterns + show verify node + logging |

---

## Step-by-step implementation

### Step 1: Update dependencies
**File:** `requirements.txt`

Add `langchain-openai>=0.2` and optionally `langchain-anthropic>=0.2`. Keep everything else.

### Step 2: Enrich Pydantic schemas
**File:** `schemas.py`

Current schemas are too sparse for the acceptance criteria. New design:

```
Agent1Output (Data Synthesizer):
  - business_name: str
  - location: str
  - customer_segments: list[CustomerSegment]  (name, pain_points, questions/faqs)
  - key_insights: list[str]                   (top patterns from the data)
  - recommended_channels: list[str]

Agent2Output (Competitor Analyst):
  - site_summary: str                         (what each site covers)
  - keyword_opportunities: list[Keyword]      (term, volume, difficulty, relevance)
  - competitor_weaknesses: list[str]
  - observed_content_gaps: list[str]          (things missing from site text)

Agent3Output (Content Strategist):
  - unanswered_buyer_questions: list[str]
  - content_gaps: list[ContentGap]            (gap, site, severity, evidence)
  - opportunity_prioritization: list[Opportunity] (rank, recommendation, rationale, effort)
  - report_sections: list[str]                (headings for the markdown report)
```

### Step 3: Add LLM factory + logging setup
**File:** `config.py`

Two new functions:

```python
def llm() -> BaseChatModel:
    """Return a LangChain chat model based on .env config."""
    provider = LLM_PROVIDER
    api_key = LLM_API_KEY
    model = resolve_model()
    if provider == "openai":
        return ChatOpenAI(model=model, api_key=api_key, temperature=0)
    elif provider == "anthropic":
        return ChatAnthropic(model=model, api_key=api_key, temperature=0)
    raise ValueError(f"Unknown LLM_PROVIDER: {provider}")


def setup_logging() -> logging.Logger:
    """Dual-output logger: console (INFO) + output/transcript.log (DEBUG).

    This is the "agents visibly passing context" acceptance criterion.
    Console shows the orchestration flow in real time; transcript.log
    is a permanent record for judges/submission.
    """
    logger = logging.getLogger("confluence_iq")
    logger.setLevel(logging.DEBUG)

    # Console handler — summary level
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(console)

    # File handler — full verbosity
    log_dir = HERE.parent.parent / "output"
    log_dir.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(log_dir / "transcript.log", mode="w")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        "%(asctime)s [%(name)s] %(levelname)s %(message)s"
    ))
    logger.addHandler(fh)

    return logger
```

### Step 4: Rewrite prompts
**Files:** `prompts/*.md`

Each prompt gets:
- A clear role definition
- Detailed instructions on what to extract from the provided data
- Explicit grounding constraint: "Use ONLY the data below. Do not use external knowledge."
- A note that output must be valid JSON matching the schema (the actual schema is injected at runtime by the agent, not in the .md file — the .md describes the fields)

**Key pattern** for `data_synthesizer.md`:
```
You are a marketing-data analyst. Given raw customer data...

Extract the following:
1. Customer segments and their specific pain points
2. Common questions or FAQs each segment would have
3. Key insights from the revenue breakdown and channel mix

GROUNDING RULE: Use ONLY the data below. Do not add external knowledge.
```

**Key pattern** for `competitor_analyst.md`:
```
You are an SEO / competitive-intelligence analyst. Given keyword trends and scraped site text...

Analyze:
1. What content each site currently has (summarise from the page texts)
2. Keyword opportunities where basilford.com is underperforming
3. Competitor weaknesses to exploit
4. Content gaps visible from the site text comparison

GROUNDING RULE: ...
```

**Key pattern** for `content_strategist.md`:
```
You are a senior content strategist. Given the customer insights from Agent 1 and the competitive analysis from Agent 2...

Produce:
1. Unanswered buyer questions — specific questions customers have that neither site answers
2. Content gaps — what content is missing, on which site, and why it matters
3. Prioritised opportunities — ranked by impact and effort, with clear rationale

Every recommendation must trace to evidence in Agent 1 or Agent 2's output.
```

### Step 5: Implement agents with LLM calls + logging
**Files:** `agents/data_synthesizer.py`, `competitor_analyst.py`, `content_strategist.py`

Each agent gets a module-level `logger = logging.getLogger("confluence_iq.agentN")` and uses `logger.info()` instead of `print()`:

```python
import json
import logging
import pathlib

from langchain_core.messages import SystemMessage, HumanMessage

from ..config import llm
from ..schemas import Agent1Output
from ..tools.loaders import load_customer_data

HERE = pathlib.Path(__file__).resolve().parent
logger = logging.getLogger("confluence_iq.agent1")


class DataSynthesizerAgent:

    @staticmethod
    def run(state: dict) -> dict:
        logger.info("═╡ Agent 1: Data Synthesizer ╞" + "═"*40)
        logger.info("Reading customer data...")

        data = load_customer_data()
        prompt = (HERE.parent / "prompts" / "data_synthesizer.md").read_text()

        logger.info("Calling LLM with %d customer segments ...",
                     len(data.get("customer_segments", [])))

        chat = llm()
        structured = chat.with_structured_output(Agent1Output)
        output = structured.invoke([
            SystemMessage(prompt),
            HumanMessage(f"Customer data:\n{json.dumps(data, indent=2)}"),
        ])

        logger.info("Found %d customer segments", len(output.customer_segments))
        for seg in output.customer_segments:
            logger.info("  • %s — pain points: %s",
                        seg.name, ", ".join(seg.pain_points))
        logger.info("Key insights: %d identified", len(output.key_insights))
        logger.info("Agent 1 complete. Passing to Agent 3.")

        return {"agent1_output": output.model_dump()}
```

The `competitor_analyst.py` additionally loads site texts via `load_site_texts()`. The `content_strategist.py` receives `agent1_output` and `agent2_output` from state and logs its comparison reasoning.

### Step 6: Logging + rule-based verification in graph
**File:** `graph.py`, `run.py`

**`run.py`** — initialise logging before the graph:
```python
from confluence_iq.config import setup_logging
from confluence_iq.graph import build_graph

def main():
    logger = setup_logging()
    logger.info("Confluence IQ Agents — starting pipeline")
    graph = build_graph()
    final = graph.invoke({})
    logger.info("Report written to %s", final["report_path"])
```

**`graph.py`** — add a `verify_outputs` node and conditional edge:

```python
import logging

logger = logging.getLogger("confluence_iq.graph")


def verify_outputs(state: AgentState) -> str:
    """Deterministic checks — no LLM involved. Returns "pass" or "fail"."""
    errors = []

    a1 = state.get("agent1_output")
    a2 = state.get("agent2_output")
    a3 = state.get("agent3_output")

    if not a1: errors.append("Missing Agent 1 output")
    elif not a1.get("customer_segments"): errors.append("Agent 1: no segments")

    if not a2: errors.append("Missing Agent 2 output")
    elif not a2.get("keyword_opportunities"): errors.append("Agent 2: no keywords")

    if not a3: errors.append("Missing Agent 3 output")
    else:
        if not a3.get("unanswered_buyer_questions"):
            errors.append("Agent 3: no unanswered buyer questions")
        if not a3.get("content_gaps"):
            errors.append("Agent 3: no content gaps")
        if not a3.get("opportunity_prioritization"):
            errors.append("Agent 3: no opportunity prioritization")

    logger.info("═╡ Rule-based verification ╞" + "═"*40)
    if errors:
        for e in errors:
            logger.error("  ✗ %s", e)
        logger.error("  → Report rejected. Check transcript.log for details.")
        return "fail"

    logger.info("  ✓ All required fields present")
    logger.info("  → Report approved.")
    return "pass"
```

Graph wiring:
```python
builder.add_node("data_synthesizer", DataSynthesizerAgent.run)
builder.add_node("competitor_analyst", CompetitorAnalystAgent.run)
builder.add_node("content_strategist", ContentStrategistAgent.run)
builder.add_node("verify", verify_outputs)
builder.add_node("report_writer", write_report_node)

builder.add_edge(START, "data_synthesizer")
builder.add_edge(START, "competitor_analyst")
builder.add_edge("data_synthesizer", "content_strategist")
builder.add_edge("competitor_analyst", "content_strategist")
builder.add_edge("content_strategist", "verify")

builder.add_conditional_edges(
    "verify",
    lambda s: s["verdict"],  # verify stores "pass"/"fail" in state
    {"pass": "report_writer", "fail": END},
)
builder.add_edge("report_writer", END)
```

### Step 7: Update report writer
**File:** `markdown_report.py`

New report structure:
```markdown
# Confluence IQ Market Intelligence Report

## Executive Summary
...

## 1. Customer Insights (Agent 1)
...

## 2. Competitive Landscape (Agent 2)
...

## 3. Content Gap Analysis (Agent 3)

### Unanswered Buyer Questions
- Question 1
- Question 2

### Content Gaps
| Gap | Site | Severity | Evidence |
|-----|------|----------|----------|

### Opportunity Prioritization
| Rank | Recommendation | Rationale | Effort |
|------|---------------|-----------|--------|
```

### Step 8: Update tests
**Files:** `tests/*.py`

Switch from hardcoded-value assertions to schema-validity checks (LLM output varies):

```python
from confluence_iq.schemas import Agent1Output

def test_run_returns_agent1_output():
    result = DataSynthesizerAgent.run({})
    output = Agent1Output(**result["agent1_output"])
    assert len(output.customer_segments) > 0
    assert all(s.name for s in output.customer_segments)
```

Also add a test for the verification function:
```python
def test_verify_rejects_missing_output():
    from confluence_iq.graph import verify_outputs
    assert verify_outputs({"agent1_output": {}}) == "fail"
```

---

## Verification

```bash
cd confluence-iq-agents

# 1. Tests pass
pip install -e .
pytest tests/ -v

# 2. Full pipeline runs
python run.py

# 3. Report has all required sections
cat output/report_*.md | grep -E "(Unanswered buyer questions|Content gap|Opportunity prioritization)"

# 4. Transcript log captured everything
cat output/transcript.log

# 5. Console output shows agents communicating:
#    ═╡ Agent 1: Data Synthesizer ╞══════════════════════════
#    Reading customer data...
#    Calling LLM with 2 customer segments ...
#    Found 2 customer segments
#      • Local commuters — pain points: trade-in value transparency, service wait times
#      • Tourists / seasonal visitors — pain points: rental vs purchase confusion, short-term financing
#    Agent 1 complete. Passing to Agent 3.
#    ═╡ Agent 2: Competitor Analyst ╞════════════════════════
#    Reading SEO trends + site texts for 2 domains...
#    ...
#    ═╡ Agent 3: Content Strategist ╞════════════════════════
#    Comparing customer needs vs. existing site content...
#    ...
#    ═╡ Rule-based verification ╞════════════════════════════
#      ✓ All required fields present
#    Report written to output/report_20260710_143022.md
```

---

## Key design decisions

1. **LangChain `with_structured_output()`** — maps Pydantic schemas directly to LLM output without manual JSON parsing. Judges see industry-standard tooling.

2. **Prompt files stay as .md** — keep them separate from code for easy iteration. Agents read + inject data at runtime.

3. **No-hallucination via prompt engineering** — every system prompt ends with "Use ONLY the data below. Do not add external knowledge." The structured output parsing enforces schema compliance.

4. **Python logging, not print()** — dual output (console + `transcript.log`) satisfies the "agents visibly passing context" criterion. Console shows real-time orchestration; `transcript.log` is a permanent record for judges. Hierarchical loggers (`confluence_iq.agent1`, etc.) keep the transcript organised.

5. **Rule-based verification is a graph node, not an LLM** — deterministic schema/field checks as a conditional edge. If verification fails, the graph terminates with logged errors but no report. This is the "fail fast" guarantee and the third Anthropic pattern.
