from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


TOOL_PATH = Path(__file__).parents[1] / "tools" / "tsun_dump.py"
SPEC = importlib.util.spec_from_file_location("tsun_dump_update_test", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
TOOL = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = TOOL
SPEC.loader.exec_module(TOOL)


class DiagnosticUpdateTests(unittest.TestCase):
    def _manifest(self, *, version: str = "9.0.0", asset: str = "tsun_dump.py", payload: bytes = b"new") -> dict:
        return {
            "schema_version": 1,
            "build_commit": "abc123",
            "components": {
                "dump": {
                    "version": version,
                    "asset": asset,
                    "sha256": hashlib.sha256(payload).hexdigest(),
                }
            },
        }

    def test_version_comparison_is_numeric(self) -> None:
        self.assertGreater(TOOL._version_key("2.10.0"), TOOL._version_key("2.9.9"))
        self.assertEqual(TOOL._version_key("2.7"), (2, 7, 0, 0))

    def test_selects_only_a_newer_component(self) -> None:
        manifest = self._manifest(version="2.8.0")
        update = TOOL.select_update_component(manifest, "dump", "2.7.0")
        self.assertIsNotNone(update)
        assert update is not None
        self.assertEqual(update["version"], "2.8.0")
        self.assertIsNone(TOOL.select_update_component(manifest, "dump", "2.8.0"))
        self.assertIsNone(TOOL.select_update_component(manifest, "dump", "2.9.0"))

    def test_rejects_unsafe_asset_names(self) -> None:
        manifest = self._manifest(asset="../tsun_dump.py")
        with self.assertRaises(TOOL.TsunUpdateError):
            TOOL.select_update_component(manifest, "dump", "2.7.0")

    def test_download_is_written_only_after_hash_validation(self) -> None:
        payload = b"verified update payload"
        manifest = self._manifest(payload=payload)
        update = TOOL.select_update_component(manifest, "dump", "2.7.0")
        assert update is not None
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "tsun_dump.py"
            with patch.object(TOOL, "_download_bytes", return_value=payload):
                TOOL.download_verified_update(update, destination)
            self.assertEqual(destination.read_bytes(), payload)

    def test_hash_mismatch_does_not_replace_destination(self) -> None:
        expected = b"expected"
        actual = b"tampered"
        manifest = self._manifest(payload=expected)
        update = TOOL.select_update_component(manifest, "dump", "2.7.0")
        assert update is not None
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "tsun_dump.py"
            destination.write_bytes(b"old")
            with patch.object(TOOL, "_download_bytes", return_value=actual):
                with self.assertRaises(TOOL.TsunUpdateError):
                    TOOL.download_verified_update(update, destination)
            self.assertEqual(destination.read_bytes(), b"old")

    def test_cli_exposes_update_controls(self) -> None:
        parser = TOOL.build_parser()
        self.assertTrue(parser.parse_args(["--no-update"]).no_update)
        self.assertTrue(parser.parse_args(["--check-update"]).check_update)


if __name__ == "__main__":
    unittest.main()
