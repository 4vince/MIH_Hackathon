"""EventBus — sync↔async event relay for real-time pipeline visualization.

Publishes events from the synchronous pipeline thread and streams them
to the async SSE endpoint via asyncio.Queue.

Thread-safe: uses ``loop.call_soon_threadsafe`` so ``publish`` can be
called from any thread (including the LangGraph pipeline thread).
"""

import asyncio
from datetime import datetime, timezone
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class EventBus:
    """Bridge between sync pipeline thread and async SSE endpoint."""

    def __init__(self) -> None:
        self._queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._loop: asyncio.AbstractEventLoop | None = None

    def _set_loop(self) -> None:
        """Capture the running event loop (called from the async subscriber)."""
        if self._loop is None:
            self._loop = asyncio.get_running_loop()

    def publish(self, event_type: str, **data: Any) -> None:
        """Called from the sync pipeline thread (or anywhere).

        Thread-safe: uses ``call_soon_threadsafe`` if a loop is registered,
        otherwise falls back to ``put_nowait`` (single-threaded usage).
        """
        event: dict[str, Any] = {
            "type": event_type,
            "timestamp": _now_iso(),
            **data,
        }
        if self._loop is not None:
            # Thread-safe path — called from pipeline thread
            self._loop.call_soon_threadsafe(self._queue.put_nowait, event)
        else:
            # Single-threaded path — direct put
            self._queue.put_nowait(event)

    async def subscribe(self):
        """Async generator — yields events as they arrive.

        Captures the running event loop on first call so that ``publish``
        can be invoked from a background thread via ``call_soon_threadsafe``.

        Usage in an SSE endpoint::

            async for event in event_bus.subscribe():
                yield dict(event)
        """
        self._set_loop()
        while True:
            event = await self._queue.get()
            yield event
