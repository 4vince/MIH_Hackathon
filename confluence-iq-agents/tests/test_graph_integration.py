"""End-to-end integration test for the full graph (all LLM calls mocked)."""

from unittest.mock import patch

from confluence_iq.graph import build_graph
from confluence_iq.schemas import (
    Agent1Output, Agent2Output, Agent3Output,
    ContentGap, CustomerSegment, KeywordOpportunity, Opportunity,
)


def _agent1() -> Agent1Output:
    return Agent1Output(
        business_name="Basil Ford of Niagara Falls",
        location="Niagara Falls, ON",
        customer_segments=[
            CustomerSegment(name="Local commuters", pain_points=["trade-in value transparency"], faqs=["How is my trade-in value calculated?"])
        ],
        key_insights=["New vehicle sales make up 45% of revenue"],
        recommended_channels=["Google Ads"],
    )


def _agent2() -> Agent2Output:
    return Agent2Output(
        site_summary={"basilford_com": "covers new/used inventory"},
        keyword_opportunities=[
            KeywordOpportunity(term="used cars niagara falls", volume=1900, difficulty=44, relevance="underrepresented")
        ],
        competitor_weaknesses=["low domain authority"],
        observed_content_gaps=["no EV FAQ"],
    )


def _agent3_with_one_fabricated_claim() -> Agent3Output:
    return Agent3Output(
        unanswered_buyer_questions=["Does Basil Ford offer EV charging installation?"],
        content_gaps=[
            ContentGap(gap="No EV FAQ", site="basilford.com", severity="medium", evidence="trade-in value transparency was a commuter pain point"),
            ContentGap(gap="Fabricated gap", site="basilford.com", severity="high", evidence="completely made up statistic with no source"),
        ],
        opportunity_prioritization=[
            Opportunity(rank=1, recommendation="Add EV FAQ", rationale="used cars niagara falls is underrepresented", effort="low"),
        ],
    )


@patch("confluence_iq.agents.content_strategist.call_llm")
@patch("confluence_iq.agents.competitor_analyst.call_llm")
@patch("confluence_iq.agents.data_synthesizer.call_llm")
def test_full_pipeline_runs_and_strips_fabricated_claim(mock_ds_llm, mock_ca_llm, mock_cs_llm, tmp_path, monkeypatch):
    import confluence_iq.report.markdown_report as mr
    monkeypatch.setattr(mr, "OUTPUT_DIR", tmp_path)

    mock_ds_llm.return_value = (_agent1(), "thinking 1")
    mock_ca_llm.return_value = (_agent2(), "thinking 2")
    mock_cs_llm.return_value = (_agent3_with_one_fabricated_claim(), "thinking 3")

    graph = build_graph()
    final_state = graph.invoke({})

    assert final_state["report_path"]
    assert len(final_state["flagged_claims"]) == 2
    assert any("Fabricated gap" in item for item in final_state["flagged_claims"])
    assert any("no EV FAQ" in item for item in final_state["flagged_claims"])

    report_text = mr.pathlib.Path(final_state["report_path"]).read_text(encoding="utf-8")
    assert "No EV FAQ" in report_text
    assert "Fabricated gap" not in report_text.split("⚠ Flagged Claims")[0]
    assert "⚠ Flagged Claims" in report_text
