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
