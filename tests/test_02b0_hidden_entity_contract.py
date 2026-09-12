from __future__ import annotations

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).parents[1]


class Hidden02b0EntityContractTests(unittest.TestCase):
    def test_entities_are_disabled_by_default(self) -> None:
        source = (ROOT / "custom_components/tsun_local/sensor.py").read_text(encoding="utf-8")
        for key in (
            "solar_plant_rated_power",
            "zero_export_status",
            "zero_export_power_offset",
        ):
            match = re.search(
                rf'key="{key}".*?entity_registry_enabled_default=False',
                source,
                flags=re.DOTALL,
            )
            self.assertIsNotNone(match, key)

    def test_register_addresses_are_documented_in_sensor_metadata(self) -> None:
        source = (ROOT / "custom_components/tsun_local/sensor.py").read_text(encoding="utf-8")
        for key, address in {
            "solar_plant_rated_power": "0x2047",
            "zero_export_status": "0x2048",
            "zero_export_power_offset": "0x204A",
        }.items():
            self.assertIn(f'"{key}": "{address}"', source)


if __name__ == "__main__":
    unittest.main()
