"""Tests for Agent 1 — Data Synthesizer."""

from confluence_iq.agents.data_synthesizer import DataSynthesizerAgent


def test_run_returns_agent1_output():
    result = DataSynthesizerAgent.run({})
    assert "agent1_output" in result
    assert result["agent1_output"]["business_name"] == "Basil Ford of Niagara Falls"
