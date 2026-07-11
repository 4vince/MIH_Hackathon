# Explore & Confluence IQ Hackathon

GitHub Repo: https://github.com/4vince/MIH_Hackathon

## Confluence IQ Agents - Building the Unified Market Intelligence Layer!

### The Mission

You'll be building an AI-driven Market Intelligence system that pulls together first-party data (CRM, sales calls, tickets) and external market data, then uses AI agents to surface actionable content gaps and opportunities. Everything will be tested against Basilford.com and BasilfordOfNiagaraFalls.com.

There are three challenge tracks to choose from (or combine, if you're feeling ambitious):
- **The Unified Data Moat** — Data engineering, vector databases, and RAG. Build the ingestion + retrieval pipeline.
- **The Multi-Agent Orchestra** — Build a team of specialized AI agents (Data Synthesizer, Market Competitor Analyst, Content Strategist) that collaborate to produce a market intelligence report.
- **Actionable Intelligence Dashboard** — Full-stack app with a live LLM-powered backend, a dashboard, and role-based access control.

Full details, scope, and acceptance criteria for each challenge are already in the PRD attached to this message. Read through your chosen track closely, since judging is based on how well you meet those specific criteria.

### Timeline

- **Today and the next weekdays:** You'll get a headstart to begin planning, forming teams consisting of 2 members, and getting your environment set up.
- **Saturday:** Formal hackathon kickoff. Attendance is required for all interns, alongside the rest of the MIH team.
- **Sunday:** Continue building, code freeze at end of day.
- **Monday morning:** Live demo presentations (3 minutes each + 2 minutes Q&A). No slide decks, working software only!

### Important: Use our internal LLM endpoint

Instead of using your own API keys for any external LLM provider, please use our internal endpoint:

```
https://api.iamtzar.com/
```

This endpoint doesn't rate-limit, so it'll save you from hitting usage caps mid-build. Please use this instead of personal or team API keys.

### Questions or concerns?

Please don't hesitate to reach out, whether it's about team formation, technical scope, the LLM endpoint, or anything else. We want you to feel supported throughout the weekend, so ask early and often rather than getting stuck.

Here are the models you can use with the endpoint:

| Task                  | Best Model                   | Why                     |
| ---------------------- | ----------------------------- | ------------------------ |
| Blog Writing          | qwen3.5:397b-cloud           | High quality, creative  |
| Code Generation       | qwen3-coder:480b-cloud       | Specialized for dev     |
| Quick Local Tasks     | gemma3:4b or llama3.2:latest | Fast, low latency       |
| Vision/Image Analysis | qwen3-vl:235b-cloud          | Multimodal capability   |
| Embeddings/Search     | nomic-embed-text:latest      | Optimized for vectors   |
| Custom TzarAI Voice   | tzar:3.5                     | Your personalized model |

Gemma, Tzar3.5, Qwen3 models have web-search capability.

---

## Executive Summary

The goal of this hackathon is to build the MVP of Confluence IQ Agents—an AI-driven Market Intelligence Layer. The system must aggregate proprietary first-party data, layer it with external market data, and use an orchestra of AI agents to deliver actionable content gap analyses and opportunity prioritization. The ultimate test cases will be applied to Basilford.com and Basilfordofniagarafalls.com.

Teams can choose to tackle one of the three challenges below, or a highly ambitious team can attempt to connect all three.

---

## Challenge 2: The Multi-Agent Orchestra (AI & Logic)

**Focus:** LLMs, Agentic Frameworks (CrewAI, AutoGen, LangChain), Prompt Engineering.

### 1. Problem Statement

A single LLM prompt is not enough to perform deep market intelligence. We need an "orchestra of AI agents," each with specialized roles, to debate, analyze, and synthesize data into actionable intelligence.

### 2. Objective

Develop a multi-agent framework ("Confluence IQ Agents") where specialized AI agents collaborate autonomously to generate a comprehensive Market Intelligence report.

### 3. Scope & Key Features

- **Agent 1: The Data Synthesizer** — Reads raw 1st-party customer data (mocked) to identify common pain points and FAQs.
- **Agent 2: The Market Competitor Analyst** — Analyzes external web data and SEO trends.
- **Agent 3: The Content Strategist** — Compares the output of Agent 1 and Agent 2 to identify "Content Gaps" (what buyers want vs. what is actually on the website).
- **Agent Orchestration** — A workflow where these agents pass information sequentially or hierarchically to produce a final output.

### 4. Out of Scope

- Building the database from scratch (can use static JSON files as "data").
- Real-time live web scraping (can use pre-scraped text files of the Basil Ford sites for speed).

### 5. Acceptance Criteria (Rule for Output Acceptability)

- **Pass/Fail:** The team must trigger the agent workflow with a single command. The system must visibly show the agents "talking" to each other or passing context.
- **Output Quality:** The final output must be a generated Markdown report specifically detailing:
  - Unanswered buyer questions.
  - A specific content gap analysis for Basil Ford.
  - Opportunity prioritization (what content they should create first).
- **No Hallucinations:** The agents must base their findings solely on the provided context/files.
