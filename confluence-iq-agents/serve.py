"""FastAPI server — dashboard + SSE + pipeline launcher.

Usage:
    python serve.py
    # Open http://localhost:8000
"""

import json
import pathlib
import re
import sys
import threading
import time
from datetime import datetime, timezone as tz
from contextlib import asynccontextmanager

# ── Ensure ``src`` is on the path for direct ``python serve.py`` ──
_HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE / "src"))

import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from sse_starlette.sse import EventSourceResponse

from confluence_iq.event_bus import EventBus
from confluence_iq.graph import build_graph
from confluence_iq.logging_setup import setup_logging

# ── Globals ───────────────────────────────────────────────────────
event_bus: EventBus | None = None
OUTPUT_DIR = _HERE / "output"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Startup: create the EventBus and logging. Shutdown: no-op."""
    global event_bus
    event_bus = EventBus()
    setup_logging()
    print("Dashboard ready — open http://localhost:8000")
    yield


app = FastAPI(title="Confluence IQ Agents — Dashboard", lifespan=lifespan)


# ── Serve the dashboard HTML ─────────────────────────────────────
@app.get("/")
async def _dashboard() -> HTMLResponse:
    html_path = _HERE / "src" / "confluence_iq" / "ui" / "dashboard.html"
    if not html_path.exists():
        return HTMLResponse("dashboard.html not found", status_code=500)
    return HTMLResponse(html_path.read_text(encoding="utf-8"))


# ── Report listing endpoint (for history/trends) ─────────────────
_REPORT_METRICS_RE = re.compile(
    r"covering\s+(\d+)\s+customer segment"
    r"|(\d+)\s+keyword opportunit"
    r"|(\d+)\s+content gap"
    r"|(\d+)\s+prioritized recommendation"
)


def _extract_metrics(text: str) -> dict:
    """Extract summary metrics from a report's executive summary."""
    metrics = {}
    for match in _REPORT_METRICS_RE.finditer(text):
        for i, g in enumerate(match.groups(), 1):
            if g is not None:
                keys = ["segments", "keywords", "gaps", "recommendations"]
                metrics[keys[i - 1]] = int(g)
    return metrics


@app.get("/api/reports", response_model=None)
async def _list_reports():
    """List all reports with metadata, newest first."""
    reports = []
    pattern = "report_*.md"
    for f in sorted(OUTPUT_DIR.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True):
        mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=tz.utc)
        content = f.read_text(encoding="utf-8")
        metrics = _extract_metrics(content)
        reports.append({
            "filename": f.name,
            "size": f.stat().st_size,
            "modified": mtime.isoformat(),
            "metrics": metrics,
        })
    return reports


# ── SSE event stream ─────────────────────────────────────────────
@app.get("/api/events")
async def _events():
    async def event_generator():
        async for event in event_bus.subscribe():
            yield {"event": "message", "data": json.dumps(event)}

    return EventSourceResponse(event_generator())


# ── Trigger pipeline run ─────────────────────────────────────────
@app.post("/api/run", response_model=None)
async def _run_pipeline():
    if event_bus is None:
        return JSONResponse({"error": "EventBus not initialized"}, status_code=500)

    def _run() -> None:
        """Target for the background thread — builds graph and invokes it."""
        graph = build_graph(event_bus)
        event_bus.publish("graph_start", nodes=[str(n) for n in graph.nodes])
        t0 = time.time()
        try:
            result = graph.invoke({})
            elapsed = round(time.time() - t0, 2)
            report_path = result.get("report_path", "")
            event_bus.publish("graph_end", elapsed_seconds=elapsed)
            if report_path:
                event_bus.publish(
                    "report_written",
                    filename=pathlib.Path(report_path).name,
                    path=report_path,
                )
        except Exception as exc:
            elapsed = round(time.time() - t0, 2)
            event_bus.publish("graph_end", elapsed_seconds=elapsed, error=str(exc))

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    return {"status": "started"}


# ── Serve generated reports ──────────────────────────────────────
@app.get("/api/report/{filename:path}", response_model=None)
async def _get_report(filename: str):
    safe_path = (OUTPUT_DIR / filename).resolve()
    if not str(safe_path).startswith(str(OUTPUT_DIR.resolve())):
        return JSONResponse({"error": "invalid path"}, status_code=400)
    if not safe_path.exists():
        return JSONResponse({"error": "not found"}, status_code=404)
    return FileResponse(safe_path, media_type="text/markdown")


# ── Entrypoint ───────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run("serve:app", host="0.0.0.0", port=8000, reload=True)
