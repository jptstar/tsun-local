# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Regression tests for resilient TSUN 1097 polling."""

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
    "tsun_local_1097_resilience_tests",
    PROTOCOLS_PATH / "__init__.py",
    submodule_search_locations=[str(PROTOCOLS_PATH)],
)
assert SPEC is not None and SPEC.loader is not None
PROTOCOLS = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PROTOCOLS
SPEC.loader.exec_module(PROTOCOLS)

from tsun_local_1097_resilience_tests.ap import checksum_ap  # noqa: E402
from tsun_local_1097_resilience_tests.protocol_1097 import (  # noqa: E402
    BLOCKS,
    Tsun1097Client,
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

    set_register(0x1100, 2)
    set_register(0x1200, 2300)
    set_register(0x1201, 100)
    set_register(0x1202, 500)
    set_register(0x1209, 5000)
    set_register(0x1210, 800)
    set_register(0x1212, 125)
    set_register(0x1213, 0)
    set_register(0x1214, 12345)
    set_register(0x1302, 410)
    set_register(0x1303, 100)
    set_register(0x1304, 400)
    set_register(0x1305, 0)
    set_register(0x1306, 100)
    set_register(0x1307, 0)
    set_register(0x1308, 5000)

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


class Protocol1097ResilienceTests(unittest.IsolatedAsyncioTestCase):
    """Verify persistent sessions, retry and daily-counter stability."""

    def test_uses_proxy_aligned_fast_blocks(self) -> None:
        self.assertEqual(
            BLOCKS,
            (
                (0x03, 0x1100, 0x110F),
                (0x03, 0x1200, 0x122F),
                (0x03, 0x1300, 0x133F),
            ),
        )

    async def test_one_healthy_tcp_session_serves_complete_fast_cycle(self) -> None:
        stream = b"".join(_block_reply(block) for block in BLOCKS)
        writer = FakeWriter()
        open_calls = 0

        async def open_connection(_host: str, _port: int):
            nonlocal open_calls
            open_calls += 1
            return FakeReader(stream), writer

        module = sys.modules[
            "tsun_local_1097_resilience_tests.protocol_1097"
        ]
        with patch.object(
            module.asyncio, "open_connection", new=open_connection
        ):
            client = Tsun1097Client("192.0.2.10", 8899, 123456)
            client._last_diagnostic_read = time.monotonic()
            result = await client.async_read_all()

        self.assertEqual(open_calls, 1)
        self.assertEqual(len(writer.requests), 3)
        self.assertEqual(result.blocks_ok, 3)
        self.assertAlmostEqual(result.measurements["ac_energy_today"], 1.25)
        self.assertAlmostEqual(result.measurements["pv1_energy_today"], 1.0)

    async def test_reconnects_once_and_retries_failed_block(self) -> None:
        good_stream = b"".join(_block_reply(block) for block in BLOCKS)
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

        module = sys.modules[
            "tsun_local_1097_resilience_tests.protocol_1097"
        ]
        with patch.object(
            module.asyncio, "open_connection", new=open_connection
        ):
            client = Tsun1097Client("192.0.2.10", 8899, 123456)
            client._last_diagnostic_read = time.monotonic()
            result = await client.async_read_all()

        self.assertEqual(open_calls, 2)
        self.assertTrue(writers[0].closed)
        self.assertEqual(result.blocks_ok, 3)

    def test_transient_daily_zero_is_not_published(self) -> None:
        client = Tsun1097Client("192.0.2.10", 8899, 123456)
        first = client._stabilize_daily_energy(
            {"ac_energy_today": 4.2, "pv1_energy_today": 4.0}
        )
        transient = client._stabilize_daily_energy(
            {"ac_energy_today": 0.0, "pv1_energy_today": 0.0}
        )
        recovered = client._stabilize_daily_energy(
            {"ac_energy_today": 4.3, "pv1_energy_today": 4.1}
        )

        self.assertEqual(first["ac_energy_today"], 4.2)
        self.assertEqual(transient["ac_energy_today"], 4.2)
        self.assertEqual(transient["pv1_energy_today"], 4.0)
        self.assertEqual(recovered["ac_energy_today"], 4.3)

    def test_real_daily_reset_is_accepted_on_second_lower_sample(self) -> None:
        client = Tsun1097Client("192.0.2.10", 8899, 123456)
        client._stabilize_daily_energy({"ac_energy_today": 5.0})
        first_lower = client._stabilize_daily_energy({"ac_energy_today": 0.0})
        second_lower = client._stabilize_daily_energy({"ac_energy_today": 0.1})

        self.assertEqual(first_lower["ac_energy_today"], 5.0)
        self.assertEqual(second_lower["ac_energy_today"], 0.1)
