"""Tests for the deterministic claim verifier (no LLM involved)."""

from confluence_iq.schemas import Agent3Output, ContentGap, Opportunity
from confluence_iq.verifier import claim_is_grounded, verify_agent3_output


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
