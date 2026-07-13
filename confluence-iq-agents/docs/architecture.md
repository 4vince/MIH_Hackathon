> **Note:** this diagram predates the `verify_agent1`, `verify_agent2`, `verify`, and `report_writer` nodes added in the finalized implementation. See `../../documentation/2026-07-13-confluence-iq-methodology-design.md` for the current 7-node architecture (data_synthesizer + competitor_analyst → verify_agent1 + verify_agent2 → content_strategist → verify → report_writer).

# Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        run.py (entrypoint)                       │
│          python run.py  ───→  build_graph().invoke({})          │
└───────────────────────────┬──────────────────────────────────────┘
                            │
                    ┌───────┴────────┐
                    │   StateGraph   │
                    │  (LangGraph)   │
                    └───────┬────────┘
                            │
              ┌─────────────┼──────────────┐
              ▼             ▼              │
     ┌────────────────┐ ┌────────────────┐ │
     │  Agent 1       │ │  Agent 2       │ │   ← run in parallel
     │  Data          │ │  Competitor    │ │
     │  Synthesizer   │ │  Analyst       │ │
     └───────┬────────┘ └───────┬────────┘ │
             │                  │          │
             └────────┬─────────┘          │
                      ▼                    │
             ┌────────────────┐            │
             │  Agent 3       │◄───────────┘
             │  Content       │
             │  Strategist    │
             └───────┬────────┘
                     ▼
             ┌────────────────┐
             │  markdown_     │
             │  report.py     │
             └───────┬────────┘
                     ▼
             output/report_<timestamp>.md
```

## Rationale

- **Parallel agents 1 & 2** — customer data and SEO intel are independent;
  no reason to serialise them.
- **LangGraph StateGraph** — gives us built-in state passing, parallel edges,
  and a single `invoke()` call from the entrypoint.
- **Pydantic schemas** — every agent's output is validated, making the graph
  type-safe and testable without a running LLM.
- **Markdown report** — keeps the deliverable human-readable and git-friendly.
