from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).parents[1]
PROTOCOLS_PATH = ROOT / "custom_components" / "tsun_local" / "protocols"
SPEC = importlib.util.spec_from_file_location(
    "tsun_local_release_141_protocol_tests",
    PROTOCOLS_PATH / "__init__.py",
    submodule_search_locations=[str(PROTOCOLS_PATH)],
)
assert SPEC is not None and SPEC.loader is not None
PKG = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PKG
SPEC.loader.exec_module(PKG)

from tsun_local_release_141_protocol_tests.protocol_02b0 import decode_advanced_diagnostics as decode_02b0  # noqa: E402,E501
from tsun_local_release_141_protocol_tests.protocol_1097 import decode_advanced_diagnostics as decode_1097  # noqa: E402,E501
from tsun_local_release_141_protocol_tests.protocol_1511 import decode_advanced_diagnostics as decode_1511_advanced, decode_measurements as decode_1511  # noqa: E402,E501


class Release141FieldUpdateTests(unittest.TestCase):
    def test_02b0_power_level_scaling(self) -> None:
        self.assertEqual(decode_02b0({0x202C: 1024})["output_coefficient"], 100.0)
        self.assertEqual(decode_02b0({0x202C: 512})["output_coefficient"], 50.0)

    def test_1511_temperatures_are_semantic_entities(self) -> None:
        registers = {
            0x0BB8: 1,
            0x0BC4: 2300,
            0x0BC5: 100,
            0x0BC7: 5000,
            0x0BC9: 94,
            0x0BCA: 8,
            0x0BCC: 3000,
            0x0BCD: 1000,
            0x0BCE: 100,
            0x0BCF: 0,
            0x0BD0: 100,
            0x0BD4: 92,
        }
        data = decode_1511(registers, pv_count=0)
        self.assertEqual(data["inverter_temperature"], 54)
        self.assertEqual(data["ambient_temperature"], 52)
        self.assertEqual(data["register_3018_raw"], 8)
        self.assertNotIn("register_3017_raw", data)
        self.assertNotIn("register_3028_raw", data)

    def test_1511_unvalidated_power_level_candidate_is_removed(self) -> None:
        data = decode_1511_advanced({0x07EC: 1024})
        self.assertNotIn("output_coefficient_candidate", data)

    def test_1097_power_level_remains_experimental(self) -> None:
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
        release = (ROOT / "docs/releases/1.4.1.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        site = (ROOT / "docs/index.html").read_text(encoding="utf-8")
        self.assertNotIn("MX3000D", release)
        self.assertNotIn("Field refinements in 1.4.1", release)
        self.assertNotIn("What 1.4.1 refines", release)
        self.assertIn("TSOL-MX3000D", readme)
        self.assertIn("TSOL-MX3000D", site)
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
