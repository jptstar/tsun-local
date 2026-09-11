# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Regression tests for the optional TSUN 0xFF Modbus reply marker."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


AP_PATH = (
    Path(__file__).parents[1]
    / "custom_components"
    / "tsun_local"
    / "protocols"
    / "ap.py"
)
SPEC = importlib.util.spec_from_file_location("tsun_local_ap_prefix_tests", AP_PATH)
assert SPEC is not None and SPEC.loader is not None
AP = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = AP
SPEC.loader.exec_module(AP)


def _build_ap_reply(payload: bytes) -> bytes:
    """Build a synthetic valid AP response around one protocol payload."""
    length = 14 + len(payload)
    scope = (
        length.to_bytes(2, "little")
        + b"\x10\x15\x00\x01"
        + b"\x78\x56\x34\x12"
        + b"\x02\x01"
        + bytes(12)
        + payload
    )
    return b"\xA5" + scope + bytes((AP.checksum_ap(scope), 0x15))


class ModbusPrefixTests(unittest.TestCase):
    """Accept the field-observed marker without weakening AP validation."""

    def test_keeps_normal_modbus_reply_unchanged(self) -> None:
        payload = bytes.fromhex("01 03 02 12 34 B5 33")
        self.assertEqual(AP.parse_ap_frame(_build_ap_reply(payload)), payload)

    def test_strips_one_ff_before_read_holding_registers_reply(self) -> None:
        payload = bytes.fromhex("01 03 02 12 34 B5 33")
        self.assertEqual(
            AP.parse_ap_frame(_build_ap_reply(b"\xFF" + payload)),
            payload,
        )

    def test_strips_one_ff_before_modbus_exception_reply(self) -> None:
        payload = bytes.fromhex("01 83 02 C0 F1")
        self.assertEqual(
            AP.parse_ap_frame(_build_ap_reply(b"\xFF" + payload)),
            payload,
        )

    def test_does_not_strip_ff_from_non_modbus_payload(self) -> None:
        payload = bytes.fromhex("FF A1 81 01 00 00")
        self.assertEqual(AP.parse_ap_frame(_build_ap_reply(payload)), payload)

    def test_ap_checksum_still_covers_the_original_wire_frame(self) -> None:
        frame = bytearray(_build_ap_reply(bytes.fromhex("FF 01 03 02 12 34 B5 33")))
        frame[-2] ^= 0x01
        with self.assertRaises(AP.TsunProtocolError):
            AP.parse_ap_frame(bytes(frame))


if __name__ == "__main__":
    unittest.main()
