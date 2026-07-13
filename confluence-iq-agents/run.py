"""Single entrypoint — builds and runs the Confluence IQ agent graph."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "src"))

from confluence_iq.graph import build_graph  # noqa: E402
from confluence_iq.logging_setup import setup_logging  # noqa: E402


def main() -> None:
    logger = setup_logging()
    logger.info("Confluence IQ Agents — starting pipeline")

    try:
        graph = build_graph()
        final_state = graph.invoke({})
    except Exception as exc:
        # Broad catch is deliberate: this is the pipeline's only external-network
        # boundary (the live LLM endpoint), and a live demo run should degrade to
        # a clean message instead of a raw traceback. Full detail still reaches
        # transcript.log via exc_info=True.
        logger.error("Pipeline failed: %s", exc)
        logger.debug("Full traceback:", exc_info=True)
        print(
            f"\nPipeline failed: {exc}\n"
            "See output/transcript.log for full details.\n"
            "If this happens during the demo, use a previously generated report from output/ instead.",
            file=sys.stderr,
        )
        sys.exit(1)

    logger.info("Report written to %s", final_state["report_path"])


if __name__ == "__main__":
    main()
