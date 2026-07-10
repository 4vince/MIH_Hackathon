"""Single entrypoint — builds and runs the Confluence IQ agent graph."""

from confluence_iq.graph import build_graph

def main() -> None:
    graph = build_graph()
    # initial state: empty; each agent loads what it needs from data/
    final_state = graph.invoke({})
    print(f"Report written to {final_state['report_path']}")

if __name__ == "__main__":
    main()
