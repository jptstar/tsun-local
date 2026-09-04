# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Verify defensive TCP stream closing used by all TSUN transports."""

from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path
import unittest


AP_PATH = (
    Path(__file__).parents[1]
    / "custom_components"
    / "tsun_local"
    / "protocols"
    / "ap.py"
)
SPEC = importlib.util.spec_from_file_location("tsun_local_ap_close_tests", AP_PATH)
assert SPEC is not None and SPEC.loader is not None
AP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AP)


class _Writer:
    def __init__(self, wait_error: Exception | None = None) -> None:
        self.closed = False
        self.wait_error = wait_error

    def close(self) -> None:
        self.closed = True

    async def wait_closed(self) -> None:
        if self.wait_error is not None:
            raise self.wait_error


class _HangingWriter(_Writer):
    async def wait_closed(self) -> None:
        await asyncio.sleep(60)


class StreamCloseTests(unittest.IsolatedAsyncioTestCase):
    async def test_successful_close(self) -> None:
        writer = _Writer()
        await AP.async_close_writer(writer)
        self.assertTrue(writer.closed)

    async def test_close_oserror_is_non_fatal(self) -> None:
        writer = _Writer(OSError("socket already gone"))
        await AP.async_close_writer(writer)
        self.assertTrue(writer.closed)

    async def test_hanging_close_is_bounded(self) -> None:
        original_timeout = AP.STREAM_CLOSE_TIMEOUT
        AP.STREAM_CLOSE_TIMEOUT = 0.01
        try:
            writer = _HangingWriter()
            await AP.async_close_writer(writer)
        finally:
            AP.STREAM_CLOSE_TIMEOUT = original_timeout
        self.assertTrue(writer.closed)


if __name__ == "__main__":
    unittest.main()
