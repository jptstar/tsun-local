# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Regression tests for harmonized daily-energy tracking."""

from __future__ import annotations

from datetime import date
import importlib.util
from pathlib import Path
import sys
import unittest

MODULE_PATH = (
    Path(__file__).parents[1]
    / "custom_components"
    / "tsun_local"
    / "daily_energy.py"
)
SPEC = importlib.util.spec_from_file_location("tsun_daily_energy_tests", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)
DailyEnergyTracker = MODULE.DailyEnergyTracker
repair_legacy_daily_state = MODULE.repair_legacy_daily_state


class DailyEnergyTrackerTests(unittest.TestCase):
    def test_1511_or_02b0_sunrise_reset_does_not_create_new_day(self) -> None:
        day = date(2026, 9, 8)
        tracker = DailyEnergyTracker(date(2026, 9, 7), value=1.9)
        tracker.reset_for_date(day, raw_daily=1.9, total_energy=100.0)
        self.assertEqual(
            tracker.update(current_date=day, raw_daily=1.9, total_energy=100.0, online=True),
            0.0,
        )
        self.assertEqual(
            tracker.update(current_date=day, raw_daily=0.0, total_energy=100.0, online=True),
            0.0,
        )
        self.assertAlmostEqual(
            tracker.update(current_date=day, raw_daily=0.2, total_energy=100.2, online=True),
            0.2,
        )

    def test_1097_18h_reset_is_ignored_while_total_continues(self) -> None:
        day = date(2026, 9, 8)
        tracker = DailyEnergyTracker(
            day, value=3.2, raw_daily=3.2, total_energy=1003.2
        )
        self.assertAlmostEqual(
            tracker.update(current_date=day, raw_daily=0.0, total_energy=1003.2, online=True),
            3.2,
        )
        self.assertAlmostEqual(
            tracker.update(current_date=day, raw_daily=0.25, total_energy=1003.45, online=True),
            3.45,
        )

    def test_same_day_restart_recovers_missed_total_delta(self) -> None:
        day = date(2026, 9, 8)
        tracker = DailyEnergyTracker(day)
        value = tracker.restore(
            current_date=day,
            state_value=3.2,
            state_date=day,
            restored_raw_daily=3.2,
            restored_total_energy=1003.2,
            current_raw_daily=0.25,
            current_total_energy=1003.45,
            current_online=True,
        )
        self.assertAlmostEqual(value, 3.45)

    def test_restart_after_midnight_uses_midnight_total_reference(self) -> None:
        day = date(2026, 9, 8)
        tracker = DailyEnergyTracker(day)
        value = tracker.restore(
            current_date=day,
            state_value=0.0,
            state_date=day,
            restored_raw_daily=0.40,
            restored_total_energy=1003.60,
            current_raw_daily=0.42,
            current_total_energy=1003.62,
            current_online=True,
        )
        self.assertAlmostEqual(value, 0.02)

    def test_long_cross_midnight_outage_uses_fresh_daily_best_effort(self) -> None:
        yesterday = date(2026, 9, 7)
        today = date(2026, 9, 8)
        tracker = DailyEnergyTracker(today)
        value = tracker.restore(
            current_date=today,
            state_value=3.0,
            state_date=yesterday,
            restored_raw_daily=3.0,
            restored_total_energy=1000.0,
            current_raw_daily=1.5,
            current_total_energy=1001.9,
            current_online=True,
        )
        self.assertEqual(value, 1.5)

    def test_total_reset_falls_back_to_raw_daily_delta(self) -> None:
        day = date(2026, 9, 8)
        tracker = DailyEnergyTracker(
            day, value=2.0, raw_daily=2.0, total_energy=500.0
        )
        value = tracker.update(
            current_date=day,
            raw_daily=2.1,
            total_energy=1.0,
            online=True,
        )
        self.assertAlmostEqual(value, 2.1)

    def test_repairs_gross_161_wh_kwh_contamination(self) -> None:
        self.assertAlmostEqual(
            repair_legacy_daily_state(
                190.27,
                current_total_energy=42.0,
                restored_total_energy=41.99,
            ),
            0.19027,
        )

    def test_repairs_legacy_daily_value_that_exceeds_lifetime_total(self) -> None:
        self.assertAlmostEqual(
            repair_legacy_daily_state(
                50.0,
                current_total_energy=12.0,
                restored_total_energy=11.99,
            ),
            0.05,
        )

    def test_keeps_plausible_legacy_daily_value(self) -> None:
        self.assertEqual(
            repair_legacy_daily_state(
                5.0,
                current_total_energy=120.0,
                restored_total_energy=119.9,
            ),
            5.0,
        )

    def test_tracker_metadata_marks_normalized_restore_version(self) -> None:
        tracker = DailyEnergyTracker(date(2026, 9, 12), value=1.25)
        self.assertEqual(tracker.state_attributes()["tracking_version"], 2)


if __name__ == "__main__":
    unittest.main()
