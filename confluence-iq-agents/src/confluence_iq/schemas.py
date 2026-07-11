"""Pydantic models for the output of each agent node."""

from pydantic import BaseModel, Field


class CustomerSegment(BaseModel):
    name: str
    pain_points: list[str]
    faqs: list[str]


class Agent1Output(BaseModel):
    """Agent 1 — Data Synthesizer: structured summary of customer data."""
    business_name: str
    location: str
    customer_segments: list[CustomerSegment]
    key_insights: list[str]
    recommended_channels: list[str]


class KeywordOpportunity(BaseModel):
    term: str
    volume: int
    difficulty: int
    relevance: str = Field(..., description="e.g. 'well covered', 'underrepresented', 'not covered'")


class Agent2Output(BaseModel):
    """Agent 2 — Competitor Analyst: SEO / competitive landscape."""
    site_summary: dict[str, str] = Field(..., description="{domain: summary of what the site covers}")
    keyword_opportunities: list[KeywordOpportunity]
    competitor_weaknesses: list[str]
    observed_content_gaps: list[str]


class ContentGap(BaseModel):
    gap: str
    site: str
    severity: str = Field(..., description="'high' | 'medium' | 'low'")
    evidence: str = Field(..., description="Must trace to Agent1/Agent2 output or source data")


class Opportunity(BaseModel):
    rank: int
    recommendation: str
    rationale: str = Field(..., description="Must trace to Agent1/Agent2 output or source data")
    effort: str = Field(..., description="'low' | 'medium' | 'high'")


class Agent3Output(BaseModel):
    """Agent 3 — Content Strategist: content-gap analysis + prioritization."""
    unanswered_buyer_questions: list[str]
    content_gaps: list[ContentGap]
    opportunity_prioritization: list[Opportunity]
