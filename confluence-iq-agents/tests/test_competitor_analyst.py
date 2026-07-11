"""Tests for Agent 2 — Competitor Analyst."""

from unittest.mock import patch

from confluence_iq.agents.competitor_analyst import CompetitorAnalystAgent
from confluence_iq.schemas import Agent2Output, KeywordOpportunity


def _fake_agent2_output() -> Agent2Output:
    return Agent2Output(
        site_summary={"basilford_com": "covers new/used inventory and service"},
        keyword_opportunities=[
            KeywordOpportunity(term="used cars niagara falls ontario", volume=1900, difficulty=44, relevance="underrepresented")
        ],
        competitor_weaknesses=["low domain authority"],
        observed_content_gaps=["no EV charging FAQ"],
    )


@patch("confluence_iq.agents.competitor_analyst.call_llm")
def test_run_returns_valid_agent2_output(mock_call_llm):
    mock_call_llm.return_value = (_fake_agent2_output(), "reasoning text")

    result = CompetitorAnalystAgent.run({})

    assert "agent2_output" in result
    output = Agent2Output(**result["agent2_output"])
    assert len(output.keyword_opportunities) > 0


@patch("confluence_iq.agents.competitor_analyst.call_llm")
def test_run_passes_seo_trends_and_site_text_to_llm(mock_call_llm):
    mock_call_llm.return_value = (_fake_agent2_output(), "reasoning text")

    CompetitorAnalystAgent.run({})

    _, kwargs = mock_call_llm.call_args
    assert "niagara falls" in kwargs["user_content"].lower()
    assert "basilford_com" in kwargs["user_content"] or "Basil Ford" in kwargs["user_content"]
