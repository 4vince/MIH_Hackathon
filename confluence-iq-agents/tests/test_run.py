"""Tests for run.py's error handling around the live LLM/graph invocation."""

import importlib.util
import pathlib
import sys
from unittest.mock import MagicMock, patch

import httpx
import pytest

_RUN_PY_PATH = pathlib.Path(__file__).resolve().parent.parent / "run.py"
_spec = importlib.util.spec_from_file_location("run", _RUN_PY_PATH)
run = importlib.util.module_from_spec(_spec)
sys.modules["run"] = run
_spec.loader.exec_module(run)


@patch("run.build_graph")
def test_main_exits_cleanly_on_network_error(mock_build_graph):
    mock_graph = MagicMock()
    mock_graph.invoke.side_effect = httpx.ConnectError("connection refused")
    mock_build_graph.return_value = mock_graph

    with pytest.raises(SystemExit) as exc_info:
        run.main()

    assert exc_info.value.code == 1


@patch("run.build_graph")
def test_main_exits_cleanly_on_unexpected_error(mock_build_graph):
    mock_graph = MagicMock()
    mock_graph.invoke.side_effect = RuntimeError("something unexpected broke")
    mock_build_graph.return_value = mock_graph

    with pytest.raises(SystemExit) as exc_info:
        run.main()

    assert exc_info.value.code == 1


@patch("run.build_graph")
def test_main_completes_normally_on_success(mock_build_graph):
    mock_graph = MagicMock()
    mock_graph.invoke.return_value = {"report_path": "output/report_20260101_000000.md"}
    mock_build_graph.return_value = mock_graph

    run.main()  # should not raise or call sys.exit
