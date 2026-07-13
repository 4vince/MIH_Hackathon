"""LangGraph StateGraph — wires the 3 agent nodes + verifiers + report writer, with logging."""

import logging
from typing import Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from .agents.competitor_analyst import CompetitorAnalystAgent
from .agents.content_strategist import ContentStrategistAgent
from .agents.data_synthesizer import DataSynthesizerAgent
from .report.markdown_report import write_report
from .schemas import Agent1Output, Agent2Output, Agent3Output
from .tools.loaders import load_raw_corpus_text
from .verifier import verify_agent1_output, verify_agent2_output, verify_agent3_output

logger = logging.getLogger("confluence_iq.graph")


class AgentState(TypedDict):
    agent1_output: Optional[dict]
    agent2_output: Optional[dict]
    agent3_output: Optional[dict]
    agent1_flagged_claims: Optional[list]
    agent2_flagged_claims: Optional[list]
    flagged_claims: Optional[list]
    report_path: Optional[str]


def verify_agent1_node(state: AgentState) -> dict:
    logger.info("=== Verifier (Agent 1) ===")
    agent1_output = Agent1Output(**state["agent1_output"])
    corpus = load_raw_corpus_text()
    cleaned, flagged = verify_agent1_output(agent1_output, corpus)
    if flagged:
        for item in flagged:
            logger.warning("  Flagged: %s", item)
        logger.info("Verifier stripped %d unsourced Agent 1 claim(s).", len(flagged))
    else:
        logger.info("Agent 1 output verified against source data.")
    return {"agent1_output": cleaned.model_dump(), "agent1_flagged_claims": flagged}


def verify_agent2_node(state: AgentState) -> dict:
    logger.info("=== Verifier (Agent 2) ===")
    agent2_output = Agent2Output(**state["agent2_output"])
    corpus = load_raw_corpus_text()
    cleaned, flagged = verify_agent2_output(agent2_output, corpus)
    if flagged:
        for item in flagged:
            logger.warning("  Flagged: %s", item)
        logger.info("Verifier stripped %d unsourced Agent 2 claim(s).", len(flagged))
    else:
        logger.info("Agent 2 output verified against source data.")
    return {"agent2_output": cleaned.model_dump(), "agent2_flagged_claims": flagged}


def verify_node(state: AgentState) -> dict:
    logger.info("=== Verifier (Agent 3) ===")
    agent3_output = Agent3Output(**state["agent3_output"])
    corpus = load_raw_corpus_text()
    cleaned, flagged = verify_agent3_output(
        agent3_output, state["agent1_output"], state["agent2_output"], corpus
    )
    if flagged:
        for item in flagged:
            logger.warning("  Flagged: %s", item)
        logger.info("Verifier stripped %d unsourced Agent 3 claim(s).", len(flagged))
    else:
        logger.info("All Agent 3 claims verified against source data.")
    return {"agent3_output": cleaned.model_dump(), "flagged_claims": flagged}


def report_node(state: AgentState) -> dict:
    logger.info("=== Report Writer ===")
    agent1 = Agent1Output(**state["agent1_output"])
    agent2 = Agent2Output(**state["agent2_output"])
    agent3 = Agent3Output(**state["agent3_output"])
    all_flagged = (
        (state.get("agent1_flagged_claims") or [])
        + (state.get("agent2_flagged_claims") or [])
        + (state.get("flagged_claims") or [])
    )
    path = write_report(agent1, agent2, agent3, all_flagged)
    logger.info("Report written to %s", path)
    return {"report_path": path, "flagged_claims": all_flagged}


def build_graph() -> StateGraph:
    builder = StateGraph(AgentState)

    builder.add_node("data_synthesizer", DataSynthesizerAgent.run)
    builder.add_node("verify_agent1", verify_agent1_node)
    builder.add_node("competitor_analyst", CompetitorAnalystAgent.run)
    builder.add_node("verify_agent2", verify_agent2_node)
    builder.add_node("content_strategist", ContentStrategistAgent.run)
    builder.add_node("verify", verify_node)
    builder.add_node("report_writer", report_node)

    builder.add_edge(START, "data_synthesizer")
    builder.add_edge(START, "competitor_analyst")   # parallel with agent 1
    builder.add_edge("data_synthesizer", "verify_agent1")
    builder.add_edge("competitor_analyst", "verify_agent2")
    builder.add_edge("verify_agent1", "content_strategist")
    builder.add_edge("verify_agent2", "content_strategist")
    builder.add_edge("content_strategist", "verify")
    builder.add_edge("verify", "report_writer")
    builder.add_edge("report_writer", END)

    return builder.compile()
