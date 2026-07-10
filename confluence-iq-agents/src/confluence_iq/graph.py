"""LangGraph StateGraph — wires the 3 agent nodes with logging."""

from langgraph.graph import StateGraph, START, END
from langgraph.types import StateSnapshot
from typing import TypedDict, Optional

from confluence_iq.agents.data_synthesizer import DataSynthesizerAgent
from confluence_iq.agents.competitor_analyst import CompetitorAnalystAgent
from confluence_iq.agents.content_strategist import ContentStrategistAgent


class AgentState(TypedDict):
    agent1_output: Optional[dict]
    agent2_output: Optional[dict]
    agent3_output: Optional[dict]
    report_path: Optional[str]


def build_graph() -> StateGraph:
    builder = StateGraph(AgentState)

    builder.add_node("data_synthesizer", DataSynthesizerAgent.run)
    builder.add_node("competitor_analyst", CompetitorAnalystAgent.run)
    builder.add_node("content_strategist", ContentStrategistAgent.run)

    builder.add_edge(START, "data_synthesizer")
    builder.add_edge(START, "competitor_analyst")   # parallel with agent 1
    builder.add_edge("data_synthesizer", "content_strategist")
    builder.add_edge("competitor_analyst", "content_strategist")
    builder.add_edge("content_strategist", END)

    return builder.compile()
