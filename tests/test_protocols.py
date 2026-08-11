# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Unit tests for the protocol-independent TSUN Local decoders."""

from __future__ import annotations

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
    "tsun_local_protocol_tests",
    PROTOCOLS_PATH / "__init__.py",
    submodule_search_locations=[str(PROTOCOLS_PATH)],
)
assert SPEC is not None and SPEC.loader is not None
PROTOCOLS = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PROTOCOLS
SPEC.loader.exec_module(PROTOCOLS)

from tsun_local_protocol_tests.ap import (  # noqa: E402
    TsunProtocolError,
    checksum_ap,
    parse_ap_frame,
)
from tsun_local_protocol_tests.protocol_02b0 import (  # noqa: E402
    build_modbus_request,
    crc16_modbus,
    decode_measurements as decode_02b0,
    detect_pv_count as detect_02b0_pv_count,
    parse_modbus_response,
)
from tsun_local_protocol_tests.protocol_1511 import (  # noqa: E402
    build_1511_request,
    detect_pv_count as detect_1511_pv_count,
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


class ApFrameTests(unittest.TestCase):
    """Verify the common AP envelope."""

    def test_extracts_protocol_payload(self) -> None:
        payload = bytes.fromhex("0103041234ABCD0020")
        self.assertEqual(parse_ap_frame(_build_ap_reply(payload)), payload)

    def test_rejects_bad_checksum(self) -> None:
        frame = bytearray(_build_ap_reply(b"\x01\x03\x00"))
        frame[-2] ^= 0x01
        with self.assertRaises(TsunProtocolError):
            parse_ap_frame(bytes(frame))


class Protocol02b0Tests(unittest.TestCase):
    """Verify standard Modbus framing and 02B0 register decoding."""

    def test_builds_official_measurement_requests(self) -> None:
        self.assertEqual(
            build_modbus_request(0x03, 0x3009, 0x301E),
            bytes.fromhex("01 03 30 09 00 16 1B 06"),
        )
        self.assertEqual(
            build_modbus_request(0x03, 0x301F, 0x302A),
            bytes.fromhex("01 03 30 1F 00 0C 7B 09"),
        )

    def test_parses_big_endian_registers(self) -> None:
        body = bytes.fromhex("01 03 04 12 34 AB CD")
        response = body + crc16_modbus(body)
        self.assertEqual(
            parse_modbus_response(response, 0x03, 0x3009, 0x300A),
            {0x3009: 0x1234, 0x300A: 0xABCD},
        )

    def test_decodes_scaling_type5_and_total_dc_power(self) -> None:
        registers = {address: 0 for address in range(0x3009, 0x302B)}
        registers.update(
            {
                0x3009: 2301,
                0x300A: 123,
                0x300B: 5000,
                0x300F: 4567,
                0x301C: 125,
                0x301D: 1,
                0x301E: 2345,
                0x3010: 410,
                0x3011: 222,
                0x3012: 910,
                0x301F: 150,
                0x3020: 0,
                0x3021: 12345,
                0x3013: 420,
                0x3014: 111,
                0x3015: 800,
                0x3028: 25,
            }
        )
        data = decode_02b0(registers, 4)
        self.assertAlmostEqual(data["ac_voltage"], 230.1)
        self.assertAlmostEqual(data["ac_frequency"], 50.0)
        self.assertAlmostEqual(data["ac_energy_total"], 678.81)
        self.assertAlmostEqual(data["pv1_energy_total"], 123.45)
        self.assertEqual(data["dc_power_total"], 171.0)

    def test_detects_highest_populated_pv_input(self) -> None:
        registers: dict[int, int] = {}
        self.assertEqual(detect_02b0_pv_count(registers), 1)
        registers[0x3014] = 1
        self.assertEqual(detect_02b0_pv_count(registers), 2)
        registers[0x3014] = 0
        registers[0x3029] = 1
        self.assertEqual(detect_02b0_pv_count(registers), 4)
        registers[0x3029] = 0xFFFF
        self.assertEqual(detect_02b0_pv_count(registers), 1)


class Protocol1511Tests(unittest.TestCase):
    """Protect the validated 1511 request and dynamic PV discovery."""

    def test_builds_validated_ac_request(self) -> None:
        self.assertEqual(
            build_1511_request(0xA1, 0x01, 0x0BB8, 0x0BD0),
            bytes.fromhex("A1 01 00 0B B8 00 02 00 19 C1 FF"),
        )

    def test_detects_highest_populated_pv_input(self) -> None:
        self.assertEqual(detect_1511_pv_count({}), 1)
        self.assertEqual(detect_1511_pv_count({0x0EF2: 1}), 5)
        self.assertEqual(detect_1511_pv_count({0x0EF4: 0xFFFF}), 1)


if __name__ == "__main__":
    unittest.main()
