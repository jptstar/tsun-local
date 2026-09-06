# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Regression tests for resilient TSUN 02B0 polling."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import time
import unittest
from unittest.mock import patch


PROTOCOLS_PATH = (
    Path(__file__).parents[1]
    / "custom_components"
    / "tsun_local"
    / "protocols"
)
SPEC = importlib.util.spec_from_file_location(
    "tsun_local_02b0_resilience_tests",
    PROTOCOLS_PATH / "__init__.py",
    submodule_search_locations=[str(PROTOCOLS_PATH)],
)
assert SPEC is not None and SPEC.loader is not None
PROTOCOLS = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PROTOCOLS
SPEC.loader.exec_module(PROTOCOLS)

from tsun_local_02b0_resilience_tests.ap import checksum_ap  # noqa: E402
from tsun_local_02b0_resilience_tests.protocol_02b0 import (  # noqa: E402
    ALARM_BLOCKS,
    BLOCKS,
    DIAGNOSTIC_BLOCKS,
    Tsun02b0Client,
    crc16_modbus,
)


def _build_ap_reply(payload: bytes) -> bytes:
    """Build a synthetic valid AP response around a protocol payload."""
    length = 14 + len(payload)
    scope = (
        length.to_bytes(2, "little")
        + b"\x10\x15\x00\x01"
        + b"\x78\x56\x34\x12"
        + b"\x02\x01"
        + bytes(12)
        + payload
    )
    return b"\xA5" + scope + bytes((checksum_ap(scope), 0x15))


def _block_reply(block: tuple[int, int, int]) -> bytes:
    function, start, end = block
    values = bytearray((end - start + 1) * 2)

    def set_register(address: int, value: int) -> None:
        if start <= address <= end:
            offset = (address - start) * 2
            values[offset : offset + 2] = value.to_bytes(2, "big")

    set_register(0x3000, 1)
    set_register(0x3008, 0x4039)
    set_register(0x3009, 2301)
    set_register(0x300A, 123)
    set_register(0x300B, 5000)
    set_register(0x300C, 65)
    set_register(0x300E, 800)
    set_register(0x300F, 4567)
    set_register(0x3010, 410)
    set_register(0x3011, 222)
    set_register(0x3012, 910)
    set_register(0x301C, 125)
    set_register(0x301D, 0)
    set_register(0x301E, 2345)
    set_register(0x301F, 150)
    set_register(0x3020, 0)
    set_register(0x3021, 12345)
    body = bytes((1, function, len(values))) + bytes(values)
    return _build_ap_reply(body + crc16_modbus(body))


class FakeReader:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload
        self.offset = 0

    async def readexactly(self, size: int) -> bytes:
        result = self.payload[self.offset : self.offset + size]
        self.offset += size
        if len(result) != size:
            raise EOFError("synthetic stream exhausted")
        return result


class FakeWriter:
    def __init__(self) -> None:
        self.requests: list[bytes] = []
        self.closed = False

    def write(self, request: bytes) -> None:
        self.requests.append(request)

    async def drain(self) -> None:
        pass

    def close(self) -> None:
        self.closed = True

    async def wait_closed(self) -> None:
        pass


class Protocol02b0ResilienceTests(unittest.IsolatedAsyncioTestCase):
    """Verify unchanged register coverage with a resilient session lifecycle."""

    def test_register_coverage_is_unchanged(self) -> None:
        self.assertEqual(
            BLOCKS,
            ((0x03, 0x3008, 0x301E), (0x03, 0x301F, 0x302A)),
        )
        self.assertEqual(ALARM_BLOCKS, ((0x03, 0x3000, 0x3006),))
        self.assertEqual(
            DIAGNOSTIC_BLOCKS,
            (
                (0x03, 0x2007, 0x2007),
                (0x03, 0x2000, 0x2010),
                (0x03, 0x2014, 0x202C),
            ),
        )

    async def test_one_healthy_session_serves_fast_and_alarm_reads(self) -> None:
        cycle_blocks = (*BLOCKS, *ALARM_BLOCKS)
        stream = b"".join(_block_reply(block) for block in cycle_blocks)
        writer = FakeWriter()
        open_calls = 0

        async def open_connection(_host: str, _port: int):
            nonlocal open_calls
            open_calls += 1
            return FakeReader(stream), writer

        module = sys.modules["tsun_local_02b0_resilience_tests.protocol_02b0"]
        with patch.object(module.asyncio, "open_connection", new=open_connection):
            client = Tsun02b0Client("192.0.2.10", 8899, 123456)
            client._last_diagnostic_read = time.monotonic()
            result = await client.async_read_all()

        self.assertEqual(open_calls, 1)
        self.assertEqual(len(writer.requests), 3)
        self.assertEqual(result.blocks_ok, 3)
        self.assertAlmostEqual(result.measurements["ac_energy_today"], 1.25)
        self.assertAlmostEqual(result.measurements["pv1_energy_total"], 123.45)

    async def test_reconnects_once_and_retries_failed_fast_block(self) -> None:
        bad = bytearray(_block_reply(BLOCKS[0]))
        bad[-2] ^= 0x01
        good_stream = b"".join(
            _block_reply(block) for block in (*BLOCKS, *ALARM_BLOCKS)
        )
        readers = iter((FakeReader(bytes(bad)), FakeReader(good_stream)))
        writers = [FakeWriter(), FakeWriter()]
        open_calls = 0

        async def open_connection(_host: str, _port: int):
            nonlocal open_calls
            writer = writers[open_calls]
            open_calls += 1
            return next(readers), writer

        module = sys.modules["tsun_local_02b0_resilience_tests.protocol_02b0"]
        with patch.object(module.asyncio, "open_connection", new=open_connection):
            client = Tsun02b0Client("192.0.2.10", 8899, 123456)
            client._last_diagnostic_read = time.monotonic()
            result = await client.async_read_all()

        self.assertEqual(open_calls, 2)
        self.assertTrue(writers[0].closed)
        self.assertEqual(result.blocks_ok, 3)
