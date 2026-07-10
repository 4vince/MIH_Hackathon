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
