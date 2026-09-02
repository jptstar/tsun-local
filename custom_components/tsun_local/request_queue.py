# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Per-logger FIFO request serialization for TSUN Local."""

from __future__ import annotations

import asyncio


class LoggerRequestQueue:
    """Serialize local requests for one logger in FIFO order.

    ``asyncio.Lock`` wakes blocked acquirers fairly, so wrapping one lock per
    logger gives us an explicit FIFO gate without coupling unrelated devices.
    The small counters are diagnostics only and do not influence scheduling.
    """

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._waiting = 0
        self._active = False

    async def __aenter__(self) -> LoggerRequestQueue:
        self._waiting += 1
        try:
            await self._lock.acquire()
        finally:
            self._waiting -= 1
        self._active = True
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: object | None,
    ) -> None:
        self._active = False
        self._lock.release()

    @property
    def waiting(self) -> int:
        """Return the number of requests currently queued behind the active one."""
        return self._waiting

    @property
    def depth(self) -> int:
        """Return active plus waiting request count."""
        return self._waiting + int(self._active)

    def locked(self) -> bool:
        """Return whether one request currently owns the queue."""
        return self._lock.locked()
