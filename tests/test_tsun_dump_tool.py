# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for the standalone TSUN hardware validation dump tool."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


TOOL_PATH = Path(__file__).parents[1] / "tools" / "tsun_dump.py"
SPEC = importlib.util.spec_from_file_location("tsun_dump_tool_test", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
TOOL = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = TOOL
SPEC.loader.exec_module(TOOL)


class TsunDumpToolTests(unittest.TestCase):
    """Verify privacy helpers, capture plans and comparison behavior."""

    def test_extracts_single_monitor_sn_from_json_discovery(self) -> None:
        payload = b'{"ip":"192.168.1.25","logger_sn":"1234567890"}'
        self.assertEqual(TOOL.serial_candidates_from_payload(payload), {1234567890})

    def test_ambiguous_text_discovery_keeps_all_candidates(self) -> None:
        payload = b"192.168.1.25,AA:BB:CC:DD:EE:FF,123456789,987654321"
        self.assertEqual(
            TOOL.serial_candidates_from_payload(payload),
            {123456789, 987654321},
        )

    def test_modbus_capture_plans_are_read_only_fc03(self) -> None:
        for protocol in ("02b0", "1097"):
            for full in (False, True):
                dynamic, supplemental = TOOL.capture_plans(protocol, full)
                for function, start, end in (*dynamic, *supplemental):
                    self.assertEqual(function, 0x03)
                    self.assertLessEqual(start, end)
                    self.assertLessEqual(
                        end - start + 1,
                        TOOL.MAX_MODBUS_REGISTERS_PER_READ,
                    )

    def test_1511_plan_uses_only_known_native_read_blocks(self) -> None:
        dynamic, supplemental = TOOL.capture_plans("1511", True)
        self.assertEqual(
            dynamic,
            [
                (0xA1, 0x01, 0x0BB8, 0x0BD7),
                (0xA2, 0x02, 0x0CE4, 0x0CE7),
                (0xA3, 0x03, 0x0E10, 0x0E2D),
                (0xA4, 0x04, 0x0ED8, 0x0EF5),
            ],
        )
        self.assertEqual(supplemental, [(0xA1, 0x21, 0x07D0, 0x082F)])

    def test_full_02b0_plan_covers_zero_export_research_area(self) -> None:
        _dynamic, supplemental = TOOL.capture_plans("02b0", True)
        addresses = {
            address
            for _function, start, end in supplemental
            for address in range(start, end + 1)
        }
        self.assertIn(0x2047, addresses)
        self.assertIn(0x2048, addresses)
        self.assertIn(0x204A, addresses)

    def test_snapshot_analysis_separates_dynamic_and_stable_values(self) -> None:
        snapshots = [
            {"registers": {"0x3009": 2300, "0x300F": 5000, "0x2007": 800, "0x2048": 0}},
            {"registers": {"0x3009": 2301, "0x300F": 5100, "0x2007": 800, "0x2048": 0}},
            {"registers": {"0x3009": 2299, "0x300F": 5050, "0x2007": 800, "0x2048": 0}},
        ]
        result = TOOL.analyze_snapshots(snapshots)
        self.assertEqual(result["changing_registers"], ["0x3009", "0x300F"])
        self.assertEqual(result["stable_registers"], ["0x2007"])
        self.assertEqual(result["zero_registers"], ["0x2048"])

    def test_compare_reports_raw_changes_without_semantic_guess(self) -> None:
        before = {
            "metadata": {"detected_protocol": "02b0"},
            "raw_registers": [
                {"key": "0x2007", "raw_decimal": 800},
                {"key": "0x2048", "raw_decimal": 0},
            ],
        }
        after = {
            "metadata": {"detected_protocol": "02b0"},
            "raw_registers": [
                {"key": "0x2007", "raw_decimal": 800},
                {"key": "0x2048", "raw_decimal": 1},
            ],
        }
        result = TOOL.compare_documents(before, after)
        self.assertEqual(
            result["changed_registers"],
            [
                {
                    "key": "0x2048",
                    "before": 0,
                    "before_hex": "0x0000",
                    "after": 1,
                    "after_hex": "0x0001",
                }
            ],
        )
        self.assertNotIn("name", result["changed_registers"][0])

    def test_output_filename_is_sanitized(self) -> None:
        from datetime import UTC, datetime

        path = TOOL.default_output_path(
            "TSOL-MS800 / test",
            "02b0",
            datetime(2026, 8, 20, 8, 0, tzinfo=UTC),
        )
        self.assertEqual(path.name, "tsun_tsol-ms800-test_02b0_20260820T080000Z.json")


if __name__ == "__main__":
    unittest.main()
