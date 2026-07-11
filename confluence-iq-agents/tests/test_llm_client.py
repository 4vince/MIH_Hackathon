"""Tests for the internal LLM client (HTTP layer mocked — no live network calls)."""

from unittest.mock import MagicMock, patch

from confluence_iq.llm_client import call_llm
from confluence_iq.schemas import Agent1Output, CustomerSegment


def _fake_agent1_output() -> Agent1Output:
    return Agent1Output(
        business_name="Basil Ford",
        location="Cheektowaga, NY",
        customer_segments=[
            CustomerSegment(name="Commuters", pain_points=["wait times"], faqs=["How long is a service visit?"])
        ],
        key_insights=["insight"],
        recommended_channels=["Google Ads"],
    )


@patch("confluence_iq.llm_client.httpx.post")
def test_call_llm_parses_message_content_and_thinking(mock_post):
    fake_output = _fake_agent1_output()
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "message": {
            "role": "assistant",
            "content": fake_output.model_dump_json(),
            "thinking": "reasoning trace",
        },
        "done": True,
    }
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    output, thinking = call_llm(
        system_prompt="system prompt",
        user_content="user content",
        output_schema=Agent1Output,
    )

    assert output.business_name == "Basil Ford"
    assert thinking == "reasoning trace"


@patch("confluence_iq.llm_client.httpx.post")
def test_call_llm_hits_correct_route_with_structured_format(mock_post):
    fake_output = _fake_agent1_output()
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "message": {"role": "assistant", "content": fake_output.model_dump_json(), "thinking": ""},
        "done": True,
    }
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    call_llm(system_prompt="sys", user_content="usr", output_schema=Agent1Output, model="qwen3.5:397b-cloud")

    call_url = mock_post.call_args[0][0]
    call_kwargs = mock_post.call_args[1]
    assert call_url.endswith("/api/chat")
    assert call_kwargs["json"]["model"] == "qwen3.5:397b-cloud"
    assert call_kwargs["json"]["stream"] is False
    assert call_kwargs["json"]["format"] == Agent1Output.model_json_schema()
    assert call_kwargs["json"]["messages"] == [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "usr"},
    ]
