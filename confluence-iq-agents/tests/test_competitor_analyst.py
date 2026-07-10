"""Tests for Agent 2 — Competitor Analyst."""

from confluence_iq.agents.competitor_analyst import CompetitorAnalystAgent


def test_run_returns_agent2_output():
    result = CompetitorAnalystAgent.run({})
    assert "agent2_output" in result
    assert len(result["agent2_output"]["top_keywords"]) > 0
