"""Single entrypoint — builds and runs the Confluence IQ agent graph."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "src"))

from confluence_iq.graph import build_graph  # noqa: E402


def main() -> None:
    graph = build_graph()
    final_state = graph.invoke({})
    print(f"Report written to {final_state['report_path']}")


if __name__ == "__main__":
    main()
