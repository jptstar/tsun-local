# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).parents[1]
MODULE_PATH = ROOT / "custom_components" / "tsun_local" / "logger_wifi_freshness.py"
SPEC = importlib.util.spec_from_file_location("tsun_logger_wifi_freshness", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
FRESHNESS = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = FRESHNESS
SPEC.loader.exec_module(FRESHNESS)
LOGGER_WIFI_MISS_THRESHOLD = FRESHNESS.LOGGER_WIFI_MISS_THRESHOLD
LoggerWifiSignalFreshness = FRESHNESS.LoggerWifiSignalFreshness


class LoggerWifiSignalFreshnessTests(unittest.TestCase):
    def test_one_miss_is_preserved_and_second_miss_expires(self) -> None:
        tracker = LoggerWifiSignalFreshness()
        self.assertEqual(LOGGER_WIFI_MISS_THRESHOLD, 2)
        self.assertFalse(tracker.observe(None))
        self.assertEqual(tracker.consecutive_misses, 1)
        self.assertTrue(tracker.observe(None))
        self.assertEqual(tracker.consecutive_misses, 2)

    def test_valid_signal_recovers_immediately(self) -> None:
        tracker = LoggerWifiSignalFreshness()
        tracker.observe(None)
        tracker.observe(None)
        self.assertFalse(tracker.observe(47))
        self.assertEqual(tracker.consecutive_misses, 0)
        self.assertFalse(tracker.observe(None))

    def test_common_integration_wiring_expires_rssi_without_zero(self) -> None:
        init_source = (
            ROOT / "custom_components" / "tsun_local" / "__init__.py"
        ).read_text(encoding="utf-8")
        coordinator_source = (
            ROOT / "custom_components" / "tsun_local" / "coordinator.py"
        ).read_text(encoding="utf-8")
        sensor_source = (
            ROOT / "custom_components" / "tsun_local" / "sensor.py"
        ).read_text(encoding="utf-8")
        self.assertIn("wifi_signal_freshness.observe(None)", init_source)
        self.assertIn("async_remove_logger_metadata", init_source)
        self.assertIn("def async_remove_logger_metadata", coordinator_source)
        self.assertIn('key == "logger_wifi_signal"', sensor_source)
        self.assertNotIn('updates["logger_wifi_signal"] = 0', init_source)


if __name__ == "__main__":
    unittest.main()
