"""Tests for enriched agent output schemas."""

import pytest
from pydantic import ValidationError

from confluence_iq.schemas import (
    Agent1Output,
    Agent2Output,
    Agent3Output,
    ContentGap,
    CustomerSegment,
    KeywordOpportunity,
    Opportunity,
)


def test_agent1_output_requires_customer_segments():
    output = Agent1Output(
        business_name="Basil Ford",
        location="Cheektowaga, NY",
        customer_segments=[
            CustomerSegment(name="Commuters", pain_points=["wait times"], faqs=["How long?"])
        ],
        key_insights=["insight one"],
        recommended_channels=["Google Ads"],
    )
    assert output.customer_segments[0].name == "Commuters"


def test_agent2_output_keyword_opportunity_fields():
    output = Agent2Output(
        site_summary={"basilford.com": "covers new/used inventory"},
        keyword_opportunities=[
            KeywordOpportunity(term="used cars niagara falls", volume=1900, difficulty=44, relevance="underrepresented")
        ],
        competitor_weaknesses=["low domain authority"],
        observed_content_gaps=["no FAQ page"],
    )
    assert output.keyword_opportunities[0].volume == 1900


def test_agent3_output_requires_three_report_elements():
    output = Agent3Output(
        unanswered_buyer_questions=["Does Basil Ford offer EV charging installation?"],
        content_gaps=[
            ContentGap(gap="No EV FAQ", site="basilford.com", severity="medium", evidence="some evidence")
        ],
        opportunity_prioritization=[
            Opportunity(rank=1, recommendation="Add EV FAQ", rationale="some rationale", effort="low")
        ],
    )
    assert len(output.unanswered_buyer_questions) == 1
    assert output.content_gaps[0].site == "basilford.com"
    assert output.opportunity_prioritization[0].rank == 1


def test_content_gap_missing_field_raises():
    with pytest.raises(ValidationError):
        ContentGap(gap="No EV FAQ", site="basilford.com", severity="medium")  # missing evidence
