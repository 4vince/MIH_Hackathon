# Confluence IQ Agents — Finalized Methodology (Design)

**Status:** Approved 2026-07-11. Supersedes the draft methodology notes and reconciles them with the official PRD (`mih_hackathon_guide_PRDs.md`) and the `api.iamtzar.com` endpoint's confirmed contract.

**Goal:** Turn the existing `confluence-iq-agents` skeleton (LangGraph wiring + stub agents) into a working submission for Challenge 2 — The Multi-Agent Orchestra — that passes all three acceptance criteria in the PRD.

## Global constraints (from the PRD)

- Single command trigger: `python run.py`.
- Agents must visibly show they're "talking" / passing context — not just internally, but observably during a live demo.
- Final output is a Markdown report containing: unanswered buyer questions, a specific content gap analysis for Basil Ford, and opportunity prioritization.
- No hallucinations — findings must trace to the provided context/files only, enforced by a deterministic (non-LLM) check.
- Use the internal LLM endpoint `https://api.iamtzar.com/` — no personal/external API keys.
- Out of scope: building a database from scratch (static JSON is fine), live scraping during the demo (pre-scraped `.txt` files only — already done).

## Decisions locked in this session

| Question | Decision | Why |
|---|---|---|
| Orchestration framework | Keep LangGraph `StateGraph` | Official PRD lists agentic frameworks (incl. LangChain) as Challenge 2's focus area, contradicting the earlier draft methodology's ban. Least rework — `graph.py` already exists and its parallel edges naturally model Agent 1 / Agent 2 running independently. |
| LLM call method | Plain `httpx`, not a LangChain chat-model wrapper | Avoids depending on `api.iamtzar.com` matching LangChain's exact expected schema. Confirmed compatible with Ollama's native API (see below). |
| Verifier design | Claim-level fact-checking (fuzzy-match extracted claims against source data), not simple field-presence | Directly targets the "No Hallucinations" criterion — field-presence only catches missing structure, not wrong content. |
| Verifier failure mode | Strip unsourced claims + flag inline in the report; pipeline always completes | Never risk producing *no report* live in front of judges. Showing a caught/flagged claim is a stronger demo beat than silently succeeding — it proves the guarantee is enforced, not just claimed. |
| Pipeline mode | Holistic report, no question argument (`python run.py`, no args) | Matches the PRD's Agent 1/2/3 scope description (no per-question mode mentioned). Simpler to demo reliably under time pressure. |
| Reusable skill wrapper | Bonus, thin `SKILL.md` wrapper around the existing `python run.py` — not a replacement for it | A `SKILL.md` is instructions Claude Code itself executes — using it as the actual "3 agents" would mean Claude/Anthropic runs the analysis instead of the mandated internal endpoint (`api.iamtzar.com` / `qwen3.5:397b-cloud`), directly violating the PRD. Kept as portfolio polish only, matching the `dealer-site-seo-extract` skill pattern from the Agentic-Skill-for-LLMs repo. Ships after the core pipeline works. |

## `api.iamtzar.com` — confirmed contract (verified 2026-07-11 via manual curl/Invoke-RestMethod testing)

- Backend: **Ollama**, reverse-proxied via Cloudflare. Root (`GET /`) returns `Ollama is running`.
- **No authentication required.**
- Model list: `GET /api/tags` → `{"models":[{"name":"qwen3.5:397b-cloud", ...}, ...]}`. Confirmed `qwen3.5:397b-cloud` is present and exactly matches the PRD's model name.
- Chat route: `POST /api/chat`
  - Request: `{"model": "qwen3.5:397b-cloud", "messages": [{"role": "user", "content": "..."}], "stream": false}`
    - `"stream": false` is required — without it, Ollama returns newline-delimited JSON chunks instead of one object.
  - Response (native Ollama shape, **not** OpenAI-style):
    ```json
    {
      "model": "qwen3.5:397b",
      "created_at": "...",
      "message": {"role": "assistant", "content": "OK", "thinking": "..."},
      "done": true,
      "done_reason": "stop",
      "total_duration": ...,
      "prompt_eval_count": ...,
      "eval_count": ...
    }
    ```
  - Answer text is at `response["message"]["content"]`.
  - This is a **thinking model** — `response["message"]["thinking"]` contains the model's chain-of-thought separately from the final answer. This can be logged to `transcript.log` as extra evidence of agent reasoning (bonus for the "visible agent communication" criterion), but only `content` is used as the actual structured output.
- **Structured output:** Ollama's native `/api/chat` supports a `format` field accepting a JSON schema, which constrains the model's output to match it. Each agent will pass `AgentNOutput.model_json_schema()` as `format`, removing the need for manual JSON parsing/retry logic or a LangChain structured-output wrapper.

## Architecture

```
python run.py
      │
      ▼
┌─────────────┐
│ StateGraph   │  (LangGraph — unchanged shape from today)
└──────┬───────┘
       │
   ┌───┴────────────┐
   ▼                ▼
Agent 1          Agent 2         ← parallel (existing edges)
Data             Competitor
Synthesizer      Analyst
   │                │
   └───────┬────────┘
           ▼
       Agent 3
       Content Strategist
       (reads state["agent1_output"] / state["agent2_output"] — currently broken, must be fixed)
           ▼
       Verifier (deterministic, no LLM)
       — extracts claims (ContentGap.evidence, Opportunity.rationale) from Agent 3's draft
       — fuzzy-matches each against source corpus (Agent1/2 output + raw JSON/text files)
       — strips unsourced claims, collects them as flagged_claims
           ▼
       Report Writer
       — writes output/report_<timestamp>.md
       — includes "⚠ Flagged Claims (Unverified)" section only if verifier caught something
           ▼
   output/report_<timestamp>.md + output/transcript.log
```

