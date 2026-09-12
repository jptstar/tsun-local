# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Regression tests for Home Assistant Activity noise reduction."""

from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).parents[1]


class ActivityVisibilityTests(unittest.TestCase):
    def test_raw_helpers_are_hidden_without_removing_entities(self) -> None:
        source = (ROOT / "custom_components/tsun_local/sensor.py").read_text(encoding="utf-8")
        raw_alarm = source[source.index("def _raw_alarm("):source.index("def _raw_register(")]
        raw_register = source[source.index("def _raw_register("):source.index("def _diagnostic_power(")]
        advanced = source[source.index("def _advanced_diagnostic("):source.index("def _field_validation_diagnostic(")]
        self.assertIn("entity_registry_visible_default=False", raw_alarm)
        self.assertIn("entity_registry_visible_default=False", raw_register)
        self.assertIn('entity_registry_visible_default=not key.endswith("_raw")', advanced)

    def test_last_success_is_hidden_but_enabled(self) -> None:
        source = (ROOT / "custom_components/tsun_local/sensor.py").read_text(encoding="utf-8").splitlines()
        key_line = '        key="communication_last_success",'
        index = source.index(key_line)
        start = index
        while source[start] != "    TsunSensorDescription(":
            start -= 1
        end = index
        while source[end] != "    ),":
            end += 1
        block = source[start:end]
        self.assertIn("        entity_registry_visible_default=False,", block)
        self.assertNotIn("        entity_registry_enabled_default=False,", block)

    def test_existing_entries_get_one_time_visibility_migration(self) -> None:
        source = (ROOT / "custom_components/tsun_local/__init__.py").read_text(encoding="utf-8")
        self.assertIn('key != "communication_last_success" and not key.endswith("_raw")', source)
        self.assertIn("RegistryEntryHider.INTEGRATION", source)
        self.assertIn("_ACTIVITY_VISIBILITY_VERSION_KEY", source)


if __name__ == "__main__":
    unittest.main()
