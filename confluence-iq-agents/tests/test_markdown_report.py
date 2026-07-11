"""Tests for the markdown report writer."""

from confluence_iq.report.markdown_report import write_report
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


def _agent3() -> Agent3Output:
    return Agent3Output(
        unanswered_buyer_questions=["Does Basil Ford offer EV charging installation?"],
        content_gaps=[
            ContentGap(gap="No EV FAQ", site="basilford.com", severity="medium", evidence="tourists reported EV charging confusion")
        ],
        opportunity_prioritization=[
            Opportunity(rank=1, recommendation="Add EV FAQ", rationale="matches keyword gap", effort="low")
        ],
    )


def test_write_report_includes_required_sections(tmp_path, monkeypatch):
    import confluence_iq.report.markdown_report as mr
    monkeypatch.setattr(mr, "OUTPUT_DIR", tmp_path)

    path = write_report(_agent1(), _agent2(), _agent3(), [])

    text = mr.pathlib.Path(path).read_text(encoding="utf-8")
    assert "## Unanswered Buyer Questions" in text
    assert "## Content Gap Analysis" in text
    assert "## Opportunity Prioritization" in text
    assert "Does Basil Ford offer EV charging installation?" in text
    assert "⚠ Flagged Claims" not in text


def test_write_report_shows_flagged_claims_when_present(tmp_path, monkeypatch):
    import confluence_iq.report.markdown_report as mr
    monkeypatch.setattr(mr, "OUTPUT_DIR", tmp_path)

    path = write_report(_agent1(), _agent2(), _agent3(), ["Fabricated claim example"])

    text = mr.pathlib.Path(path).read_text(encoding="utf-8")
    assert "⚠ Flagged Claims" in text
    assert "Fabricated claim example" in text
