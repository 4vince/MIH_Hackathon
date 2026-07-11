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
        unanswered_buyer_questions=["Does Basil Ford offer EV charging installation?"],
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
    corpus = "Tourists and seasonal visitors reported EV charging confusion and rental versus purchase questions."

    cleaned, flagged = verify_agent3_output(agent3_output, {}, {}, corpus)

    assert len(cleaned.content_gaps) == 1
    assert cleaned.content_gaps[0].gap == "No EV FAQ"
    assert len(cleaned.opportunity_prioritization) == 1
    assert len(flagged) == 1
    assert "Fabricated gap" in flagged[0]
