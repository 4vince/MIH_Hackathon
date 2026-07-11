"""Agent 1/2/3 outputs → final .md file in output/."""

import pathlib
from datetime import datetime

from ..schemas import Agent1Output, Agent2Output, Agent3Output

OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent.parent.parent / "output"


def write_report(
    agent1_output: Agent1Output,
    agent2_output: Agent2Output,
    agent3_output: Agent3Output,
    flagged_claims: list[str],
) -> str:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = OUTPUT_DIR / f"report_{timestamp}.md"

    lines = ["# Confluence IQ Market Intelligence Report — Basil Ford\n"]

    lines.append("## Executive Summary\n")
    lines.append(
        f"Analysis of {agent1_output.business_name} ({agent1_output.location}) covering "
        f"{len(agent1_output.customer_segments)} customer segment(s), "
        f"{len(agent2_output.keyword_opportunities)} keyword opportunity/ies, "
        f"{len(agent3_output.content_gaps)} content gap(s), and "
        f"{len(agent3_output.opportunity_prioritization)} prioritized recommendation(s).\n"
    )

    lines.append("## Customer Insights (Agent 1)\n")
    for segment in agent1_output.customer_segments:
        lines.append(f"### {segment.name}")
        lines.append("**Pain points:** " + ", ".join(segment.pain_points))
        lines.append("**FAQs:** " + ", ".join(segment.faqs))
        lines.append("")
    if agent1_output.key_insights:
        lines.append("**Key insights:**")
        for insight in agent1_output.key_insights:
            lines.append(f"- {insight}")
        lines.append("")

    lines.append("## Competitive Landscape (Agent 2)\n")
    for domain, summary in agent2_output.site_summary.items():
        lines.append(f"**{domain}:** {summary}")
    lines.append("")
    if agent2_output.keyword_opportunities:
        lines.append("**Keyword opportunities:**")
        for kw in agent2_output.keyword_opportunities:
            lines.append(f"- {kw.term} (volume: {kw.volume}, difficulty: {kw.difficulty}, relevance: {kw.relevance})")
        lines.append("")
    if agent2_output.competitor_weaknesses:
        lines.append("**Competitor weaknesses:**")
        for weakness in agent2_output.competitor_weaknesses:
            lines.append(f"- {weakness}")
        lines.append("")

    lines.append("## Unanswered Buyer Questions\n")
    for question in agent3_output.unanswered_buyer_questions:
        lines.append(f"- {question}")
    lines.append("")

    lines.append("## Content Gap Analysis\n")
    lines.append("| Gap | Site | Severity | Evidence |")
    lines.append("|---|---|---|---|")
    for gap in agent3_output.content_gaps:
        lines.append(f"| {gap.gap} | {gap.site} | {gap.severity} | {gap.evidence} |")
    lines.append("")

    lines.append("## Opportunity Prioritization\n")
    lines.append("| Rank | Recommendation | Rationale | Effort |")
    lines.append("|---|---|---|---|")
    for opp in sorted(agent3_output.opportunity_prioritization, key=lambda o: o.rank):
        lines.append(f"| {opp.rank} | {opp.recommendation} | {opp.rationale} | {opp.effort} |")
    lines.append("")

    if flagged_claims:
        lines.append("## ⚠ Flagged Claims (Unverified)\n")
        for claim in flagged_claims:
            lines.append(f"- {claim}")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)
