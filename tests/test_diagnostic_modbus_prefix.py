# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Regression tests for diagnostic handling of the optional 0xFF marker."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


MODULE_PATH = Path(__file__).parents[1] / "tools" / "tsun_dump.py"
SPEC = importlib.util.spec_from_file_location("tsun_dump_ff_tests", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
DUMP = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = DUMP
SPEC.loader.exec_module(DUMP)


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
    return b"\xA5" + scope + bytes((DUMP.checksum_ap(scope), 0x15))


class DiagnosticModbusPrefixTests(unittest.TestCase):
    def test_keeps_normal_modbus_reply(self) -> None:
        payload = bytes.fromhex("01 03 02 12 34 B5 33")
        self.assertEqual(DUMP.parse_ap_frame(_build_ap_reply(payload)), payload)

    def test_strips_one_leading_ff_from_modbus_reply(self) -> None:
        payload = bytes.fromhex("01 03 02 12 34 B5 33")
        self.assertEqual(
            DUMP.parse_ap_frame(_build_ap_reply(b"\xFF" + payload)),
            payload,
        )

    def test_strips_one_leading_ff_from_modbus_exception(self) -> None:
        payload = bytes.fromhex("01 83 02 C0 F1")
        self.assertEqual(
            DUMP.parse_ap_frame(_build_ap_reply(b"\xFF" + payload)),
            payload,
        )

    def test_keeps_non_modbus_ff_payload(self) -> None:
        payload = bytes.fromhex("FF A1 81 01 00 00")
        self.assertEqual(DUMP.parse_ap_frame(_build_ap_reply(payload)), payload)

    def test_ap_checksum_is_validated_before_normalization(self) -> None:
        frame = bytearray(_build_ap_reply(bytes.fromhex("FF 01 03 02 12 34 B5 33")))
        frame[-2] ^= 0x01
        with self.assertRaises(DUMP.TsunProtocolError):
            DUMP.parse_ap_frame(bytes(frame))


if __name__ == "__main__":
    unittest.main()
