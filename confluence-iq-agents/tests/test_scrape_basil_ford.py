"""Tests for the pre-scrape script's per-site loop and blocked-page handling."""

from unittest.mock import patch

from scripts.scrape_basil_ford import _scrape_site


@patch("scripts.scrape_basil_ford._write_page")
@patch("scripts.scrape_basil_ford._scrape_page")
def test_scrape_site_skips_blocked_pages_without_crashing(mock_scrape_page, mock_write_page, tmp_path):
    # First page blocked (returns None), remaining 8 succeed.
    mock_scrape_page.side_effect = [None] + ["page text"] * 8

    site = {"base_url": "https://example.com", "label": "Example", "location": "Test City"}
    live_count, skipped_count = _scrape_site("example_com", site, tmp_path)

    assert skipped_count == 1
    assert live_count == 8
    assert mock_write_page.call_count == 8
