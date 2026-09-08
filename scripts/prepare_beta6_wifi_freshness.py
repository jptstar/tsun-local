from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parents[1]
VERSION = "1.6.1-beta.6"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"{path}: expected source block not found")
    if text.count(old) != 1:
        raise SystemExit(f"{path}: expected source block is not unique")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


# Version metadata.
manifest = ROOT / "custom_components" / "tsun_local" / "manifest.json"
replace_once(manifest, '"version": "1.6.1-beta.5"', f'"version": "{VERSION}"')

# Small protocol-independent freshness policy, deliberately separate from the
# inverter protocols because logger HTTP metadata is common to 1511/02B0/1097.
freshness = ROOT / "custom_components" / "tsun_local" / "logger_wifi_freshness.py"
freshness.write_text(
    '''# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)\n'''
    '''# SPDX-License-Identifier: GPL-3.0-or-later\n\n'''
    '''"""Freshness policy for the logger Wi-Fi signal."""\n\n'''
    '''from __future__ import annotations\n\n'''
    '''from dataclasses import dataclass\n\n'''
    '''LOGGER_WIFI_MISS_THRESHOLD = 2\n\n\n'''
    '''@dataclass(slots=True)\n'''
    '''class LoggerWifiSignalFreshness:\n'''
    '''    """Expire RSSI only after repeated HTTP refresh misses."""\n\n'''
    '''    consecutive_misses: int = 0\n'''
    '''    miss_threshold: int = LOGGER_WIFI_MISS_THRESHOLD\n\n'''
    '''    def observe(self, signal: int | None) -> bool:\n'''
    '''        """Return True when a missing RSSI has become stale."""\n'''
    '''        if signal is not None:\n'''
    '''            self.consecutive_misses = 0\n'''
    '''            return False\n'''
    '''        self.consecutive_misses += 1\n'''
    '''        return self.consecutive_misses >= self.miss_threshold\n''',
    encoding="utf-8",
)

# Coordinator: allow one stale metadata key to be removed without touching
# protocol polling or the rest of the logger metadata.
coordinator = ROOT / "custom_components" / "tsun_local" / "coordinator.py"
old_coordinator = '''    def async_update_logger_metadata(\n        self, updates: dict[str, Any]\n    ) -> bool:\n        """Update logger metadata without resetting inverter polling."""\n        changed = False\n        for key, value in updates.items():\n            if value is None or self._logger_metadata.get(key) == value:\n                continue\n            self._logger_metadata[key] = value\n            if key == "inverter_serial_number":\n                self._inverter_serial_prefix = inverter_serial_prefix(str(value))\n            changed = True\n        if not changed:\n            return False\n\n        self.data = {\n            **dict(self.data or {}),\n            **self._logger_metadata,\n        }\n        self.async_update_listeners()\n        return True\n'''
new_coordinator = old_coordinator + '''\n    def async_remove_logger_metadata(self, key: str) -> bool:\n        """Remove one stale logger metadata value and notify listeners."""\n        current_data = dict(self.data or {})\n        if key not in self._logger_metadata and key not in current_data:\n            return False\n        self._logger_metadata.pop(key, None)\n        current_data.pop(key, None)\n        self.data = current_data\n        self.async_update_listeners()\n        return True\n'''
replace_once(coordinator, old_coordinator, new_coordinator)

# Integration setup: preserve one transient RSSI miss, expire after the second
# consecutive five-minute miss, and restore immediately on the next valid read.
init = ROOT / "custom_components" / "tsun_local" / "__init__.py"
replace_once(
    init,
    '''from .logger_web import (\n    async_read_logger_web_data,\n    async_read_logger_wifi_signal,\n)\n''',
    '''from .logger_web import (\n    async_read_logger_web_data,\n    async_read_logger_wifi_signal,\n)\nfrom .logger_wifi_freshness import LoggerWifiSignalFreshness\n''',
)
replace_once(
    init,
    '''    _async_sync_device_info(hass, entry, coordinator)\n\n    async def _async_refresh_logger_metadata(_now: datetime) -> None:\n''',
    '''    _async_sync_device_info(hass, entry, coordinator)\n    wifi_signal_freshness = LoggerWifiSignalFreshness()\n\n    async def _async_refresh_logger_metadata(_now: datetime) -> None:\n''',
)
old_refresh = '''        updates: dict[str, Any] = {}\n        async with coordinator.poll_lock:\n            if coordinator.data.get("logger_raw_profile") is None:\n                refreshed = await async_read_logger_web_data(hass, host)\n                for key, value in (\n                    ("logger_firmware_version", refreshed.firmware_version),\n                    ("logger_mac_address", refreshed.mac_address),\n                    ("inverter_serial_number", refreshed.inverter_serial_number),\n                    ("logger_raw_profile", refreshed.raw_profile),\n                ):\n                    if value is not None:\n                        updates[key] = value\n                if refreshed.wifi_signal is not None:\n                    updates["logger_wifi_signal"] = refreshed.wifi_signal\n            else:\n                signal = await async_read_logger_wifi_signal(hass, host)\n                if signal is not None:\n                    updates["logger_wifi_signal"] = signal\n\n        if not updates or not coordinator.async_update_logger_metadata(\n            updates\n        ):\n            return\n'''
new_refresh = '''        updates: dict[str, Any] = {}\n        signal: int | None = None\n        async with coordinator.poll_lock:\n            if coordinator.data.get("logger_raw_profile") is None:\n                refreshed = await async_read_logger_web_data(hass, host)\n                for key, value in (\n                    ("logger_firmware_version", refreshed.firmware_version),\n                    ("logger_mac_address", refreshed.mac_address),\n                    ("inverter_serial_number", refreshed.inverter_serial_number),\n                    ("logger_raw_profile", refreshed.raw_profile),\n                ):\n                    if value is not None:\n                        updates[key] = value\n                signal = refreshed.wifi_signal\n            else:\n                signal = await async_read_logger_wifi_signal(hass, host)\n\n        wifi_stale_changed = False\n        if signal is None:\n            if wifi_signal_freshness.observe(None):\n                wifi_stale_changed = coordinator.async_remove_logger_metadata(\n                    "logger_wifi_signal"\n                )\n        else:\n            wifi_signal_freshness.observe(signal)\n            updates["logger_wifi_signal"] = signal\n\n        metadata_changed = (\n            coordinator.async_update_logger_metadata(updates)\n            if updates\n            else False\n        )\n        if not metadata_changed and not wifi_stale_changed:\n            return\n'''
replace_once(init, old_refresh, new_refresh)

