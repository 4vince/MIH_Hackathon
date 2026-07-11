"""Tests for Agent 1 — Data Synthesizer."""

from unittest.mock import patch

from confluence_iq.agents.data_synthesizer import DataSynthesizerAgent
from confluence_iq.schemas import Agent1Output, CustomerSegment


def _fake_agent1_output() -> Agent1Output:
    return Agent1Output(
        business_name="Basil Ford of Niagara Falls",
        location="Niagara Falls, ON",
        customer_segments=[
            CustomerSegment(
                name="Local commuters",
                pain_points=["trade-in value transparency"],
                faqs=["How is my trade-in value calculated?"],
            )
        ],
        key_insights=["New vehicle sales make up 45% of revenue"],
        recommended_channels=["Google Ads", "Facebook"],
    )


@patch("confluence_iq.agents.data_synthesizer.call_llm")
def test_run_returns_valid_agent1_output(mock_call_llm):
    mock_call_llm.return_value = (_fake_agent1_output(), "reasoning text")

    result = DataSynthesizerAgent.run({})

    assert "agent1_output" in result
    output = Agent1Output(**result["agent1_output"])
    assert len(output.customer_segments) > 0
    assert all(seg.name for seg in output.customer_segments)


@patch("confluence_iq.agents.data_synthesizer.call_llm")
def test_run_passes_real_customer_data_to_llm(mock_call_llm):
    mock_call_llm.return_value = (_fake_agent1_output(), "reasoning text")

    DataSynthesizerAgent.run({})

    _, kwargs = mock_call_llm.call_args
    assert "Basil Ford" in kwargs["user_content"]
