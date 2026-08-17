from pathlib import Path
import unittest


class Beta8SensorMetadataTests(unittest.TestCase):
    def test_advanced_timing_entities_are_durations_in_seconds(self) -> None:
        source = Path("custom_components/tsun_local/sensor.py").read_text(encoding="utf-8")
        keys = (
            "grid_undervoltage_time_1", "grid_undervoltage_time_2",
            "grid_overvoltage_time_1", "grid_overvoltage_time_2",
            "grid_underfrequency_time_1", "grid_underfrequency_time_2",
            "grid_overfrequency_time_1", "grid_overfrequency_time_2",
            "grid_undervoltage_time_3",
        )
        for key in keys:
            start = source.index(f'    _advanced_diagnostic(\n        "{key}",')
            block = source[start:start + 320]
            self.assertIn("SensorDeviceClass.DURATION", block)
            self.assertIn("UnitOfTime.SECONDS", block)

    def test_advanced_entities_are_disabled_by_default(self) -> None:
        source = Path("custom_components/tsun_local/sensor.py").read_text(encoding="utf-8")
        self.assertIn("entity_registry_enabled_default=False", source)


if __name__ == "__main__":
    unittest.main()
