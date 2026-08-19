from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).parents[1]
PROTOCOLS_PATH = ROOT / "custom_components" / "tsun_local" / "protocols"
SPEC = importlib.util.spec_from_file_location(
    "tsun_local_mp3000_protection_tests",
    PROTOCOLS_PATH / "__init__.py",
    submodule_search_locations=[str(PROTOCOLS_PATH)],
)
assert SPEC is not None and SPEC.loader is not None
PKG = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PKG
SPEC.loader.exec_module(PKG)

from tsun_local_mp3000_protection_tests.protocol_1511 import (  # noqa: E402
    ADVANCED_GRID_REGISTERS,
    decode_advanced_diagnostics,
)


class Mp3000ProtectionCandidateTests(unittest.TestCase):
    def test_candidate_register_positions_are_stable(self) -> None:
        expected = {
            "grid_qp_voltage_threshold": (0x07D2, 0.1),
            "grid_recovery_speed": (0x07D3, 0.1),
            "grid_overtemperature_protection_value": (0x07D8, 1.0),
            "grid_overfrequency_reduction_frequency": (0x07E1, 0.01),
            "grid_overfrequency_reduction_coefficient": (0x07EC, 1.0),
            "grid_start_upper_voltage": (0x07F1, 0.1),
            "grid_start_lower_voltage": (0x07F2, 0.1),
            "grid_start_upper_frequency": (0x07F3, 0.01),
            "grid_start_lower_frequency": (0x07F4, 0.01),
            "grid_connection_time": (0x07F7, 0.1),
            "grid_reconnection_time": (0x07F8, 0.1),
            "grid_ten_minute_overvoltage_protection": (0x07F9, 0.1),
        }
        for key, mapping in expected.items():
            self.assertEqual(ADVANCED_GRID_REGISTERS[key], mapping)

    def test_candidate_scaling_matches_export_reference_values(self) -> None:
        registers = {
            0x07D2: 1050,
            0x07D3: 6400,
            0x07D8: 79,
            0x07E1: 5020,
            0x07EC: 0x0FA0,
            0x07F1: 2510,
            0x07F2: 1960,
            0x07F3: 5009,
            0x07F4: 4951,
            0x07F7: 400,
            0x07F8: 400,
            0x07F9: 2530,
        }
        data = decode_advanced_diagnostics(registers)
        self.assertEqual(data["grid_qp_voltage_threshold"], 105.0)
        self.assertEqual(data["grid_recovery_speed"], 640.0)
        self.assertEqual(data["grid_overtemperature_protection_value"], 79.0)
        self.assertEqual(data["grid_overfrequency_reduction_frequency"], 50.2)
        self.assertEqual(data["grid_overfrequency_reduction_coefficient"], 4000.0)
        self.assertEqual(data["grid_start_upper_voltage"], 251.0)
        self.assertEqual(data["grid_start_lower_voltage"], 196.0)
        self.assertEqual(data["grid_start_upper_frequency"], 50.09)
        self.assertEqual(data["grid_start_lower_frequency"], 49.51)
        self.assertEqual(data["grid_connection_time"], 40.0)
        self.assertEqual(data["grid_reconnection_time"], 40.0)
        self.assertEqual(
            data["grid_ten_minute_overvoltage_protection"], 253.0
        )

    def test_documentation_marks_candidates_as_physical_test_required(self) -> None:
        documentation = (
            ROOT / "docs" / "MP3000_PROTECTION_VALIDATION.md"
        ).read_text(encoding="utf-8")
        self.assertGreaterEqual(documentation.count("Physical test required"), 12)
        self.assertIn("Home Assistant deliberately shows the clean functional name only", documentation)


if __name__ == "__main__":
    unittest.main()
