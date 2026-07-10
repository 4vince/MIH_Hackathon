"""Tests for Agent 3 — Content Strategist."""

from confluence_iq.agents.content_strategist import ContentStrategistAgent


def test_run_returns_report_path():
    state = {
        "agent1_output": {"business_name": "Test"},
        "agent2_output": {"top_keywords": ["kw"]},
    }
    result = ContentStrategistAgent.run(state)
    assert "report_path" in result
    assert result["report_path"].endswith(".md")