Each of the 3 agent nodes calls the LLM via a shared `call_llm(system_prompt, user_content, model, output_schema)` helper built on plain `httpx`, hitting `POST https://api.iamtzar.com/api/chat`, model `qwen3.5:397b-cloud` for all three agents (per the PRD's model table — best general-quality model available; Agent 3 is the judged deliverable, so it isn't downgraded for latency).

**Considered and rejected:** `tzar:3.5` (a local 4.3B Gemma3-based fine-tune, PRD-labeled "Custom TzarAI Voice") as a swap-in for all three agents. Rejected because it's ~90x smaller than `qwen3.5:397b-cloud` with real quality risk for the judged content-gap/prioritization reasoning, and the reliability concern that motivated considering it (external cloud round-trip for `qwen3.5:397b-cloud`) wasn't observed in practice — a live test against it succeeded in ~1.2s. Reserved as a documented fallback only if real rate-limiting/latency problems surface during Saturday/Sunday build.

## Schemas

```python
class CustomerSegment(BaseModel):
    name: str
    pain_points: list[str]
    faqs: list[str]

class Agent1Output(BaseModel):
    business_name: str
    location: str
    customer_segments: list[CustomerSegment]
    key_insights: list[str]
    recommended_channels: list[str]

class KeywordOpportunity(BaseModel):
    term: str
    volume: int
    difficulty: int
    relevance: str

class Agent2Output(BaseModel):
    site_summary: dict[str, str]          # {domain: summary}
    keyword_opportunities: list[KeywordOpportunity]
    competitor_weaknesses: list[str]
    observed_content_gaps: list[str]

class ContentGap(BaseModel):
    gap: str
    site: str
    severity: str
    evidence: str                          # must trace to Agent1/Agent2 output or source data

class Opportunity(BaseModel):
    rank: int
    recommendation: str
    rationale: str                         # must trace to Agent1/Agent2 output or source data
    effort: str

class Agent3Output(BaseModel):
    unanswered_buyer_questions: list[str]
    content_gaps: list[ContentGap]
    opportunity_prioritization: list[Opportunity]
```

## Logging strategy

Dual-output Python `logging`, hierarchical loggers per agent (`confluence_iq.agent1`, `.agent2`, `.agent3`, `.verifier`):

- **Console handler (INFO+)** — real-time narration during the live demo: what each agent read, what it's calling the LLM with, what it produced, and the verifier's pass/flag summary.
- **File handler (DEBUG+)**, `output/transcript.log` — full record including raw prompts/responses and the model's `thinking` field, for judges who ask "how does it work" during Q&A.

## Verifier — claim-level fact-checking

1. Build one combined source corpus: `Agent1Output` + `Agent2Output` (serialized) + raw `mock_customer_data.json` + `mock_seo_trends.json` + all `site_text/*.txt`.
2. For each `ContentGap.evidence` and `Opportunity.rationale` string, fuzzy-match against that corpus (`difflib.SequenceMatcher` or keyword-overlap, deterministic — no LLM call).
3. Anything below the match threshold is stripped from the report body and collected into `flagged_claims: list[str]`.
4. Pipeline always completes; the report includes a `## ⚠ Flagged Claims (Unverified)` section only when something was caught.

## Report structure

```markdown
# Confluence IQ Market Intelligence Report — Basil Ford

## Executive Summary
## Customer Insights (Agent 1)
## Competitive Landscape (Agent 2)
## Unanswered Buyer Questions
## Content Gap Analysis
| Gap | Site | Severity | Evidence |
## Opportunity Prioritization
| Rank | Recommendation | Rationale | Effort |
## ⚠ Flagged Claims (Unverified)   ← only appears if verifier caught something
```

## Testing

Tests switch from hardcoded-value assertions to schema-validity + verifier-behavior assertions:
- Each agent test validates the returned dict against its Pydantic schema (not exact hardcoded values, since LLM output varies).
- A new verifier test feeds a known-fabricated claim (not present in any source file) and asserts it gets flagged and stripped.
- A clean, fully-sourced draft produces zero flags.

## Bonus (non-blocking): SKILL.md wrapper

`confluence-iq-agents/.claude/skills/confluence-iq-agents/SKILL.md` — documents how to trigger `python run.py` and interpret `output/report_*.md` / `output/transcript.log` conversationally through Claude Code. Matches the `dealer-site-seo-extract` skill's project-local install convention (`.claude/skills/<name>/`). Built only after the core pipeline passes all three acceptance criteria — it wraps the existing entrypoint, it does not reimplement any agent logic.

## Out of scope for this design

- Query-driven pipeline mode (`python run.py "<question>"`) — explicitly deferred in favor of the holistic no-argument mode.
- Vector DB / RAG (belongs to Challenge 1, not attempted here).
- Dashboard / RBAC (belongs to Challenge 3, not attempted here).
