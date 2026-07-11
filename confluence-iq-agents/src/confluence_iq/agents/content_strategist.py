"""Agent 3 — Content Strategist: synthesise agent 1 & 2 into a report draft."""

import json
import logging

from ..llm_client import call_llm
from ..schemas import Agent3Output
from ..tools.loaders import load_prompt

logger = logging.getLogger("confluence_iq.agent3")


class ContentStrategistAgent:

    @staticmethod
    def run(state: dict) -> dict:
        logger.info("=== Agent 3: Content Strategist ===")
        agent1_output = state["agent1_output"]
        agent2_output = state["agent2_output"]
        logger.info(
            "Received Agent 1 output (%d segments) and Agent 2 output (%d keyword opportunities)",
            len(agent1_output["customer_segments"]),
            len(agent2_output["keyword_opportunities"]),
        )

        prompt = load_prompt("content_strategist")
        user_content = (
            f"Agent 1 output (customer insights):\n{json.dumps(agent1_output, indent=2)}\n\n"
            f"Agent 2 output (competitive analysis):\n{json.dumps(agent2_output, indent=2)}"
        )
        output, thinking = call_llm(
            system_prompt=prompt,
            user_content=user_content,
            output_schema=Agent3Output,
        )
        logger.debug("Agent 3 model reasoning: %s", thinking)
        logger.info(
            "Agent 3 drafted %d unanswered questions, %d content gaps, %d opportunities",
            len(output.unanswered_buyer_questions),
            len(output.content_gaps),
            len(output.opportunity_prioritization),
        )
        logger.info("Agent 3 complete. Passing to Verifier.")

        return {"agent3_output": output.model_dump()}
