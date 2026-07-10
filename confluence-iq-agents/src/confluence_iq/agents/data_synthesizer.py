"""Agent 1 — Data Synthesizer: ground customer data into structured insights."""

from ..schemas import Agent1Output
from ..tools.loaders import load_customer_data


class DataSynthesizerAgent:

    @staticmethod
    def run(state: dict) -> dict:
        data = load_customer_data()
        # TODO: call LLM with data_synthesizer.md prompt -> Agent1Output
        output = Agent1Output(
            business_name=data["business_name"],
            key_segments=[s["segment"] for s in data.get("customer_segments", [])],
            top_pain_points=["trade-in transparency", "service wait times"],
            recommended_channels=data.get("current_marketing_channels", []),
        )
        return {"agent1_output": output.model_dump()}
