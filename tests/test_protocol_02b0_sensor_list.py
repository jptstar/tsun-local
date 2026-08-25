# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Regression test for the explicit Solarman 02B0 sensor-list selector."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


PROTOCOLS_PATH = (
    Path(__file__).parents[1]
    / "custom_components"
    / "tsun_local"
    / "protocols"
)
SPEC = importlib.util.spec_from_file_location(
    "tsun_local_protocol_02b0_sensor_list_tests",
    PROTOCOLS_PATH / "__init__.py",
    submodule_search_locations=[str(PROTOCOLS_PATH)],
)
assert SPEC is not None and SPEC.loader is not None
PROTOCOLS = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PROTOCOLS
SPEC.loader.exec_module(PROTOCOLS)

from tsun_local_protocol_02b0_sensor_list_tests.ap import checksum_ap  # noqa: E402
from tsun_local_protocol_02b0_sensor_list_tests.protocol_02b0 import (  # noqa: E402
    SENSOR_LIST,
    Tsun02b0Client,
    crc16_modbus,
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


class Protocol02b0SensorListTests(unittest.IsolatedAsyncioTestCase):
    """Ensure every 02B0 read identifies the inverter family explicitly."""

    async def test_client_sends_sensor_list_02b0(self) -> None:
        body = bytes.fromhex("01 03 02 00 01")
        reply = _build_ap_reply(body + crc16_modbus(body))
        requests: list[bytes] = []

        class FakeReader:
            def __init__(self) -> None:
                self.offset = 0

            async def readexactly(self, size: int) -> bytes:
                result = reply[self.offset : self.offset + size]
                self.offset += size
                return result

        class FakeWriter:
            def write(self, request: bytes) -> None:
                requests.append(request)

            async def drain(self) -> None:
                pass

            def close(self) -> None:
                pass

            async def wait_closed(self) -> None:
                pass

        async def open_connection(_host: str, _port: int):
            return FakeReader(), FakeWriter()

        module = sys.modules[
            "tsun_local_protocol_02b0_sensor_list_tests.protocol_02b0"
        ]
        with patch.object(module.asyncio, "open_connection", new=open_connection):
            client = Tsun02b0Client("192.0.2.10", 8899, 0x12345678)
            registers = await client._read_block((0x03, 0x3000, 0x3000))

        self.assertEqual(SENSOR_LIST, 0x02B0)
        self.assertEqual(registers, {0x3000: 1})
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0][12:14], b"\xB0\x02")


if __name__ == "__main__":
    unittest.main()
