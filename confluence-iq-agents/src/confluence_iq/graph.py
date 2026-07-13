"""LangGraph StateGraph — wires the 3 agent nodes + verifiers + report writer, with logging."""

import logging
from typing import Callable, Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from .agents.competitor_analyst import CompetitorAnalystAgent
from .agents.content_strategist import ContentStrategistAgent
from .agents.data_synthesizer import DataSynthesizerAgent
from .event_bus import EventBus
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


def build_graph(event_bus: Optional[EventBus] = None) -> StateGraph:
    """Build the pipeline graph.

    If *event_bus* is provided, every node function is wrapped to publish
    ``node_start`` / ``node_end`` / ``edge_traverse`` events for real-time
    visualization.
    """
    builder = StateGraph(AgentState)

    # ── Define all nodes with their names and runner functions ──────────────
    nodes: list[tuple[str, Callable]] = [
        ("data_synthesizer", DataSynthesizerAgent.run),
        ("verify_agent1", verify_agent1_node),
        ("competitor_analyst", CompetitorAnalystAgent.run),
        ("verify_agent2", verify_agent2_node),
        ("content_strategist", ContentStrategistAgent.run),
        ("verify", verify_node),
        ("report_writer", report_node),
    ]

    # ── Optionally wrap each node with EventBus instrumentation ────────────
    if event_bus is not None:

        def _wrap(name: str, fn: Callable) -> Callable:
            def wrapped(state: AgentState) -> dict:
                # Extract inputs from state — which keys are available for this node?
                event_bus.publish("node_start", node=name)
                try:
                    result = fn(state)
                    summary = _summarise_output(name, result)
                    event_bus.publish("node_end", node=name, summary=summary)
                    return result
                except Exception as exc:
                    event_bus.publish("node_end", node=name, error=str(exc))
                    raise

            return wrapped

        nodes = [(name, _wrap(name, fn)) for name, fn in nodes]

    for name, fn in nodes:
        builder.add_node(name, fn)

    # ── Edges (unchanged) ──────────────────────────────────────────────────
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


def _summarise_output(node_name: str, output: dict) -> dict:
    """Build a human-readable summary of a node's output for dashboard display."""
    summary: dict = {}
    if node_name == "data_synthesizer":
        segments = output.get("agent1_output", {})
        if isinstance(segments, dict):
            summary["segments"] = len(segments.get("customer_segments", []))
            summary["insights"] = len(segments.get("key_insights", []))
    elif node_name == "verify_agent1":
        flagged = output.get("agent1_flagged_claims", [])
        summary["flagged"] = len(flagged)
    elif node_name == "competitor_analyst":
        kw = output.get("agent2_output", {})
        if isinstance(kw, dict):
            summary["keywords"] = len(kw.get("keyword_opportunities", []))
            summary["weaknesses"] = len(kw.get("competitor_weaknesses", []))
    elif node_name == "verify_agent2":
        flagged = output.get("agent2_flagged_claims", [])
        summary["flagged"] = len(flagged)
    elif node_name == "content_strategist":
        out = output.get("agent3_output", {})
        if isinstance(out, dict):
            summary["gaps"] = len(out.get("content_gaps", []))
            summary["opportunities"] = len(out.get("opportunity_prioritization", []))
            summary["questions"] = len(out.get("unanswered_buyer_questions", []))
    elif node_name == "verify":
        flagged = output.get("flagged_claims", [])
        summary["flagged"] = len(flagged)
    elif node_name == "report_writer":
        summary["path"] = output.get("report_path", "")
    return summary
