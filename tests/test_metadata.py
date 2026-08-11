# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Project metadata, privacy, and translation consistency tests."""

from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).parents[1]
INTEGRATION = ROOT / "custom_components" / "tsun_local"


def _load_json(path: Path) -> dict:
    """Load one project JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))


def _leaf_paths(value: object, prefix: tuple[str, ...] = ()) -> set[tuple[str, ...]]:
    """Return every translatable leaf path in a nested JSON object."""
    if not isinstance(value, dict):
        return {prefix}
    paths: set[tuple[str, ...]] = set()
    for key, nested_value in value.items():
        paths.update(_leaf_paths(nested_value, (*prefix, key)))
    return paths


class MetadataTests(unittest.TestCase):
    """Keep release metadata and public files synchronized."""

    def test_manifest_version_has_matching_changelog_entry(self) -> None:
        manifest = _load_json(INTEGRATION / "manifest.json")
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn(f"## [{manifest['version']}]", changelog)

    def test_translation_keys_match_strings(self) -> None:
        strings = _load_json(INTEGRATION / "strings.json")
        expected = _leaf_paths(strings) - {("title",)}
        for path in sorted((INTEGRATION / "translations").glob("*.json")):
            translated = _load_json(path)["entity"]
            translated_document = _load_json(path)
            self.assertEqual(
                _leaf_paths(translated_document),
                expected,
                f"translation keys differ in {path.name}",
            )
            self.assertEqual(set(translated), {"sensor", "binary_sensor", "button"})

    def test_documentation_language_layout(self) -> None:
        self.assertTrue((ROOT / "README.md").is_file())
        self.assertFalse((ROOT / "README_EN.md").exists())
        self.assertFalse((ROOT / "README_FR.md").exists())
        self.assertFalse((ROOT / "README_DE.md").exists())
        localized = (
            "README_FR.md",
            "README_DE.md",
            "README_ES.md",
            "README_IT.md",
            "README_NL.md",
            "README_PL.md",
            "README_ZH.md",
        )
        for name in localized:
            self.assertTrue((ROOT / "docs" / name).is_file())
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("[Français](docs/README_FR.md)", root_readme)
        self.assertIn("[Deutsch](docs/README_DE.md)", root_readme)
        version = _load_json(INTEGRATION / "manifest.json")["version"]
        self.assertIn(f"**{version}**", root_readme)
        for name in localized:
            self.assertIn(
                version,
                (ROOT / "docs" / name).read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
