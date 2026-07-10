"""Agent 2 — Competitor Analyst: SEO trends + site text analysis."""

from ..schemas import Agent2Output
from ..tools.loaders import load_seo_trends, load_site_texts


class CompetitorAnalystAgent:

    @staticmethod
    def run(state: dict) -> dict:
        trends = load_seo_trends()
        site_texts = load_site_texts()
        # TODO: call LLM with competitor_analyst.md prompt -> Agent2Output
        output = Agent2Output(
            top_keywords=[kw["term"] for kw in trends.get("keywords", [])[:5]],
            keyword_gaps=["long-tail service keywords"],
            competitor_weaknesses=["low domain authority"],
        )
        return {"agent2_output": output.model_dump()}
