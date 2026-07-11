"""Tests for Agent 3 — Content Strategist."""

from unittest.mock import patch

from confluence_iq.agents.content_strategist import ContentStrategistAgent
from confluence_iq.schemas import Agent3Output, ContentGap, Opportunity


def _fake_agent3_output() -> Agent3Output:
    return Agent3Output(
        unanswered_buyer_questions=["Does Basil Ford offer EV charging installation?"],
        content_gaps=[
            ContentGap(
                gap="No EV charging FAQ page",
                site="basilford.com",
                severity="medium",
                evidence="Agent 1 found EV charging confusion among the tourist segment",
            )
        ],
        opportunity_prioritization=[
            Opportunity(
                rank=1,
                recommendation="Add an EV charging FAQ page",
                rationale="Matches Agent 2's underrepresented keyword gap",
                effort="low",
            )
        ],
    )


def _state_with_agent1_and_agent2() -> dict:
    return {
        "agent1_output": {
            "business_name": "Basil Ford of Niagara Falls",
            "location": "Niagara Falls, ON",
            "customer_segments": [],
            "key_insights": [],
            "recommended_channels": [],
        },
        "agent2_output": {
            "site_summary": {},
            "keyword_opportunities": [],
            "competitor_weaknesses": [],
            "observed_content_gaps": [],
        },
    }


@patch("confluence_iq.agents.content_strategist.call_llm")
def test_run_returns_valid_agent3_output(mock_call_llm):
    mock_call_llm.return_value = (_fake_agent3_output(), "reasoning text")

    result = ContentStrategistAgent.run(_state_with_agent1_and_agent2())

    assert "agent3_output" in result
    output = Agent3Output(**result["agent3_output"])
    assert len(output.content_gaps) > 0


@patch("confluence_iq.agents.content_strategist.call_llm")
def test_run_actually_consumes_agent1_and_agent2_state(mock_call_llm):
    """Regression test for the bug where Agent 3 ignored `state` entirely."""
    mock_call_llm.return_value = (_fake_agent3_output(), "reasoning text")

    ContentStrategistAgent.run(_state_with_agent1_and_agent2())

    _, kwargs = mock_call_llm.call_args
    assert "Niagara Falls" in kwargs["user_content"]
