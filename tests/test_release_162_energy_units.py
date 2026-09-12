# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Release 1.6.2 energy-unit regression audit across every runtime protocol."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).parents[1]
PROTOCOLS_PATH = ROOT / "custom_components" / "tsun_local" / "protocols"
SPEC = importlib.util.spec_from_file_location(
    "tsun_local_release_162_energy_tests",
    PROTOCOLS_PATH / "__init__.py",
    submodule_search_locations=[str(PROTOCOLS_PATH)],
)
assert SPEC is not None and SPEC.loader is not None
PKG = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PKG
SPEC.loader.exec_module(PKG)

from tsun_local_release_162_energy_tests.protocol_02b0 import (  # noqa: E402
    decode_measurements as decode_02b0,
)
from tsun_local_release_162_energy_tests.protocol_1097 import (  # noqa: E402
    decode_measurements as decode_1097,
)
from tsun_local_release_162_energy_tests.protocol_1511 import (  # noqa: E402
    decode_measurements as decode_1511,
)


class Release162EnergyUnitTests(unittest.TestCase):
    """Prove that every decoder feeds the shared HA layer in native kWh."""

    def test_1511_ac_and_pv_energy_are_kwh(self) -> None:
        registers = {
            0x0BB8: 1,
            0x0BC4: 2300,
            0x0BC5: 100,
            0x0BC7: 5000,
            0x0BC9: 65,
            0x0BCC: 3000,
            0x0BCD: 1000,
            0x0BCE: 125,
            0x0BCF: 0,
            0x0BD0: 12345,
            0x0E10: 410,
            0x0E11: 100,
            0x0E12: 400,
            0x0E15: 150,
            0x0E28: 0,
            0x0E29: 23456,
        }
        data = decode_1511(registers, 1)
        self.assertAlmostEqual(data["ac_energy_today"], 1.25)
        self.assertAlmostEqual(data["ac_energy_total"], 123.45)
        self.assertAlmostEqual(data["pv1_energy_today"], 1.50)
        self.assertAlmostEqual(data["pv1_energy_total"], 234.56)

    def test_02b0_ac_and_pv_energy_are_kwh(self) -> None:
        registers = {address: 0 for address in range(0x3009, 0x302B)}
        registers.update(
            {
                0x3009: 2300,
                0x300A: 100,
                0x300B: 5000,
                0x300E: 800,
                0x300F: 1000,
                0x301C: 125,
                0x301D: 0,
                0x301E: 12345,
                0x3010: 410,
                0x3011: 100,
                0x3012: 400,
                0x301F: 150,
                0x3020: 0,
                0x3021: 23456,
            }
        )
        data = decode_02b0(registers, 1)
        self.assertAlmostEqual(data["ac_energy_today"], 1.25)
        self.assertAlmostEqual(data["ac_energy_total"], 123.45)
        self.assertAlmostEqual(data["pv1_energy_today"], 1.50)
        self.assertAlmostEqual(data["pv1_energy_total"], 234.56)

    def test_1097_ac_and_pv_energy_are_kwh(self) -> None:
        registers = {
            0x1100: 2,
            0x1200: 2300,
            0x1201: 100,
            0x1202: 1000,
            0x1209: 5000,
            0x1210: 800,
            0x1212: 125,
            0x1213: 0,
            0x1214: 12345,
            0x1302: 410,
            0x1303: 100,
            0x1304: 400,
            0x1305: 0,
            0x1306: 150,
            0x1307: 0,
            0x1308: 23456,
        }
        data = decode_1097(registers, 1)
        self.assertAlmostEqual(data["ac_energy_today"], 1.25)
        self.assertAlmostEqual(data["ac_energy_total"], 123.45)
        self.assertAlmostEqual(data["pv1_energy_today"], 1.50)
        self.assertAlmostEqual(data["pv1_energy_total"], 234.56)

    def test_home_assistant_energy_contract_is_kwh_and_unit_safe(self) -> None:
        sensor = (ROOT / "custom_components/tsun_local/sensor.py").read_text(
            encoding="utf-8"
        )
        self.assertGreaterEqual(sensor.count("UnitOfEnergy.KILO_WATT_HOUR"), 4)
        self.assertIn("EnergyConverter.convert", sensor)
        self.assertIn('state.attributes.get("unit_of_measurement")', sensor)
        self.assertIn("_restored_energy_kwh(last_state)", sensor)
        self.assertNotIn("state_value = energy_value(last_state.state)", sensor)
        self.assertNotIn(
            "_restored_energy_value = energy_value(last_state.state)", sensor
        )

    def test_tracking_metadata_marks_corrected_restore_format(self) -> None:
        daily = (ROOT / "custom_components/tsun_local/daily_energy.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('"tracking_version": 2', daily)
        self.assertIn("repair_legacy_daily_state", daily)


if __name__ == "__main__":
    unittest.main()
