"""Agent 3 — Content Strategist: synthesise agent 1 & 2 into a report."""

from ..schemas import Agent3Output
from ..report.markdown_report import write_report


class ContentStrategistAgent:

    @staticmethod
    def run(state: dict) -> dict:
        # TODO: call LLM with content_strategist.md prompt -> Agent3Output
        output = Agent3Output(
            report_title="Confluence IQ Marketing Report",
            sections=[
                {"heading": "Executive Summary", "body": "Placeholder."},
                {"heading": "Customer Insights", "body": "Placeholder."},
                {"heading": "Competitive Landscape", "body": "Placeholder."},
                {"heading": "Content Recommendations", "body": "Placeholder."},
            ],
            seo_keyword_targets=["used cars niagara falls", "auto service niagara falls"],
        )
        path = write_report(output)
        return {"agent3_output": output.model_dump(), "report_path": path}
