from __future__ import annotations

from pathlib import Path
import sys
import unittest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import tsun_diagnostic_desktop as desktop  # noqa: E402


class DiagnosticDesktopTestModeTests(unittest.TestCase):
    def test_magic_offsite_trigger_is_exact(self) -> None:
        self.assertEqual(desktop.MAGIC_TEST_HOST, "89:89:89:89")
        self.assertEqual(desktop.MAGIC_TEST_SN, "89898989")

    def test_test_report_is_explicitly_synthetic_and_read_only(self) -> None:
        source = Path(desktop.__file__).read_text(encoding="utf-8")
        self.assertIn('"test_mode": True', source)
        self.assertIn('"communication_attempted": False', source)
        self.assertIn("No logger or microinverter was contacted", source)

    def test_published_report_link_is_supported(self) -> None:
        source = Path(desktop.__file__).read_text(encoding="utf-8")
        self.assertIn('get("view_url")', source)
        self.assertIn("webbrowser.open", source)
        self.assertIn("Open published report", source)

    def test_desktop_version_was_bumped(self) -> None:
        self.assertEqual(desktop.APP_VERSION, "1.5.6")


if __name__ == "__main__":
    unittest.main()