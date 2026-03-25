"""ibazel integration for ``jupyter_lab``.

Provides a long-poll Tornado handler and a stdin reader thread that
together enable automatic notebook reload and re-execution when ibazel
detects source changes.

When a ``jupyter_lab`` target has ``tags = ["ibazel_notify_changes"]``,
ibazel keeps the server process alive and sends build notifications on
stdin.  The stdin reader picks up ``IBAZEL_BUILD_COMPLETED SUCCESS``,
re-copies the rebuilt notebook into the serving directory, and signals
the long-poll handler.  Browser-side JavaScript (``ibazel_reload.js``)
polls the handler and, on receiving a signal, reverts the notebook from
disk and re-executes all cells.
"""

from __future__ import annotations

import asyncio
import json
import shutil
import sys
import threading
from pathlib import Path

import tornado.ioloop
import tornado.web

_state: dict[str, tornado.ioloop.IOLoop | None] = {"ioloop": None}


class IBazelReloadHandler(tornado.web.RequestHandler):
    """Long-poll endpoint that blocks until a notebook reload is needed.

    Browser JS fetches ``/api/rules_jupyter/wait_for_reload`` and the
    response is held open until :meth:`trigger_reload` resolves all
    waiting futures.
    """

    _waiters: set[asyncio.Future[bool]] = set()

    def data_received(self, chunk: bytes) -> None:
        """Not used (required by tornado's abstract interface)."""

    async def get(self) -> None:
        """Block until a reload is triggered, then return a JSON signal."""
        loop = asyncio.get_running_loop()
        future: asyncio.Future[bool] = loop.create_future()
        IBazelReloadHandler._waiters.add(future)
        try:
            await future
        except asyncio.CancelledError:
            return
        finally:
            IBazelReloadHandler._waiters.discard(future)
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps({"action": "reload"}))

    @classmethod
    def trigger_reload(cls) -> None:
        """Resolve all waiting long-poll futures.

        Must be called on the IO-loop thread (e.g. via
        ``ioloop.add_callback``).
        """
        waiters = list(cls._waiters)
        cls._waiters = set()
        for future in waiters:
            if not future.done():
                future.set_result(True)


class IBazelStdinReader(threading.Thread):
    """Daemon thread that reads ibazel's stdin notification protocol.

    Protocol lines::

        IBAZEL_BUILD_STARTED
        IBAZEL_BUILD_COMPLETED SUCCESS
        IBAZEL_BUILD_COMPLETED FAILURE
    """

    def __init__(self, source_path: Path, dest_path: Path) -> None:
        super().__init__(daemon=True, name="ibazel-stdin-reader")
        self._source = source_path
        self._dest = dest_path

    def run(self) -> None:
        for line in sys.stdin:
            stripped = line.strip()
            if stripped == "IBAZEL_BUILD_COMPLETED SUCCESS":
                self._on_build_success()
            elif stripped == "IBAZEL_BUILD_COMPLETED FAILURE":
                print(
                    "  [rules_jupyter] ibazel: build failed, skipping reload",
                    flush=True,
                )
            elif stripped == "IBAZEL_BUILD_STARTED":
                print("  [rules_jupyter] ibazel: build started", flush=True)

    def _on_build_success(self) -> None:
        print(
            "  [rules_jupyter] ibazel: build succeeded, reloading notebook",
            flush=True,
        )
        try:
            shutil.copy2(self._source, self._dest)
            self._dest.chmod(self._dest.stat().st_mode | 0o200)
        except OSError as exc:
            print(
                f"  [rules_jupyter] ibazel: failed to copy notebook: {exc}",
                flush=True,
            )
            return

        ioloop = _state["ioloop"]
        if ioloop is not None:
            ioloop.add_callback(IBazelReloadHandler.trigger_reload)
        else:
            print(
                "  [rules_jupyter] ibazel: IO loop not ready, skipping reload signal",
                flush=True,
            )


def setup_ibazel(source_path: Path, dest_path: Path) -> None:
    """Register the reload handler and start the stdin reader thread.

    Call before ``lab_main()`` so the monkey-patch is in place when the
    Jupyter server initialises its HTTP server.
    """
    # pylint: disable=import-outside-toplevel
    from jupyter_server.serverapp import ServerApp

    _orig = ServerApp.init_httpserver

    def _patched_init_httpserver(self):  # type: ignore[no-untyped-def]
        if hasattr(self, "web_app") and self.web_app is not None:
            self.web_app.add_handlers(
                r".*",
                [(r"/api/rules_jupyter/wait_for_reload", IBazelReloadHandler)],
            )
            _state["ioloop"] = tornado.ioloop.IOLoop.current()
            print("  [rules_jupyter] ibazel reload handler installed", flush=True)
        return _orig(self)

    ServerApp.init_httpserver = _patched_init_httpserver  # type: ignore[method-assign]

    reader = IBazelStdinReader(source_path, dest_path)
    reader.start()
    print("  [rules_jupyter] ibazel stdin reader started", flush=True)
