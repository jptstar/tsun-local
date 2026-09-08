from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parents[1]

# The integration package __init__ imports Home Assistant. Load the small pure
# freshness module directly so this regression test remains standalone like the
# existing logger-web unit tests.
test_path = ROOT / "tests" / "test_logger_wifi_freshness.py"
test_path.write_text(
    '''# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)\n'''
    '''# SPDX-License-Identifier: GPL-3.0-or-later\n\n'''
    '''from __future__ import annotations\n\n'''
    '''import importlib.util\n'''
    '''from pathlib import Path\n'''
    '''import sys\n'''
    '''import unittest\n\n'''
    '''ROOT = Path(__file__).parents[1]\n'''
    '''MODULE_PATH = ROOT / "custom_components" / "tsun_local" / "logger_wifi_freshness.py"\n'''
    '''SPEC = importlib.util.spec_from_file_location("tsun_logger_wifi_freshness", MODULE_PATH)\n'''
    '''assert SPEC is not None and SPEC.loader is not None\n'''
    '''FRESHNESS = importlib.util.module_from_spec(SPEC)\n'''
    '''sys.modules[SPEC.name] = FRESHNESS\n'''
    '''SPEC.loader.exec_module(FRESHNESS)\n'''
    '''LOGGER_WIFI_MISS_THRESHOLD = FRESHNESS.LOGGER_WIFI_MISS_THRESHOLD\n'''
    '''LoggerWifiSignalFreshness = FRESHNESS.LoggerWifiSignalFreshness\n\n\n'''
    '''class LoggerWifiSignalFreshnessTests(unittest.TestCase):\n'''
    '''    def test_one_miss_is_preserved_and_second_miss_expires(self) -> None:\n'''
    '''        tracker = LoggerWifiSignalFreshness()\n'''
    '''        self.assertEqual(LOGGER_WIFI_MISS_THRESHOLD, 2)\n'''
    '''        self.assertFalse(tracker.observe(None))\n'''
    '''        self.assertEqual(tracker.consecutive_misses, 1)\n'''
    '''        self.assertTrue(tracker.observe(None))\n'''
    '''        self.assertEqual(tracker.consecutive_misses, 2)\n\n'''
    '''    def test_valid_signal_recovers_immediately(self) -> None:\n'''
    '''        tracker = LoggerWifiSignalFreshness()\n'''
    '''        tracker.observe(None)\n'''
    '''        tracker.observe(None)\n'''
    '''        self.assertFalse(tracker.observe(47))\n'''
    '''        self.assertEqual(tracker.consecutive_misses, 0)\n'''
    '''        self.assertFalse(tracker.observe(None))\n\n'''
    '''    def test_common_integration_wiring_expires_rssi_without_zero(self) -> None:\n'''
    '''        init_source = (\n'''
    '''            ROOT / "custom_components" / "tsun_local" / "__init__.py"\n'''
    '''        ).read_text(encoding="utf-8")\n'''
    '''        coordinator_source = (\n'''
    '''            ROOT / "custom_components" / "tsun_local" / "coordinator.py"\n'''
    '''        ).read_text(encoding="utf-8")\n'''
    '''        sensor_source = (\n'''
    '''            ROOT / "custom_components" / "tsun_local" / "sensor.py"\n'''
    '''        ).read_text(encoding="utf-8")\n'''
    '''        self.assertIn("wifi_signal_freshness.observe(None)", init_source)\n'''
    '''        self.assertIn("async_remove_logger_metadata", init_source)\n'''
    '''        self.assertIn("def async_remove_logger_metadata", coordinator_source)\n'''
    '''        self.assertIn('key == "logger_wifi_signal"', sensor_source)\n'''
    '''        self.assertNotIn('updates["logger_wifi_signal"] = 0', init_source)\n\n\n'''
    '''if __name__ == "__main__":\n'''
    '''    unittest.main()\n''',
    encoding="utf-8",
)

contract_path = ROOT / "tests" / "test_beta2_release_contract.py"
contract = contract_path.read_text(encoding="utf-8")
old = '''    def test_failed_http_signal_keeps_last_known_value(self) -> None:\n        init_source = (ROOT / "custom_components/tsun_local/__init__.py").read_text(encoding="utf-8")\n        self.assertNotIn('signal if signal is not None else 0', init_source)\n        self.assertIn('if signal is not None:\\n                    updates["logger_wifi_signal"] = signal', init_source)\n        self.assertIn('if refreshed.wifi_signal is not None:\\n                    updates["logger_wifi_signal"] = refreshed.wifi_signal', init_source)\n\n'''
new = '''    def test_failed_http_signal_has_bounded_stale_window(self) -> None:\n        init_source = (ROOT / "custom_components/tsun_local/__init__.py").read_text(encoding="utf-8")\n        self.assertNotIn('signal if signal is not None else 0', init_source)\n        self.assertNotIn('updates["logger_wifi_signal"] = 0', init_source)\n        self.assertIn('wifi_signal_freshness.observe(None)', init_source)\n        self.assertIn('async_remove_logger_metadata', init_source)\n        self.assertIn('updates["logger_wifi_signal"] = signal', init_source)\n\n'''
if old not in contract:
    raise SystemExit("legacy Wi-Fi contract block not found")
contract_path.write_text(contract.replace(old, new, 1), encoding="utf-8")
