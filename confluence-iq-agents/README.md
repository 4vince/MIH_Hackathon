# Confluence IQ Agents

Multi-agent system that synthesises customer data, competitor SEO intelligence, and content strategy into a structured marketing report.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate      # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env           # fill in your LLM API key
```

## How to run

```bash
python run.py
```

Output lands in `output/report_<timestamp>.md`.

## Project structure

See [docs/architecture.md](docs/architecture.md) for the full diagram and rationale.
