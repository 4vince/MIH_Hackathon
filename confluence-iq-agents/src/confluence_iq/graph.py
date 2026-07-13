"""LangGraph StateGraph — wires the 3 agent nodes + verifier + report writer, with logging."""

import logging
from typing import Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from .agents.competitor_analyst import CompetitorAnalystAgent
from .agents.content_strategist import ContentStrategistAgent
from .agents.data_synthesizer import DataSynthesizerAgent
from .report.markdown_report import write_report
from .schemas import Agent1Output, Agent2Output, Agent3Output
from .tools.loaders import load_raw_corpus_text
from .verifier import verify_agent3_output

logger = logging.getLogger("confluence_iq.graph")


class AgentState(TypedDict):
    agent1_output: Optional[dict]
    agent2_output: Optional[dict]
    agent3_output: Optional[dict]
    flagged_claims: Optional[list]
    report_path: Optional[str]


def verify_node(state: AgentState) -> dict:
    logger.info("=== Verifier ===")
    agent3_output = Agent3Output(**state["agent3_output"])
    corpus = load_raw_corpus_text()
    cleaned, flagged = verify_agent3_output(
        agent3_output, state["agent1_output"], state["agent2_output"], corpus
    )
    if flagged:
        for item in flagged:
            logger.warning("  Flagged: %s", item)
        logger.info("Verifier stripped %d unsourced claim(s).", len(flagged))
    else:
        logger.info("All claims verified against source data.")
    return {"agent3_output": cleaned.model_dump(), "flagged_claims": flagged}


def report_node(state: AgentState) -> dict:
    logger.info("=== Report Writer ===")
    agent1 = Agent1Output(**state["agent1_output"])
    agent2 = Agent2Output(**state["agent2_output"])
    agent3 = Agent3Output(**state["agent3_output"])
    path = write_report(agent1, agent2, agent3, state.get("flagged_claims") or [])
    logger.info("Report written to %s", path)
    return {"report_path": path}


def build_graph() -> StateGraph:
    builder = StateGraph(AgentState)

    builder.add_node("data_synthesizer", DataSynthesizerAgent.run)
    builder.add_node("competitor_analyst", CompetitorAnalystAgent.run)
    builder.add_node("content_strategist", ContentStrategistAgent.run)
    builder.add_node("verify", verify_node)
    builder.add_node("report_writer", report_node)

    builder.add_edge(START, "data_synthesizer")
    builder.add_edge(START, "competitor_analyst")   # parallel with agent 1
    builder.add_edge("data_synthesizer", "content_strategist")
    builder.add_edge("competitor_analyst", "content_strategist")
    builder.add_edge("content_strategist", "verify")
    builder.add_edge("verify", "report_writer")
    builder.add_edge("report_writer", END)

    return builder.compile()
