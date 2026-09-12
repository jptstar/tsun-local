from __future__ import annotations

from pathlib import Path
import sys
import unittest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import tsun_diagnostic as desktop  # noqa: E402


class DiagnosticDesktopTestModeTests(unittest.TestCase):
    def test_magic_offsite_trigger_is_exact(self) -> None:
        self.assertEqual(desktop.previous.legacy.MAGIC_TEST_HOST, "89:89:89:89")
        self.assertEqual(desktop.previous.legacy.MAGIC_TEST_SN, "89898989")

    def test_test_report_is_explicitly_synthetic_and_read_only(self) -> None:
        source = Path(desktop.previous.legacy.__file__).read_text(encoding="utf-8")
        self.assertIn('"test_mode": True', source)
        self.assertIn('"communication_attempted": False', source)
        self.assertIn("No logger or microinverter was contacted", source)

    def test_published_report_links_are_public_worker_links_only(self) -> None:
        source = Path(desktop.ui.__file__).read_text(encoding="utf-8")
        self.assertIn('get("view_url")', source)
        self.assertIn("webbrowser.open", source)
        self.assertIn("open_published", source)
        self.assertIn("_main_report_links_host", source)
        self.assertNotIn("github_report_url", source)
        self.assertNotIn("open_github", source)
        self.assertNotIn("jptstar/tsun-local-reports", source)

    def test_sunology_play_2_is_available(self) -> None:
        self.assertEqual(desktop.SUNOLOGY_PLAY2_MODEL, "Sunology PLAY 2")
        self.assertIn(
            desktop.SUNOLOGY_PLAY2_MODEL,
            desktop.previous.legacy.upload_app.TSUN_MICROINVERTER_MODELS,
        )

    def test_desktop_version_was_bumped(self) -> None:
        self.assertEqual(desktop.APP_VERSION, "1.5.12")
        self.assertEqual(desktop.previous.legacy.base.APP_VERSION, "1.5.12")
        self.assertEqual(desktop.previous.legacy.upload_app.APP_VERSION, "1.5.12")

    def test_cross_platform_update_components_are_explicit(self) -> None:
        self.assertEqual(
            desktop.platform_update_component(system="Windows", machine="AMD64"),
            "windows_gui",
        )
        self.assertEqual(
            desktop.platform_update_component(system="Darwin", machine="arm64"),
            "macos_arm64_gui",
        )
        self.assertEqual(
            desktop.platform_update_component(system="Darwin", machine="x86_64"),
            "macos_x86_64_gui",
        )
        self.assertEqual(
            desktop.platform_update_component(system="Linux", machine="x86_64"),
            "linux_x86_64_gui",
        )
        self.assertEqual(
            desktop.platform_update_component(system="Linux", machine="aarch64"),
            "linux_arm64_gui",
        )


if __name__ == "__main__":
    unittest.main()
