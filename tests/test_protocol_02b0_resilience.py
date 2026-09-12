from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path
import sys
import unittest

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
PKG = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PKG
SPEC.loader.exec_module(PKG)

from tsun_local_02b0_resilience_tests.protocol_02b0 import (  # noqa: E402
    ALARM_BLOCKS,
    BLOCKS,
    DIAGNOSTIC_BLOCKS,
    Tsun02b0Client,
    build_modbus_request,
    crc16_modbus,
)
from tsun_local_02b0_resilience_tests.ap import build_ap_frame  # noqa: E402


def _modbus_reply(block: tuple[int, int, int]) -> bytes:
    function, start, end = block
    count = end - start + 1
    values = b"".join((start + index).to_bytes(2, "big") for index in range(count))
    body = bytes((0x01, function, len(values))) + values
    return body + crc16_modbus(body)


def _block_reply(block: tuple[int, int, int]) -> bytes:
    return build_ap_frame(123456, _modbus_reply(block), sensor_list=0x02B0)


class FakeReader:
    def __init__(self, data: bytes) -> None:
        self.data = bytearray(data)

    async def readexactly(self, count: int) -> bytes:
        if len(self.data) < count:
            raise asyncio.IncompleteReadError(bytes(self.data), count)
        result = bytes(self.data[:count])
        del self.data[:count]
        return result


class FailingReader:
    async def readexactly(self, count: int) -> bytes:
        raise ConnectionResetError("simulated reset")


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
    """Verify validated fast coverage plus slow read-only signature diagnostics."""

    def test_register_coverage_matches_current_read_only_plan(self) -> None:
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
                (0x03, 0x2011, 0x2013),
                (0x03, 0x2014, 0x202C),
                (0x03, 0x202D, 0x205F),
                (0x03, 0x302B, 0x302F),
            ),
        )
        self.assertTrue(
            all(function == 0x03 for function, _, _ in DIAGNOSTIC_BLOCKS)
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

        client = Tsun02b0Client("192.0.2.1", 8899, 123456)
        client._last_diagnostic_read = float("inf")
        original = asyncio.open_connection
        asyncio.open_connection = open_connection
        try:
            result = await client.async_read_all()
        finally:
            asyncio.open_connection = original

        self.assertEqual(open_calls, 1)
        self.assertEqual(result.blocks_ok, len(cycle_blocks))
        self.assertEqual(len(writer.requests), len(cycle_blocks))

    async def test_reconnects_once_and_retries_failed_fast_block(self) -> None:
        writers: list[FakeWriter] = []
        open_calls = 0
        retry_stream = b"".join(_block_reply(block) for block in (*BLOCKS, *ALARM_BLOCKS))

        async def open_connection(_host: str, _port: int):
            nonlocal open_calls
            open_calls += 1
            writer = FakeWriter()
            writers.append(writer)
            if open_calls == 1:
                return FailingReader(), writer
            return FakeReader(retry_stream), writer

        client = Tsun02b0Client("192.0.2.1", 8899, 123456)
        client._last_diagnostic_read = float("inf")
        original = asyncio.open_connection
        asyncio.open_connection = open_connection
        try:
            result = await client.async_read_all()
        finally:
            asyncio.open_connection = original

        self.assertEqual(open_calls, 2)
        self.assertEqual(result.blocks_ok, len((*BLOCKS, *ALARM_BLOCKS)))
        self.assertTrue(writers[0].closed)
        expected_first = build_modbus_request(*BLOCKS[0])
        self.assertIn(expected_first, writers[0].requests[0])
        self.assertIn(expected_first, writers[1].requests[0])


if __name__ == "__main__":
    unittest.main()
