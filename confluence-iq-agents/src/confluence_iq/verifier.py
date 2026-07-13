"""Deterministic (non-LLM) claim verifier — enforces the 'No Hallucinations' requirement."""

import json
import re

from .schemas import Agent1Output, Agent2Output, Agent3Output

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
    """Strip buyer questions / content gaps / opportunities whose text isn't grounded in source data."""
    corpus = " ".join([json.dumps(agent1_output), json.dumps(agent2_output), raw_corpus])
    flagged: list[str] = []

    kept_questions = []
    for question in agent3_output.unanswered_buyer_questions:
        if claim_is_grounded(question, corpus):
            kept_questions.append(question)
        else:
            flagged.append(f'Unanswered buyer question — unsourced: "{question}"')

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
        "unanswered_buyer_questions": kept_questions,
        "content_gaps": kept_gaps,
        "opportunity_prioritization": kept_opportunities,
    })
    return cleaned, flagged


def verify_agent1_output(
    agent1_output: Agent1Output,
    raw_corpus: str,
) -> tuple[Agent1Output, list[str]]:
    """Strip key insights whose text isn't grounded in the raw source data."""
    flagged: list[str] = []

    kept_insights = []
    for insight in agent1_output.key_insights:
        if claim_is_grounded(insight, raw_corpus):
            kept_insights.append(insight)
        else:
            flagged.append(f'Agent 1 key insight — unsourced: "{insight}"')

    cleaned = agent1_output.model_copy(update={"key_insights": kept_insights})
    return cleaned, flagged


def verify_agent2_output(
    agent2_output: Agent2Output,
    raw_corpus: str,
) -> tuple[Agent2Output, list[str]]:
    """Strip keyword opportunities / competitor weaknesses / content gaps not grounded in raw source data."""
    flagged: list[str] = []

    kept_keywords = []
    for kw in agent2_output.keyword_opportunities:
        claim = f"{kw.term} {kw.volume} {kw.difficulty}"
        if claim_is_grounded(claim, raw_corpus):
            kept_keywords.append(kw)
        else:
            flagged.append(
                f'Agent 2 keyword opportunity — unsourced: "{kw.term}" '
                f"(volume={kw.volume}, difficulty={kw.difficulty})"
            )

    kept_weaknesses = []
    for weakness in agent2_output.competitor_weaknesses:
        if claim_is_grounded(weakness, raw_corpus):
            kept_weaknesses.append(weakness)
        else:
            flagged.append(f'Agent 2 competitor weakness — unsourced: "{weakness}"')

    kept_gaps = []
    for gap in agent2_output.observed_content_gaps:
        if claim_is_grounded(gap, raw_corpus):
            kept_gaps.append(gap)
        else:
            flagged.append(f'Agent 2 observed content gap — unsourced: "{gap}"')

    cleaned = agent2_output.model_copy(update={
        "keyword_opportunities": kept_keywords,
        "competitor_weaknesses": kept_weaknesses,
        "observed_content_gaps": kept_gaps,
    })
    return cleaned, flagged
