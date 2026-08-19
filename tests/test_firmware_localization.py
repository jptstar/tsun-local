from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).parents[1]
COMPONENT = ROOT / "custom_components" / "tsun_local"

EXPECTED = {
    "en.json": ("DSP firmware version", "QCPU1 firmware version", "QCPU2 firmware version"),
    "fr.json": ("Version du firmware DSP", "Version du firmware QCPU1", "Version du firmware QCPU2"),
    "de.json": ("DSP-Firmwareversion", "QCPU1-Firmwareversion", "QCPU2-Firmwareversion"),
    "es.json": ("Versión del firmware DSP", "Versión del firmware QCPU1", "Versión del firmware QCPU2"),
    "it.json": ("Versione firmware DSP", "Versione firmware QCPU1", "Versione firmware QCPU2"),
    "nl.json": ("DSP-firmwareversie", "QCPU1-firmwareversie", "QCPU2-firmwareversie"),
    "pl.json": ("Wersja oprogramowania DSP", "Wersja oprogramowania QCPU1", "Wersja oprogramowania QCPU2"),
    "zh-Hans.json": ("DSP 固件版本", "QCPU1 固件版本", "QCPU2 固件版本"),
}
KEYS = ("dsp_firmware_version", "qcpu1_firmware_version", "qcpu2_firmware_version")


class FirmwareLocalizationTests(unittest.TestCase):
    def test_firmware_entities_have_all_eight_localized_names(self) -> None:
        strings = json.loads((COMPONENT / "strings.json").read_text(encoding="utf-8"))
        sensors = strings["entity"]["sensor"]
        self.assertEqual(tuple(sensors[key]["name"] for key in KEYS), EXPECTED["en.json"])
        for filename, expected in EXPECTED.items():
            translated = json.loads(
                (COMPONENT / "translations" / filename).read_text(encoding="utf-8")
            )["entity"]["sensor"]
            self.assertEqual(tuple(translated[key]["name"] for key in KEYS), expected)

    def test_firmware_entity_ids_remain_stable_english(self) -> None:
        source = (COMPONENT / "sensor.py").read_text(encoding="utf-8")
        for key in KEYS:
            self.assertIn(f'key="{key}"', source)
            self.assertIn(f'suggested_object_id="{key}"', source)
            self.assertIn(f'translation_key="{key}"', source)


if __name__ == "__main__":
    unittest.main()
