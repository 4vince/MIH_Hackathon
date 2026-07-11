"""Tests for data/prompt loaders."""

from confluence_iq.tools.loaders import load_prompt, load_raw_corpus_text


def test_load_prompt_returns_grounding_rule():
    prompt = load_prompt("data_synthesizer")
    assert "GROUNDING RULE" in prompt


def test_load_raw_corpus_text_includes_customer_and_site_data():
    corpus = load_raw_corpus_text()
    assert "Basil Ford" in corpus
    assert "trade-in" in corpus.lower() or "trade-in value" in corpus
