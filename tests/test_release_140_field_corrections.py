# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Regression tests for the field-validation corrections in stable 1.4.0."""

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
    "tsun_local_release_140_protocol_tests",
    PROTOCOLS_PATH / "__init__.py",
    submodule_search_locations=[str(PROTOCOLS_PATH)],
)
assert SPEC is not None and SPEC.loader is not None
PROTOCOLS = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PROTOCOLS
SPEC.loader.exec_module(PROTOCOLS)

from tsun_local_release_140_protocol_tests.protocol_1511 import (  # noqa: E402
    GLOBAL_ALARM_REGISTERS,
    SECONDARY_ALARM_REGISTERS,
    decode_alarms,
)


def _alarm_registers(global_1: int = 0, inverter_status: int = 0) -> dict[int, int]:
    registers = {
        address: 0
        for address in (*GLOBAL_ALARM_REGISTERS, *SECONDARY_ALARM_REGISTERS)
    }
    registers[GLOBAL_ALARM_REGISTERS[1]] = global_1
    registers[0x0BB8] = inverter_status
    return registers


class Release140FieldCorrectionTests(unittest.TestCase):
    def test_low_solar_status_is_preserved_but_not_a_fault(self) -> None:
        data = decode_alarms(_alarm_registers(0x2000), 1)
        self.assertEqual(data["alarm_global_1_raw"], 8192)
        self.assertEqual(data["alarm_active"], 0)
        self.assertEqual(data["inverter_operating_state"], "standby_low_solar")

    def test_low_solar_plus_another_bit_remains_a_fault(self) -> None:
        data = decode_alarms(_alarm_registers(0x2001), 1)
        self.assertEqual(data["alarm_active"], 1)
        self.assertEqual(data["inverter_operating_state"], "fault")

    def test_active_and_plain_standby_states(self) -> None:
        active = decode_alarms(_alarm_registers(inverter_status=1), 1)
        standby = decode_alarms(_alarm_registers(inverter_status=0), 1)
        self.assertEqual(active["inverter_operating_state"], "active")
        self.assertEqual(standby["inverter_operating_state"], "standby")

    def test_sensor_metadata_retains_raw_values_and_confirmed_percentage(self) -> None:
        source = (
            Path(__file__).parents[1]
            / "custom_components"
            / "tsun_local"
            / "sensor.py"
        ).read_text(encoding="utf-8")

        self.assertIn('"register_3017_raw",\n        "register_3017_raw",\n        "3017 (0x0BC9)",\n        chartable=True,', source)
        self.assertIn('"register_3028_raw",\n        "register_3028_raw",\n        "3028 (0x0BD4)",\n        chartable=True,', source)

        start = source.index('        "output_coefficient",')
        block = source[start : start + 180]
        self.assertIn("unit=PERCENTAGE", block)

        self.assertIn('"standby_low_solar"', source)
        self.assertIn("GRID_TIMING_SENSOR_KEYS", source)
        self.assertIn("UnitOfTime.SECONDS", source)


if __name__ == "__main__":
    unittest.main()
