# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for MP3000/TITAN diagnostics awaiting physical validation."""

from __future__ import annotations

import unittest

from custom_components.tsun_local.protocols.protocol_1511 import (
    ADVANCED_GRID_REGISTERS,
    decode_advanced_diagnostics,
)


class Mp3000FieldValidationTests(unittest.TestCase):
    """Keep beta field candidates aligned with the observed MP3000 dump."""

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


if __name__ == "__main__":
    unittest.main()
