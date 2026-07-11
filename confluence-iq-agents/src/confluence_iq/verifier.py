"""Deterministic (non-LLM) claim verifier — enforces the 'No Hallucinations' requirement."""

import json
import re

from .schemas import Agent3Output

_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "is", "are", "was", "were", "be", "been", "this", "that",
    "it", "as", "by", "from", "has", "have", "had", "not", "no",
}


def _significant_words(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w for w in words if w not in _STOPWORDS and len(w) >= 3}


def claim_is_grounded(claim: str, corpus: str, threshold: float = 0.6) -> bool:
    """Deterministic keyword-overlap check — no LLM call."""
    claim_words = _significant_words(claim)
    if not claim_words:
        return True
    corpus_words = _significant_words(corpus)
    overlap = claim_words & corpus_words
    return (len(overlap) / len(claim_words)) >= threshold


def verify_agent3_output(
    agent3_output: Agent3Output,
    agent1_output: dict,
    agent2_output: dict,
    raw_corpus: str,
) -> tuple[Agent3Output, list[str]]:
    """Strip content gaps / opportunities whose evidence/rationale isn't grounded in source data."""
    corpus = " ".join([json.dumps(agent1_output), json.dumps(agent2_output), raw_corpus])
    flagged: list[str] = []

    kept_gaps = []
    for gap in agent3_output.content_gaps:
        if claim_is_grounded(gap.evidence, corpus):
            kept_gaps.append(gap)
        else:
            flagged.append(f'Content gap "{gap.gap}" — unsourced evidence: "{gap.evidence}"')

    kept_opportunities = []
    for opp in agent3_output.opportunity_prioritization:
        if claim_is_grounded(opp.rationale, corpus):
            kept_opportunities.append(opp)
        else:
            flagged.append(f'Opportunity "{opp.recommendation}" — unsourced rationale: "{opp.rationale}"')

    cleaned = agent3_output.model_copy(update={
        "content_gaps": kept_gaps,
        "opportunity_prioritization": kept_opportunities,
    })
    return cleaned, flagged
