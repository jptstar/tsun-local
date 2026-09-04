# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Release-contract tests for TSUN Local 1.6.0-beta.2."""

from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).parents[1]


class Beta2ReleaseContractTests(unittest.TestCase):
    def test_beta2_defaults(self) -> None:
        const = (ROOT / "custom_components/tsun_local/const.py").read_text(encoding="utf-8")
        self.assertIn("DEFAULT_SCAN_INTERVAL = 20", const)
        self.assertIn("DEFAULT_ERROR_SCAN_INTERVAL = 30", const)
        self.assertIn("DEFAULT_OFFLINE_SCAN_INTERVAL = 300", const)
        self.assertIn("DEFAULT_FAILURE_THRESHOLD = 3", const)
        self.assertIn("DEFAULT_ADAPTIVE_POLLING = True", const)

    def test_manifest_version(self) -> None:
        manifest = json.loads((ROOT / "custom_components/tsun_local/manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["version"], "1.6.0-beta.2")

    def test_failed_http_signal_is_not_kept_stale(self) -> None:
        init_source = (ROOT / "custom_components/tsun_local/__init__.py").read_text(encoding="utf-8")
        self.assertIn("signal if signal is not None else 0", init_source)
        self.assertIn("if refreshed.wifi_signal is not None\n                    else 0", init_source)

    def test_communication_sensor_visibility(self) -> None:
        source = (ROOT / "custom_components/tsun_local/sensor.py").read_text(encoding="utf-8").splitlines()

        def block(key: str) -> list[str]:
            key_line = f'        key="{key}",'
            index = source.index(key_line)
            start = index
            while source[start] != "    TsunSensorDescription(":
                start -= 1
            end = index
            while source[end] != "    ),":
                end += 1
            return source[start:end]

        visible = {"communication_last_success", "communication_failures", "adaptive_polling_interval", "adaptive_polling_state"}
        advanced = {"communication_duration", "communication_blocks", "communication_successes_consecutive", "adaptive_polling_reason", "adaptive_backoff_events"}
        for key in visible:
            self.assertNotIn("        entity_registry_enabled_default=False,", block(key), key)
        for key in advanced:
            self.assertIn("        entity_registry_enabled_default=False,", block(key), key)

    def test_french_polling_labels(self) -> None:
        fr = json.loads((ROOT / "custom_components/tsun_local/translations/fr.json").read_text(encoding="utf-8"))
        options = fr["options"]["step"]["init"]
        self.assertEqual(options["title"], "Réglages de la relève")
        self.assertEqual(options["data"]["adaptive_polling"], "Relève adaptative")
        self.assertEqual(options["data"]["error_scan_interval"], "Intervalle après erreur")
        self.assertEqual(options["data"]["offline_scan_interval"], "Hors ligne / nuit")
        sensors = fr["entity"]["sensor"]
        self.assertEqual(sensors["adaptive_polling_state"]["name"], "Communication — État")
        self.assertEqual(sensors["communication_last_success"]["name"], "Communication — Dernière réponse")
        self.assertEqual(sensors["communication_failures"]["name"], "Communication — Échecs")
        self.assertEqual(sensors["adaptive_polling_interval"]["name"], "Communication — Intervalle")
        self.assertEqual(sensors["adaptive_backoff_events"]["name"], "Communication — Ralentissements")
        self.assertEqual(sensors["country_profile_raw"]["name"], sensors["product_compliance_type_raw"]["name"])


if __name__ == "__main__":
    unittest.main()
