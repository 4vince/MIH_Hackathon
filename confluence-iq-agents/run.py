"""Single entrypoint — builds and runs the Confluence IQ agent graph."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "src"))

from confluence_iq.graph import build_graph  # noqa: E402
from confluence_iq.logging_setup import setup_logging  # noqa: E402


def main() -> None:
    logger = setup_logging()
    logger.info("Confluence IQ Agents — starting pipeline")
    graph = build_graph()
    final_state = graph.invoke({})
    logger.info("Report written to %s", final_state["report_path"])


if __name__ == "__main__":
    main()
