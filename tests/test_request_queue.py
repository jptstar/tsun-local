# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Verify per-logger FIFO request serialization."""

from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).parents[1]
MODULE_PATH = ROOT / "custom_components" / "tsun_local" / "request_queue.py"
SPEC = importlib.util.spec_from_file_location("tsun_local_request_queue_tests", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
REQUEST_QUEUE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = REQUEST_QUEUE
SPEC.loader.exec_module(REQUEST_QUEUE)


class LoggerRequestQueueTests(unittest.IsolatedAsyncioTestCase):
    """Protect FIFO ordering and independent logger queues."""

    async def test_requests_are_served_fifo(self) -> None:
        queue = REQUEST_QUEUE.LoggerRequestQueue()
        order: list[int] = []
        first_started = asyncio.Event()
        release_first = asyncio.Event()

        async def worker(index: int) -> None:
            async with queue:
                order.append(index)
                if index == 1:
                    first_started.set()
                    await release_first.wait()

        first = asyncio.create_task(worker(1))
        await first_started.wait()
        second = asyncio.create_task(worker(2))
        third = asyncio.create_task(worker(3))
        await asyncio.sleep(0)
        self.assertEqual(queue.waiting, 2)
        self.assertEqual(queue.depth, 3)

        release_first.set()
        await asyncio.gather(first, second, third)
        self.assertEqual(order, [1, 2, 3])
        self.assertEqual(queue.depth, 0)

    async def test_independent_queues_do_not_block_each_other(self) -> None:
        first_queue = REQUEST_QUEUE.LoggerRequestQueue()
        second_queue = REQUEST_QUEUE.LoggerRequestQueue()
        first_entered = asyncio.Event()
        second_entered = asyncio.Event()
        release_first = asyncio.Event()

        async def hold_first() -> None:
            async with first_queue:
                first_entered.set()
                await release_first.wait()

        async def use_second() -> None:
            async with second_queue:
                second_entered.set()

        task = asyncio.create_task(hold_first())
        await first_entered.wait()
        await use_second()
        self.assertTrue(second_entered.is_set())
        release_first.set()
        await task


if __name__ == "__main__":
    unittest.main()
