# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for MP3000/TITAN mappings validated against live device reads."""

from __future__ import annotations

import unittest

from custom_components.tsun_local.protocols.protocol_1511 import (
    ADVANCED_GRID_REGISTERS,
    decode_advanced_diagnostics,
    decode_measurements,
)


class Mp3000FieldValidationTests(unittest.TestCase):
    """Keep beta mappings aligned with live MP3000/TITAN evidence."""

    def test_candidate_register_addresses(self) -> None:
        expected = {
            "grid_recovery_rate": (0x07D3, 0.5),
            "grid_overvoltage_10min": (0x07E1, 0.1),
            "grid_overfrequency_reduction_frequency": (0x07EE, 0.01),
            "grid_overfrequency_reduction_coefficient": (0x07EF, 1.0),
            "overtemperature_protection_temperature": (0x07F0, 1.0),
            "grid_start_upper_voltage_limit": (0x07FB, 0.1),
            "grid_start_lower_voltage_limit": (0x07FC, 0.1),
            "grid_start_upper_frequency_limit": (0x07FD, 0.01),
            "grid_start_lower_frequency_limit": (0x07FE, 0.01),
            "grid_qp_voltage_threshold": (0x0800, 1.0),
        }
        for key, mapping in expected.items():
            self.assertEqual(ADVANCED_GRID_REGISTERS[key], mapping)

    def test_observed_dump_values_match_talent_profile(self) -> None:
        registers = {
            0x07D3: 1280,
            0x07E1: 2530,
            0x07EE: 5020,
            0x07EF: 4000,
            0x07F0: 79,
            0x07FB: 2510,
            0x07FC: 1960,
            0x07FD: 5009,
            0x07FE: 4951,
            0x0800: 105,
        }
        decoded = decode_advanced_diagnostics(registers)
        self.assertEqual(decoded["grid_recovery_rate"], 640.0)
        self.assertEqual(decoded["grid_overvoltage_10min"], 253.0)
        self.assertEqual(
            decoded["grid_overfrequency_reduction_frequency"], 50.2
        )
        self.assertEqual(
            decoded["grid_overfrequency_reduction_coefficient"], 4000.0
        )
        self.assertEqual(
            decoded["overtemperature_protection_temperature"], 79.0
        )
        self.assertEqual(decoded["grid_start_upper_voltage_limit"], 251.0)
        self.assertEqual(decoded["grid_start_lower_voltage_limit"], 196.0)
        self.assertEqual(decoded["grid_start_upper_frequency_limit"], 50.09)
        self.assertEqual(decoded["grid_start_lower_frequency_limit"], 49.51)
        self.assertEqual(decoded["grid_qp_voltage_threshold"], 105.0)

    def test_live_dump_confirms_six_pv_daily_registers(self) -> None:
        """Protect the six PV daily counters confirmed by the 2026-08-19 dump."""
        registers = {
            0x0BB8: 1,
            0x0BC4: 2329,
            0x0BC5: 849,
            0x0BC7: 5002,
            0x0BC9: 112,
            0x0BCC: 3000,
            0x0BCD: 19596,
            0x0BCE: 555,
            0x0BCF: 0,
            0x0BD0: 51851,
            0x0E10: 328,
            0x0E11: 1114,
            0x0E12: 3653,
            0x0E15: 104,
            0x0E17: 320,
            0x0E18: 1107,
            0x0E19: 3542,
            0x0E1C: 100,
            0x0E1E: 336,
            0x0E1F: 1074,
            0x0E20: 3608,
            0x0E23: 103,
            0x0E28: 0,
            0x0E29: 9834,
            0x0E2A: 0,
            0x0E2B: 9448,
            0x0E2C: 0,
            0x0E2D: 9678,
            0x0ED8: 335,
            0x0ED9: 1082,
            0x0EDA: 3624,
            0x0EDD: 103,
            0x0EDF: 328,
            0x0EE0: 1079,
            0x0EE1: 3539,
            0x0EE4: 103,
            0x0EE6: 345,
            0x0EE7: 1065,
            0x0EE8: 3674,
            0x0EEB: 104,
            0x0EF0: 0,
            0x0EF1: 9662,
            0x0EF2: 0,
            0x0EF3: 9750,
            0x0EF4: 0,
            0x0EF5: 9779,
        }
        decoded = decode_measurements(registers, 6)
        pv_daily = [
            decoded[f"pv{number}_energy_today"] for number in range(1, 7)
        ]
        self.assertEqual(pv_daily, [1.04, 1.0, 1.03, 1.03, 1.03, 1.04])
        self.assertEqual(round(sum(pv_daily), 2), 6.17)
        self.assertEqual(decoded["ac_energy_today"], 5.55)
        self.assertEqual(decoded["dc_power_total"], 2164.0)


if __name__ == "__main__":
    unittest.main()
