# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Regression contract for offline energy persistence and daily rollover."""

from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).parents[1]


class EnergyRestoreContractTests(unittest.TestCase):
    """Protect restart/offline energy behavior across protocol families."""

    def test_energy_entities_use_home_assistant_restore_state(self) -> None:
        source = (ROOT / "custom_components/tsun_local/sensor.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("RestoreEntity, SensorEntity", source)
        self.assertIn("await self.async_get_last_state()", source)
        self.assertIn("self._restored_energy_value", source)
        self.assertIn("key in self.coordinator.data", source)

    def test_daily_energy_has_local_midnight_rollover(self) -> None:
        source = (ROOT / "custom_components/tsun_local/sensor.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("async_track_time_change", source)
        self.assertIn("hour=0", source)
        self.assertIn("minute=0", source)
        self.assertIn("second=0", source)
        self.assertIn("last_local_date != dt_util.now().date()", source)
        self.assertIn("self._daily_reset_override = True", source)
        self.assertIn("self._daily_reset_successes >= 2", source)

    def test_missing_energy_without_history_is_unavailable_not_unknown(self) -> None:
        source = (ROOT / "custom_components/tsun_local/sensor.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("if self._is_energy:", source)
        self.assertIn("or self._restored_energy_value is not None", source)
        self.assertIn("or self._daily_reset_override", source)

    def test_1511_adds_all_validated_pv_entities_even_before_live_detection(self) -> None:
        source = (ROOT / "custom_components/tsun_local/sensor.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('protocol_name == "1511"', source)
        self.assertIn('description.key.startswith("pv")', source)


if __name__ == "__main__":
    unittest.main()
