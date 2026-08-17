# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for the read-only TITAN/1511 diagnostic registers."""

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
    "tsun_local_1511_diagnostic_tests",
    PROTOCOLS_PATH / "__init__.py",
    submodule_search_locations=[str(PROTOCOLS_PATH)],
)
assert SPEC is not None and SPEC.loader is not None
PROTOCOLS = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PROTOCOLS
SPEC.loader.exec_module(PROTOCOLS)

from tsun_local_1511_diagnostic_tests.protocol_1511 import (  # noqa: E402
    DIAGNOSTIC_BLOCKS,
    Tsun1511Client,
    build_1511_request,
    decode_measurements,
)


class Protocol1511DiagnosticTests(unittest.TestCase):
    """Protect the validated MP3000 diagnostic reads and raw semantics."""

    def test_slow_diagnostics_are_due_on_first_poll(self) -> None:
        client = Tsun1511Client("192.0.2.10", 8899, 123456)
        self.assertEqual(client._last_diagnostic_read, 0.0)

    def test_builds_validated_a1_21_2000_block_request(self) -> None:
        self.assertIn((0xA1, 0x21, 2000, 2095), DIAGNOSTIC_BLOCKS)
        self.assertEqual(
            build_1511_request(0xA1, 0x21, 2000, 2095),
            bytes.fromhex("A1 21 00 07 D0 00 02 00 60 3E 5D"),
        )

    def test_keeps_3017_3018_and_3028_as_unscaled_raw_values(self) -> None:
        registers = {
            0x0BB8: 1,
            0x0BC4: 2300,
            0x0BC5: 100,
            0x0BC7: 5000,
            0x0BC9: 92,
            0x0BCA: 68,
            0x0BCC: 3000,
            0x0BCD: 1000,
            0x0BCE: 100,
            0x0BCF: 0,
            0x0BD0: 100,
            0x0BD4: 90,
            0x07FA: 3000,
            0x0E10: 350,
            0x0E11: 300,
            0x0E12: 1050,
            0x0E14: 10,
            0x0E28: 0,
            0x0E29: 100,
        }

        data = decode_measurements(registers, 1)

        self.assertEqual(data["inverter_status_raw"], 1)
        self.assertEqual(data["rated_power"], 3000)
        self.assertEqual(data["max_designed_power"], 3000)
        self.assertEqual(data["register_3017_raw"], 92)
        self.assertEqual(data["register_3018_raw"], 68)
        self.assertEqual(data["register_3028_raw"], 90)


if __name__ == "__main__":
    unittest.main()
