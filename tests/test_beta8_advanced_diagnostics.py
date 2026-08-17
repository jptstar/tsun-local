# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

PROTOCOLS_PATH = Path(__file__).parents[1] / "custom_components" / "tsun_local" / "protocols"
SPEC = importlib.util.spec_from_file_location(
    "tsun_local_beta8_protocol_tests",
    PROTOCOLS_PATH / "__init__.py",
    submodule_search_locations=[str(PROTOCOLS_PATH)],
)
assert SPEC is not None and SPEC.loader is not None
PKG = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PKG
SPEC.loader.exec_module(PKG)

from tsun_local_beta8_protocol_tests.protocol_1511 import decode_advanced_diagnostics as decode_1511_advanced, decode_measurements as decode_1511, detect_pv_count as detect_1511_pv_count  # noqa: E402,E501
from tsun_local_beta8_protocol_tests.protocol_02b0 import DIAGNOSTIC_BLOCKS as BLOCKS_02B0_DIAGNOSTIC, decode_advanced_diagnostics as decode_02b0_advanced  # noqa: E402,E501
from tsun_local_beta8_protocol_tests.protocol_1097 import DIAGNOSTIC_BLOCKS as BLOCKS_1097_DIAGNOSTIC, decode_advanced_diagnostics as decode_1097_advanced  # noqa: E402,E501


class Beta8AdvancedDiagnosticsTests(unittest.TestCase):
    def test_1511_daily_energy_uses_base_plus_five(self) -> None:
        registers = {
            0x0BB8: 1, 0x0BC4: 2300, 0x0BC5: 100, 0x0BC7: 5000,
            0x0BC9: 0, 0x0BCC: 3000, 0x0BCD: 1000, 0x0BCE: 100,
            0x0BCF: 0, 0x0BD0: 100, 0x0E10: 350, 0x0E11: 300,
            0x0E12: 1000, 0x0E15: 130, 0x0E28: 0, 0x0E29: 100,
        }
        self.assertEqual(decode_1511(registers, 1)["pv1_energy_today"], 1.3)
        self.assertEqual(detect_1511_pv_count({0x0EEB: 1}), 6)

    def test_1511_grid_diagnostics(self) -> None:
        data = decode_1511_advanced({0x07D4: 2510, 0x07DB: 62, 0x07EA: 340})
        self.assertEqual(data["grid_overvoltage_recovery_voltage"], 251.0)
        self.assertEqual(data["grid_undervoltage_time_1"], 1.24)
        self.assertEqual(data["grid_undervoltage_level_3"], 34.0)

    def test_02b0_grid_diagnostics_and_output_coefficient(self) -> None:
        self.assertIn((0x03, 0x2014, 0x202C), BLOCKS_02B0_DIAGNOSTIC)
        data = decode_02b0_advanced({0x2014: 2510, 0x2028: 16, 0x202C: 1024})
        self.assertEqual(data["grid_overvoltage_recovery_voltage"], 251.0)
        self.assertEqual(data["grid_overfrequency_time_1"], 0.32)
        self.assertEqual(data["output_coefficient"], 100.0)

    def test_1097_advanced_diagnostics(self) -> None:
        self.assertIn((0x03, 0x1400, 0x1400), BLOCKS_1097_DIAGNOSTIC)
        data = decode_1097_advanced({0x100A: 0x1234, 0x100C: 0x210A, 0x1216: 1234, 0x1217: 567, 0x1218: 65, 0x1400: 8})
        self.assertEqual(data["protocol_version"], "V1.2.34")
        self.assertEqual(data["inverter_version"], "V2.1.0A")
        self.assertEqual(data["insulation_impedance_rx"], 12.34)
        self.assertEqual(data["insulation_impedance_ry"], 5.67)
        self.assertEqual(data["inverter_temperature"], 25)
        self.assertEqual(data["country_profile_raw"], 8)


if __name__ == "__main__":
    unittest.main()
