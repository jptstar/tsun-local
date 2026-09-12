# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Regression tests for offline energy restoration and daily rollover."""

from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).parents[1]


class EnergyRestoreContractTests(unittest.TestCase):
    def test_energy_entities_use_home_assistant_restore_state(self) -> None:
        source = (ROOT / "custom_components/tsun_local/sensor.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("RestoreEntity", source)
        self.assertIn("async_get_last_state", source)
        self.assertIn("STATE_UNKNOWN", source)
        self.assertIn("STATE_UNAVAILABLE", source)
        self.assertIn("DailyEnergyTracker", source)

    def test_daily_energy_has_local_midnight_rollover(self) -> None:
        source = (ROOT / "custom_components/tsun_local/sensor.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("async_track_time_change", source)
        self.assertIn("hour=0", source)
        self.assertIn("minute=0", source)
        self.assertIn("second=0", source)
        self.assertIn("reset_for_date", source)
        self.assertIn("dt_util.now().date()", source)
        self.assertIn("tracking_total_energy", source)
        self.assertNotIn("_daily_reset_override", source)
        self.assertNotIn("_daily_reset_successes", source)

    def test_missing_energy_without_history_is_unavailable_not_unknown(self) -> None:
        source = (ROOT / "custom_components/tsun_local/sensor.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("self._daily_tracker is not None", source)
        self.assertIn("self._daily_tracker.value is not None", source)
        self.assertIn("or self._restored_energy_value is not None", source)
        self.assertNotIn("return True", source)

    def test_1511_adds_all_validated_pv_entities_even_before_live_detection(self) -> None:
        source = (ROOT / "custom_components/tsun_local/sensor.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('protocol_name == "1511"', source)
        self.assertIn('description.key.startswith("pv")', source)

    def test_restored_energy_is_normalized_from_display_unit_to_kwh(self) -> None:
        source = (ROOT / "custom_components/tsun_local/sensor.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("def _restored_energy_kwh", source)
        self.assertIn("EnergyConverter.convert", source)
        self.assertIn('state.attributes.get("unit_of_measurement")', source)
        self.assertIn("UnitOfEnergy.KILO_WATT_HOUR", source)
        self.assertNotIn("state_value = energy_value(last_state.state)", source)
        self.assertNotIn("_restored_energy_value = energy_value(last_state.state)", source)

    def test_161_contamination_is_only_repaired_without_v2_tracker_metadata(self) -> None:
        source = (ROOT / "custom_components/tsun_local/sensor.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("repair_legacy_daily_state", source)
        self.assertIn('\"tracking_version\" not in last_state.attributes', source)


if __name__ == "__main__":
    unittest.main()
