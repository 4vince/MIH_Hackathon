# Confluence IQ Agents

Multi-agent system for the MIH Hackathon that synthesises customer data, competitor SEO intelligence, and scraped site content into a structured marketing report — **no internet access required during the demo**.

## Quick start

```bash
# 1. Install dependencies
python -m venv .venv
source .venv/bin/activate          # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

# 2. Set your LLM API key
cp .env.example .env
# Edit .env — set LLM_API_KEY and optionally LLM_PROVIDER/LLM_MODEL

# 3. Pre-scrape dealership sites (one-time setup) // na run na this one di na need irun ulit
pip install playwright
python -m playwright install chromium
python scripts/scrape_basil_ford.py

# 4. Run the agent pipeline
python run.py
```

Output lands in `output/report_<timestamp>.md`.

## How it works

```
┌─────────────────────────────────────────────────────────────┐
│                     python run.py                           │
│                  builds & invokes graph                     │
└─────────────────────────┬───────────────────────────────────┘
                          │
                ┌─────────┴─────────┐
                │   StateGraph      │
                │   (LangGraph)     │
                └─────────┬─────────┘
                          │
              ┌───────────┼──────────────┐
              ▼           ▼              │
     ┌────────────┐ ┌────────────┐       │
     │  Agent 1   │ │  Agent 2   │       │   ← parallel
     │  Data      │ │  Competitor│       │
     │  Synthesizer│ │  Analyst   │       │
     └─────┬──────┘ └─────┬──────┘       │
           │              │              │
           └──────┬───────┘              │
                  ▼                      │
          ┌──────────────┐               │
          │  Agent 3     │◄──────────────┘
          │  Content     │
          │  Strategist  │
          └──────┬───────┘
                 ▼
          ┌──────────────┐
          │  Markdown    │
          │  Report      │
          └──────┬───────┘
                 ▼
         output/report_<timestamp>.md
```

### Agents

| Agent | Role | Reads |
|---|---|---|
| **1 — Data Synthesizer** | Ground customer data into structured insights | `data/mock_customer_data.json` |
| **2 — Competitor Analyst** | Analyse SEO trends and scraped site content | `data/mock_seo_trends.json`, `data/site_text/` |
| **3 — Content Strategist** | Synthesise agents 1 & 2 into a final report | Output of agents 1 & 2 (state) |

### Reliability guarantee

The scraper (`scripts/scrape_basil_ford.py`) is a **one-time setup step** — run it ahead of the hackathon, and the scraped text files are committed as static input. During the demo, the agent pipeline reads only local files; no HTTP requests are made.

## Data sources

| File | Description |
|---|---|
| `data/mock_customer_data.json` | Synthetic customer segments, pain points, channel mix |
| `data/mock_seo_trends.json` | Keyword volumes, difficulty scores, competitor domain authority |
| `data/site_text/basilford_com/*.txt` | Pre-scraped pages from Basil Ford (Cheektowaga, NY) |
| `data/site_text/basilfordofniagarafalls_com/*.txt` | Pre-scraped pages from Basil Ford of Niagara Falls (NY) |

## Scraping

The dealership sites run on Dealer.com CMS behind **Akamai Bot Manager**, which blocks most automated clients. The scraper tries three backends in priority order:

1. **Playwright** (headless Chromium) — launches a real browser; reliably bypasses Akamai
2. **cloudscraper** — Python-based bypass; blocked on these sites
3. **plain requests** — basic browser UA; blocked

**Install Playwright before scraping:**

```bash
pip install playwright
python -m playwright install chromium
python scripts/scrape_basil_ford.py
```

Each page is cleaned with BeautifulSoup (nav/footer/scripts stripped) and saved as a `.txt` file.

## Project structure

```
confluence-iq-agents/
├── run.py                              # Single entrypoint
├── requirements.txt
├── .env.example
├── scripts/
│   └── scrape_basil_ford.py            # One-time setup: scrape sites → static files
├── data/
│   ├── mock_customer_data.json
│   ├── mock_seo_trends.json
│   └── site_text/
│       ├── basilford_com/*.txt
│       └── basilfordofniagarafalls_com/*.txt
├── src/
│   └── confluence_iq/
│       ├── __init__.py
│       ├── config.py                   # Model, API key loading
│       ├── schemas.py                  # Pydantic output models
│       ├── graph.py                    # LangGraph StateGraph
│       ├── agents/
│       │   ├── data_synthesizer.py     # Agent 1
│       │   ├── competitor_analyst.py   # Agent 2
│       │   └── content_strategist.py   # Agent 3
│       ├── prompts/
│       │   ├── data_synthesizer.md
│       │   ├── competitor_analyst.md
│       │   └── content_strategist.md
│       ├── tools/
│       │   └── loaders.py              # Reads data/ into agent context
│       └── report/
│           └── markdown_report.py      # Agent 3 output → .md
├── output/                             # Generated reports land here
├── tests/
│   ├── test_data_synthesizer.py
│   ├── test_competitor_analyst.py
│   └── test_content_strategist.py
└── docs/
    └── architecture.md
```

## Workflow

```bash
# 1. Pre-scrape
python scripts/scrape_basil_ford.py        # Populates data/site_text/

# 2. Run agents
python run.py                               # Reads static data, writes output/

# 3. Review
cat output/report_20260710_*.md
```

No API keys are needed for scraping. API keys are only used if agents invoke an LLM at runtime (per `LLM_PROVIDER` / `LLM_API_KEY` in `.env`).

## Tech stack

- **LangGraph** — state graph orchestration (parallel agent execution, typed state)
- **Pydantic** — validated agent output schemas
- **Playwright** — headless browser scraping for Akamai-protected sites
- **BeautifulSoup** — HTML cleanup and text extraction
