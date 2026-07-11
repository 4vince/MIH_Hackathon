"""Agent 1 — Data Synthesizer: ground customer data into structured insights."""

import json
import logging

from ..llm_client import call_llm
from ..schemas import Agent1Output
from ..tools.loaders import load_customer_data, load_prompt

logger = logging.getLogger("confluence_iq.agent1")


class DataSynthesizerAgent:

    @staticmethod
    def run(state: dict) -> dict:
        logger.info("=== Agent 1: Data Synthesizer ===")
        data = load_customer_data()
        logger.info(
            "Loaded customer data for %s (%d segments)",
            data["business_name"],
            len(data.get("customer_segments", [])),
        )

        prompt = load_prompt("data_synthesizer")
        output, thinking = call_llm(
            system_prompt=prompt,
            user_content=f"Customer data:\n{json.dumps(data, indent=2)}",
            output_schema=Agent1Output,
        )
        logger.debug("Agent 1 model reasoning: %s", thinking)
        logger.info(
            "Agent 1 found %d customer segments, %d key insights",
            len(output.customer_segments),
            len(output.key_insights),
        )
        logger.info("Agent 1 complete. Passing to Content Strategist.")

        return {"agent1_output": output.model_dump()}
