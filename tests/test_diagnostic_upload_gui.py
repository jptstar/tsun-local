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
        self.assertEqual(desktop.APP_VERSION, "1.5.6")
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

    def test_tsun_catalogue_contains_current_and_titan_models_without_duplicates(self) -> None:
        models = app.TSUN_MICROINVERTER_MODELS
        self.assertEqual(len(models), len(set(models)))
        for expected in (
            "TSOL-MS300",
            "TSOL-MX500",
            "TSOL-MS800",
            "TSOL-MS2000",
            "TSOL-MX3300D",
            "TSOL-MX3300D-T",
            "TSOL-MS3000",
            "TSOL-MP2250",
            "TSOL-MP3000",
            "TSOL-MP6000",
            "TSOL-MG800",
            "TSOL-MG3200",
            "TSOL-ML500",
        ):
            self.assertIn(expected, models)
        self.assertLessEqual(len(models), 50)

    def test_multiple_catalogue_models_keep_independent_quantities(self) -> None:
        devices = app.build_selected_devices(
            [
                ("TSOL-MX500", True, "2"),
                ("TSOL-MS800", False, "9"),
                ("TSOL-MP3000", True, 3),
            ]
        )
        self.assertEqual(
            devices,
            [
                {"model": "TSOL-MX500", "quantity": 2},
                {"model": "TSOL-MP3000", "quantity": 3},
            ],
        )

    def test_completed_upload_exposes_close_button_copy(self) -> None:
        self.assertIn("fermer", app._TEXT["fr"]["complete_close"].lower())
        self.assertIn("close", app._TEXT["en"]["complete_close"].lower())

    def test_footer_exposes_jptstar_and_github_project_link(self) -> None:
        self.assertIn("@jptstar", desktop.COPYRIGHT_TEXT)
        self.assertIn("GitHub", desktop.COPYRIGHT_TEXT)
        self.assertEqual(desktop.PROJECT_URL, "https://github.com/jptstar/tsun-local")


if __name__ == "__main__":
    unittest.main()
