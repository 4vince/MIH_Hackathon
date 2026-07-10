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

---

## Files to modify (in order)

| # | File | What changes |
|---|------|-------------|
| 1 | `requirements.txt` | Add `langchain-openai` (and optionally `langchain-anthropic`) for LLM calls via LangChain's `ChatOpenAI` / `with_structured_output()` |
| 2 | `src/confluence_iq/schemas.py` | Enrich all 3 agent output schemas to match acceptance criteria |
| 3 | `src/confluence_iq/config.py` | Add an `llm()` factory function that returns a LangChain chat model from `.env` config |
| 4 | `src/confluence_iq/prompts/data_synthesizer.md` | Rewrite with specific extraction instructions + output format mapping |
| 5 | `src/confluence_iq/prompts/competitor_analyst.md` | Same — focused on SEO + site text analysis |
| 6 | `src/confluence_iq/prompts/content_strategist.md` | Same — focused on gap analysis + prioritization |
| 7 | `src/confluence_iq/agents/data_synthesizer.py` | Real LLM call: load prompt + data → call structured LLM → validate → return |
| 8 | `src/confluence_iq/agents/competitor_analyst.py` | Same pattern, loads SEO trends + site texts |
| 9 | `src/confluence_iq/agents/content_strategist.py` | Same pattern, takes Agent1 + Agent2 outputs as context |
| 10 | `src/confluence_iq/graph.py` | Add logging/print statements so agent passing is visible at runtime |
| 11 | `src/confluence_iq/report/markdown_report.py` | Update to render new schema fields (gaps, questions, priorities) |
| 12 | `tests/test_data_synthesizer.py` | Update assertions — test schema validity, not hardcoded values |
| 13 | `tests/test_competitor_analyst.py` | Same |
| 14 | `tests/test_content_strategist.py` | Same |
| 15 | `docs/architecture.md` | Minor update if graph changes (e.g. logging additions) |

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

### Step 3: Add LLM factory
**File:** `config.py`

Add an `llm()` function:
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
    # fallback
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

### Step 5: Implement agents with LLM calls
**Files:** `agents/data_synthesizer.py`, `competitor_analyst.py`, `content_strategist.py`

Each agent follows the same pattern:

```python
class DataSynthesizerAgent:
    @staticmethod
    def run(state: dict) -> dict:
        print("\n" + "="*60)
        print("  Agent 1: Data Synthesizer — analysing customer data...")
        print("="*60)

        # 1. Load data
        data = load_customer_data()

        # 2. Load system prompt
        prompt_path = HERE.parent / "prompts" / "data_synthesizer.md"
        system_prompt = prompt_path.read_text()

        # 3. Build full prompt with data injected
        user_prompt = f"Here is the customer data:\n{json.dumps(data, indent=2)}\n\nOutput JSON matching this schema:\n{Agent1Output.model_json_schema()}"

        # 4. Call LLM with structured output
        chat = llm()
        structured_llm = chat.with_structured_output(Agent1Output)
        output = structured_llm.invoke([
            SystemMessage(system_prompt),
            HumanMessage(user_prompt),
        ])

        # 5. Print reasoning (visible communication)
        print(f"  → Found {len(output.customer_segments)} customer segments")
        print(f"  → Top pain points: {[p for s in output.customer_segments for p in s.pain_points][:3]}")
        print(f"  → Key insights: {len(output.key_insights)} identified")

        return {"agent1_output": output.model_dump()}
```

The `competitor_analyst.py` additionally loads site texts via `load_site_texts()` and the agent 3 receives `agent1_output` and `agent2_output` from state.

### Step 6: Visible agent communication in graph
**File:** `graph.py`

Wrap each node call with stdout logging that makes agent passing visible:

```
→ Agent 1 (Data Synthesizer) started...
  [Agent 1 output printed here]
  → Agent 1 complete. Passing customer insights to Agent 3.

→ Agent 2 (Competitor Analyst) started...
  [Agent 2 output printed here]
  → Agent 2 complete. Passing competitive analysis to Agent 3.

→ Agent 3 (Content Strategist) started...
  Reads Agent 1's findings: [summary]
  Reads Agent 2's findings: [summary]
  Comparing customer needs vs. existing site content...
  [Agent 3 output printed here]
  → Agent 3 complete. Writing report...

✓ Report written to output/report_20260710_143022.md
```

The agents themselves print their reasoning (step 5). The graph prints the orchestration flow. Together they satisfy the "visibly show agents talking" criterion.

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

Switch from hardcoded-value assertions to schema-validity checks (since LLM output varies):

```python
def test_run_returns_agent1_output():
    result = DataSynthesizerAgent.run({})
    output = Agent1Output(**result["agent1_output"])
    assert len(output.customer_segments) > 0
    assert all(s.name for s in output.customer_segments)
```

---

## Verification

After implementation, verify end-to-end:

```bash
cd confluence-iq-agents

# 1. Tests pass
pip install -e .
pytest tests/ -v

# 2. Full pipeline runs
python run.py

# 3. Report has all required sections
cat output/report_*.md | grep -E "(Unanswered buyer questions|Content gap|Opportunity prioritization)"

# 4. Check visible agent communication in stdout — should show agents
#    printing findings and passing context between each other
```

---

## Key design decisions

1. **LangChain `with_structured_output()`** — maps Pydantic schemas directly to LLM output without manual JSON parsing. Judges see industry-standard tooling.

2. **Prompt files stay as .md** — keep them separate from code for easy iteration. Agents read + inject data at runtime.

3. **No-hallucination via prompt engineering** — every system prompt ends with "Use ONLY the data below. Do not add external knowledge." The structured output parsing enforces schema compliance.

4. **Logging is in the agents, not a separate logger** — keeps visible communication co-located with the logic. The graph provides the orchestration frame.
