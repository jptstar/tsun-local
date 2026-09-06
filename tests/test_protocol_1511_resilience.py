# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Regression tests for resilient TSUN 1511 polling."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import time
import unittest
from unittest.mock import patch

PROTOCOLS_PATH = Path(__file__).parents[1] / "custom_components" / "tsun_local" / "protocols"
SPEC = importlib.util.spec_from_file_location(
    "tsun_local_1511_resilience_tests",
    PROTOCOLS_PATH / "__init__.py",
    submodule_search_locations=[str(PROTOCOLS_PATH)],
)
assert SPEC is not None and SPEC.loader is not None
PROTOCOLS = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PROTOCOLS
SPEC.loader.exec_module(PROTOCOLS)

from tsun_local_1511_resilience_tests.ap import checksum_ap  # noqa: E402
from tsun_local_1511_resilience_tests.protocol_1511 import (  # noqa: E402
    ALARM_BLOCKS,
    BLOCKS,
    DIAGNOSTIC_BLOCKS,
    Tsun1511Client,
    crc16_1511,
)


def _build_ap_reply(payload: bytes) -> bytes:
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


def _block_reply(block: tuple[int, int, int, int]) -> bytes:
    address_tag, function, start, end = block
    values = bytearray((end - start + 1) * 2)

    def set_register(address: int, value: int) -> None:
        if start <= address <= end:
            offset = (address - start) * 2
            values[offset : offset + 2] = value.to_bytes(2, "little")

    set_register(0x0BB8, 1)
    set_register(0x0BC4, 2300)
    set_register(0x0BC5, 100)
    set_register(0x0BC7, 5000)
    set_register(0x0BC9, 65)
    set_register(0x0BCC, 3000)
    set_register(0x0BCD, 5000)
    set_register(0x0BCE, 125)
    set_register(0x0BCF, 0)
    set_register(0x0BD0, 12345)
    set_register(0x0E10, 410)
    set_register(0x0E11, 100)
    set_register(0x0E12, 400)
    set_register(0x0E15, 100)
    set_register(0x0E28, 0)
    set_register(0x0E29, 5000)

    body = (
        bytes((0x7E, address_tag, function | 0x80, 0x01))
        + start.to_bytes(2, "big")
        + len(values).to_bytes(2, "big")
        + bytes(values)
    )
    return _build_ap_reply(body + crc16_1511(body[1:]))


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


class Protocol1511ResilienceTests(unittest.IsolatedAsyncioTestCase):
    def test_validated_register_coverage_is_unchanged(self) -> None:
        self.assertEqual(
            BLOCKS,
            (
                (0xA1, 0x01, 0x0BB8, 0x0BD0),
                (0xA3, 0x03, 0x0E10, 0x0E2D),
                (0xA4, 0x04, 0x0ED8, 0x0EF5),
            ),
        )
        self.assertEqual(ALARM_BLOCKS, ((0xA2, 0x02, 0x0CE4, 0x0CE7),))
        self.assertEqual(
            DIAGNOSTIC_BLOCKS,
            (
                (0xA1, 0x01, 0x0BB8, 0x0BD7),
                (0xA1, 0x21, 0x07D0, 0x082F),
            ),
        )

    async def test_one_healthy_tcp_session_serves_fast_cycle(self) -> None:
        stream = b"".join(_block_reply(block) for block in (*BLOCKS, *ALARM_BLOCKS))
        writer = FakeWriter()
        open_calls = 0

        async def open_connection(_host: str, _port: int):
            nonlocal open_calls
            open_calls += 1
            return FakeReader(stream), writer

        module = sys.modules["tsun_local_1511_resilience_tests.protocol_1511"]
        with patch.object(module.asyncio, "open_connection", new=open_connection):
            client = Tsun1511Client("192.0.2.10", 8899, 123456)
            client._last_diagnostic_read = time.monotonic()
            result = await client.async_read_all()

        self.assertEqual(open_calls, 1)
        self.assertEqual(len(writer.requests), 4)
        self.assertEqual(result.blocks_ok, 4)
        self.assertAlmostEqual(result.measurements["ac_energy_today"], 1.25)

    async def test_reconnects_once_and_retries_failed_block(self) -> None:
        good_stream = b"".join(_block_reply(block) for block in (*BLOCKS, *ALARM_BLOCKS))
        bad_first = bytearray(_block_reply(BLOCKS[0]))
        bad_first[-2] ^= 0x01
        readers = iter((FakeReader(bytes(bad_first)), FakeReader(good_stream)))
        writers = [FakeWriter(), FakeWriter()]
        open_calls = 0

        async def open_connection(_host: str, _port: int):
            nonlocal open_calls
            writer = writers[open_calls]
            open_calls += 1
            return next(readers), writer

        module = sys.modules["tsun_local_1511_resilience_tests.protocol_1511"]
        with patch.object(module.asyncio, "open_connection", new=open_connection):
            client = Tsun1511Client("192.0.2.10", 8899, 123456)
            client._last_diagnostic_read = time.monotonic()
            result = await client.async_read_all()

        self.assertEqual(open_calls, 2)
        self.assertTrue(writers[0].closed)
        self.assertEqual(result.blocks_ok, 4)
