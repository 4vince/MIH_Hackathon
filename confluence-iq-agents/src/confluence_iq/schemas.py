"""Pydantic models for the output of each agent node."""

from pydantic import BaseModel, Field


class Agent1Output(BaseModel):
    """Agent 1 — Data Synthesizer: structured summary of customer data."""
    business_name: str
    key_segments: list[str] = Field(..., description="Customer segments identified")
    top_pain_points: list[str] = Field(..., max_length=5)
    recommended_channels: list[str]


class Agent2Output(BaseModel):
    """Agent 2 — Competitor Analyst: SEO / competitive landscape."""
    top_keywords: list[str]
    keyword_gaps: list[str]
    competitor_weaknesses: list[str]


class Agent3Output(BaseModel):
    """Agent 3 — Content Strategist: final report outline + sections."""
    report_title: str
    sections: list[dict] = Field(..., description="List of {heading, body}")
    seo_keyword_targets: list[str]
