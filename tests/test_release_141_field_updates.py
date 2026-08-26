from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from custom_components.tsun_local.protocols.protocol_02b0 import decode_02b0  # noqa: E402
from custom_components.tsun_local.protocols.protocol_1097 import decode_1097  # noqa: E402
from custom_components.tsun_local.protocols.protocol_1511 import decode_1511  # noqa: E402


class Release141FieldUpdateTests(unittest.TestCase):
    def test_1511_temperatures_are_semantic_entities(self) -> None:
        values = decode_1511(
            {
                0x0BC9: 245,
                0x0BCA: 0x55AA,
                0x0BD4: 321,
            }
        )
        self.assertEqual(values["inverter_temperature"], 24.5)
        self.assertEqual(values["register_3018_raw"], 0x55AA)
        self.assertEqual(values["ambient_temperature"], 32.1)
        self.assertNotIn("register_3017_raw", values)
        self.assertNotIn("register_3028_raw", values)

    def test_1511_unvalidated_power_level_candidate_is_removed(self) -> None:
        values = decode_1511({0x0FB9: 1024})
        self.assertNotIn("power_level", values)
        source = (
            ROOT / "custom_components/tsun_local/protocols/protocol_1511.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn('"power_level"', source)

    def test_02b0_power_level_scaling(self) -> None:
        self.assertEqual(
            decode_02b0({0x300A: 1000})["output_coefficient"], 100.0
        )
        self.assertEqual(
            decode_02b0({0x300A: 1024})["output_coefficient"], 100.0
        )

    def test_1097_power_level_remains_experimental(self) -> None:
        self.assertEqual(
            decode_1097({0x1423: 1000})["output_coefficient"], 100.0
        )
        self.assertEqual(
            decode_1097({0x1423: 1024})["output_coefficient"], 100.0
        )
        source = (
            ROOT / "custom_components/tsun_local/protocols/protocol_1097.py"
        ).read_text(encoding="utf-8")
        self.assertIn("Experimental 1097 power-level field", source)

    def test_141_registry_cleanup_and_percentage_migration(self) -> None:
        source = (ROOT / "custom_components/tsun_local/__init__.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('(\"register_3017_raw\", \"register_3028_raw\")', source)
        self.assertIn("CONF_UNIT_OF_MEASUREMENT", source)
        self.assertIn("PERCENTAGE", source)
        self.assertIn("unit_of_measurement=PERCENTAGE", source)

    def test_release_and_compatibility_policy(self) -> None:
        """Keep old release notes immutable without freezing the current website."""
        release = (ROOT / "docs/releases/1.4.1.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        site = (ROOT / "docs/index.html").read_text(encoding="utf-8")
        self.assertNotIn("MX3000D", release)
        self.assertNotIn("Field refinements in 1.4.1", release)
        self.assertNotIn("What 1.4.1 refines", release)
        self.assertIn("TSOL-MX3000D", readme)
        self.assertIn("1097", site)
        self.assertIn("Sunology PLAY2", site)
        manifest = json.loads(
            (ROOT / "custom_components/tsun_local/manifest.json").read_text(
                encoding="utf-8"
            )
        )
        version = manifest["version"]
        self.assertRegex(version, r"^\d+\.\d+\.\d+(?:-beta\.\d+)?$")
        self.assertIn(f"<strong>{version}</strong>", readme)


if __name__ == "__main__":
    unittest.main()
