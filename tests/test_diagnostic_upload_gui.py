from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest import mock

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import tsun_diagnostic_app as app  # noqa: E402


class DiagnosticUploadGuiTests(unittest.TestCase):
    def test_direct_upload_version_is_newer_than_existing_gui(self) -> None:
        self.assertEqual(app.APP_VERSION, "1.5.0")
        self.assertEqual(app.base.APP_VERSION, app.APP_VERSION)

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

    def test_manual_email_route_remains_fallback_only(self) -> None:
        self.assertIn("secours", app.base._TEXT["fr"]["send"].lower())
        self.assertIn("fallback", app.base._TEXT["en"]["send"].lower())


if __name__ == "__main__":
    unittest.main()
