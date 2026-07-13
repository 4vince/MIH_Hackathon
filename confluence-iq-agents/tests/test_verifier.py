"""Tests for the deterministic claim verifier (no LLM involved)."""

import json

from confluence_iq.schemas import Agent1Output, Agent2Output, Agent3Output, ContentGap, KeywordOpportunity, Opportunity
from confluence_iq.verifier import claim_is_grounded, verify_agent1_output, verify_agent2_output, verify_agent3_output


def test_claim_is_grounded_true_for_matching_text():
    corpus = "Local commuters reported trade-in value transparency concerns during service visits."
    claim = "trade-in value transparency"
    assert claim_is_grounded(claim, corpus) is True


def test_claim_is_grounded_false_for_fabricated_text():
    corpus = "Local commuters reported trade-in value transparency concerns during service visits."
    claim = "used cars niagara falls ontario gets 1900 monthly searches at 44 difficulty"
    assert claim_is_grounded(claim, corpus) is False


def test_verify_agent3_output_strips_unsourced_claims():
    agent3_output = Agent3Output(
        unanswered_buyer_questions=[
            "Does Basil Ford of Niagara Falls offer EV charging installation for tourists?",
            "What is the store's internal profit margin on financing add-ons?",
        ],
        content_gaps=[
            ContentGap(
                gap="No EV FAQ", site="basilford.com", severity="medium",
                evidence="tourists reported EV charging confusion",
            ),
            ContentGap(
                gap="Fabricated gap", site="basilford.com", severity="high",
                evidence="internal survey shows 92 percent satisfaction rate",
            ),
        ],
        opportunity_prioritization=[
            Opportunity(
                rank=1, recommendation="Add EV FAQ",
                rationale="tourists reported EV charging confusion", effort="low",
            ),
        ],
    )
    corpus = (
        "Tourists and seasonal visitors reported EV charging confusion and rental "
        "versus purchase questions at Basil Ford of Niagara Falls."
    )

    cleaned, flagged = verify_agent3_output(agent3_output, {}, {}, corpus)

    assert cleaned.unanswered_buyer_questions == [
        "Does Basil Ford of Niagara Falls offer EV charging installation for tourists?"
    ]
    assert len(cleaned.content_gaps) == 1
    assert cleaned.content_gaps[0].gap == "No EV FAQ"
    assert len(cleaned.opportunity_prioritization) == 1
    assert len(flagged) == 2
    assert any("Fabricated gap" in item for item in flagged)
    assert any("profit margin" in item for item in flagged)


def test_verify_agent3_output_strips_unsourced_buyer_question_only():
    agent3_output = Agent3Output(
        unanswered_buyer_questions=[
            "How is my trade-in value transparency calculated for local commuters?",
            "Completely fabricated question about a topic never mentioned anywhere",
        ],
        content_gaps=[],
        opportunity_prioritization=[],
    )
    corpus = "Local commuters reported trade-in value transparency concerns during service visits."

    cleaned, flagged = verify_agent3_output(agent3_output, {}, {}, corpus)

    assert cleaned.unanswered_buyer_questions == [
        "How is my trade-in value transparency calculated for local commuters?"
    ]
    assert len(flagged) == 1
    assert "fabricated question" in flagged[0].lower()


def test_verify_agent1_output_strips_unsourced_key_insight():
    agent1_output = Agent1Output(
        business_name="Basil Ford of Niagara Falls",
        location="Niagara Falls, ON",
        customer_segments=[],
        key_insights=[
            "New vehicle sales make up 45 percent of revenue",
            "Completely fabricated insight about a metric never mentioned anywhere",
        ],
        recommended_channels=[],
    )
    corpus = json.dumps({"revenue_breakdown": {"new_vehicle_sales": 0.45}})

    cleaned, flagged = verify_agent1_output(agent1_output, corpus)

    assert cleaned.key_insights == ["New vehicle sales make up 45 percent of revenue"]
    assert len(flagged) == 1
    assert "fabricated insight" in flagged[0].lower()


def test_verify_agent2_output_strips_unsourced_keyword_weakness_and_gap():
    agent2_output = Agent2Output(
        site_summary={},
        keyword_opportunities=[
            KeywordOpportunity(term="used cars niagara falls ontario", volume=1900, difficulty=44, relevance="underrepresented"),
            KeywordOpportunity(term="completely invented keyword nobody searched", volume=99999, difficulty=1, relevance="fabricated"),
        ],
        competitor_weaknesses=[
            "low domain authority compared to Queenston Chevrolet",
            "fabricated claim about a competitor that does not exist",
        ],
        observed_content_gaps=[
            "thin service page content",
            "fabricated gap that was never observed",
        ],
    )
    corpus = json.dumps({
        "keywords": [{"term": "used cars niagara falls ontario", "volume": 1900, "difficulty": 44}],
        "competitors": [{"name": "Queenston Chevrolet", "domain_authority": 41}],
        "site_note": "auto service niagara falls page content is thin on FAQs",
    })

    cleaned, flagged = verify_agent2_output(agent2_output, corpus)

    assert [kw.term for kw in cleaned.keyword_opportunities] == ["used cars niagara falls ontario"]
    assert cleaned.competitor_weaknesses == ["low domain authority compared to Queenston Chevrolet"]
    assert cleaned.observed_content_gaps == ["thin service page content"]
    assert len(flagged) == 3
    assert any("invented keyword" in item for item in flagged)
    assert any("does not exist" in item for item in flagged)
    assert any("never observed" in item for item in flagged)
