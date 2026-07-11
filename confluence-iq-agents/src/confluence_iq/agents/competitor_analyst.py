"""Agent 2 — Competitor Analyst: SEO trends + site text analysis."""

import json
import logging

from ..llm_client import call_llm
from ..schemas import Agent2Output
from ..tools.loaders import load_prompt, load_seo_trends, load_site_texts

logger = logging.getLogger("confluence_iq.agent2")


class CompetitorAnalystAgent:

    @staticmethod
    def run(state: dict) -> dict:
        logger.info("=== Agent 2: Competitor Analyst ===")
        trends = load_seo_trends()
        site_texts = load_site_texts()
        logger.info(
            "Loaded SEO trends (%d keywords) and site text for %d domains",
            len(trends.get("keywords", [])),
            len(site_texts),
        )

        prompt = load_prompt("competitor_analyst")
        user_content = (
            f"SEO trends:\n{json.dumps(trends, indent=2)}\n\n"
            f"Scraped site text:\n{json.dumps(site_texts, indent=2)}"
        )
        output, thinking = call_llm(
            system_prompt=prompt,
            user_content=user_content,
            output_schema=Agent2Output,
        )
        logger.debug("Agent 2 model reasoning: %s", thinking)
        logger.info(
            "Agent 2 found %d keyword opportunities, %d content gaps",
            len(output.keyword_opportunities),
            len(output.observed_content_gaps),
        )
        logger.info("Agent 2 complete. Passing to Content Strategist.")

        return {"agent2_output": output.model_dump()}