# Make the entity genuinely unavailable once the stale key has been removed,
# rather than available with a None/unknown native value.
sensor = ROOT / "custom_components" / "tsun_local" / "sensor.py"
replace_once(
    sensor,
    '''        if key in DIAGNOSTIC_SENSOR_KEYS:\n            return super().available\n''',
    '''        if key == "logger_wifi_signal":\n            return super().available and key in self.coordinator.data\n        if key in DIAGNOSTIC_SENSOR_KEYS:\n            return super().available\n''',
)

# Focused regression tests: one miss is tolerated, the second expires, and a
# valid read immediately resets the miss count. Also lock in the common wiring.
test_path = ROOT / "tests" / "test_logger_wifi_freshness.py"
test_path.write_text(
    '''# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)\n'''
    '''# SPDX-License-Identifier: GPL-3.0-or-later\n\n'''
    '''from __future__ import annotations\n\n'''
    '''from pathlib import Path\n'''
    '''import unittest\n\n'''
    '''from custom_components.tsun_local.logger_wifi_freshness import (\n'''
    '''    LOGGER_WIFI_MISS_THRESHOLD,\n'''
    '''    LoggerWifiSignalFreshness,\n'''
    ''')\n\n'''
    '''ROOT = Path(__file__).parents[1]\n\n\n'''
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

# Release notes and changelog.
notes = ROOT / "docs" / "releases" / f"{VERSION}.md"
notes.write_text(
    '''# TSUN Local 1.6.1-beta.6\n\n'''
    '''This beta keeps the validated beta.5 daily-energy handling unchanged and fixes logger Wi-Fi RSSI freshness across all protocol families.\n\n'''
    '''## Logger Wi-Fi signal\n\n'''
    '''- Preserve the last valid logger RSSI across one transient five-minute HTTP refresh miss.\n'''
    '''- After two consecutive RSSI refresh misses (about 10 minutes), mark **Logger Wi-Fi signal** unavailable instead of keeping an indefinitely stale value.\n'''
    '''- Never synthesize `0%` for a failed RSSI read.\n'''
    '''- Restore the real RSSI immediately on the next successful logger HTTP read.\n'''
    '''- Apply the same common logger-metadata policy to 1511, 02B0 and 1097.\n\n'''
    '''## Daily energy retained from beta.5\n\n'''
    '''- Home Assistant local midnight remains the only displayed day boundary.\n'''
    '''- Daily AC/PV energy continues from monotonic total-energy deltas and remains protected from hardware counter resets at sunrise or around 18:00.\n'''
    '''- No protocol register mapping or device write behavior is changed.\n\n'''
    '''## Safety\n\n'''
    '''TSUN Local remains local and strictly read-only. This beta changes only Home Assistant-side logger metadata freshness.\n''',
    encoding="utf-8",
)

changelog_path = ROOT / "CHANGELOG.md"
changelog = changelog_path.read_text(encoding="utf-8")
anchor = "All notable changes to this project are documented here. The project follows [Semantic Versioning](https://semver.org/).\n\n"
entry = '''## [1.6.1-beta.6] - 2026-09-09\n\n### Fixed\n\n- Preserve one transient logger RSSI HTTP miss, then mark `logger_wifi_signal` unavailable after two consecutive five-minute misses instead of retaining a stale value indefinitely.\n- Restore the real logger Wi-Fi signal immediately on the next successful metadata read and never synthesize `0%` for a failed read.\n- Apply the RSSI freshness policy in the shared logger metadata layer for 1511, 02B0 and 1097.\n\n### Retained\n\n- Keep beta.5 daily-energy rollover and total-delta tracking unchanged.\n- Keep protocol register maps, adaptive polling, communication resilience and strictly read-only device access unchanged.\n\n'''
if entry not in changelog:
    if anchor not in changelog:
        raise SystemExit("CHANGELOG.md header anchor not found")
    changelog = changelog.replace(anchor, anchor + entry, 1)
link = "[1.6.1-beta.6]: https://github.com/jptstar/tsun-local/releases/tag/v1.6.1-beta.6\n"
if link not in changelog:
    changelog = changelog.rstrip() + "\n" + link
changelog_path.write_text(changelog, encoding="utf-8")
