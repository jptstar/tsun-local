from __future__ import annotations

from pathlib import Path
import sys
import unittest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import tsun_diagnostic_app as app  # noqa: E402
import tsun_diagnostic_desktop as desktop  # noqa: E402


class DiagnosticUploadGuiTests(unittest.TestCase):
    def test_direct_upload_desktop_version_is_current(self) -> None:
        self.assertEqual(desktop.APP_VERSION, "1.5.4")
        self.assertEqual(app.APP_VERSION, desktop.APP_VERSION)
        self.assertEqual(app.base.APP_VERSION, desktop.APP_VERSION)

    def test_french_copy_requires_explicit_consent(self) -> None:
        self.assertIn("accepte", app._TEXT["fr"]["consent"].lower())
        self.assertIn("anonym", app._TEXT["fr"]["consent"].lower())

    def test_english_copy_requires_explicit_consent(self) -> None:
        self.assertIn("agree", app._TEXT["en"]["consent"].lower())
        self.assertIn("anonym", app._TEXT["en"]["consent"].lower())

    def test_upload_uses_worker_client_and_not_github_credentials(self) -> None:
        source = Path(app.__file__).read_text(encoding="utf-8")
        self.assertIn("report_upload.upload_file", source)
        self.assertNotIn("GITHUB_PRIVATE_KEY", source)
        self.assertNotIn("GITHUB_APP_ID", source)
        self.assertNotIn("GITHUB_INSTALLATION_ID", source)

    def test_manual_email_route_is_step_four_optional_fallback(self) -> None:
        self.assertTrue(app.base._TEXT["fr"]["output_title"].startswith("4 ·"))
        self.assertTrue(app.base._TEXT["en"]["output_title"].startswith("4 ·"))
        self.assertIn("optionnel", app.base._TEXT["fr"]["report_hint"].lower())
        self.assertIn("optional", app.base._TEXT["en"]["report_hint"].lower())
        self.assertTrue(app._TEXT["fr"]["title"].startswith("3 ·"))
        self.assertTrue(app._TEXT["en"]["title"].startswith("3 ·"))


if __name__ == "__main__":
    unittest.main()
