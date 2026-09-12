from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import tsun_diagnostic_app as app  # noqa: E402
import tsun_diagnostic as desktop  # noqa: E402


class DiagnosticUploadGuiTests(unittest.TestCase):
    def test_direct_upload_desktop_version_is_current(self) -> None:
        self.assertEqual(desktop.APP_VERSION, "1.5.12")
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

    def test_tsun_catalogue_contains_current_titan_and_sunology_models_without_duplicates(self) -> None:
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
            "Sunology PLAY 2",
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

    def test_compact_selector_uses_ten_searchable_rows_and_blocks_wheel(self) -> None:
        self.assertEqual(desktop.MAX_DEVICE_ROWS, 10)
        source = Path(desktop.previous.__file__).read_text(encoding="utf-8")
        self.assertIn("ttk.Combobox", source)
        self.assertIn('state="normal"', source)
        self.assertIn('"<KeyRelease>"', source)
        self.assertIn('"<MouseWheel>"', source)
        self.assertIn('return "break"', source)

    def test_model_filter_accepts_partial_names_and_sunology_play(self) -> None:
        ms = desktop.filter_microinverter_models("ms")
        self.assertTrue(ms)
        self.assertTrue(all("MS" in model for model in ms))
        self.assertIn("TSOL-MS300", ms)
        self.assertIn("TSOL-MS3000", ms)
        self.assertEqual(desktop.filter_microinverter_models("mp3000"), ("TSOL-MP3000",))
        self.assertIn("TSOL-MX800", desktop.filter_microinverter_models("800"))
        self.assertIn("Sunology PLAY 2", desktop.filter_microinverter_models("play"))
        self.assertIn("Sunology PLAY 2", desktop.filter_microinverter_models("sunology"))

    def test_upload_profile_is_persisted_without_consent(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "profile.json"
            devices = [
                {"model": "TSOL-MX500", "quantity": 2},
                {"model": "TSOL-MP3000", "quantity": 1},
                {"model": "Sunology PLAY 2", "quantity": 1},
            ]
            desktop.save_upload_profile("JP-test", devices, path)
            loaded = desktop.load_upload_profile(path)
            self.assertEqual(loaded["tester_name"], "JP-test")
            self.assertEqual(loaded["declared_devices"], devices)
            raw = json.loads(path.read_text(encoding="utf-8"))
            self.assertNotIn("consent", raw)
            self.assertEqual(raw["schema_version"], 1)

    def test_profile_storage_is_independent_of_executable_path(self) -> None:
        source = Path(desktop.previous.__file__).read_text(encoding="utf-8")
        self.assertIn('("LOCALAPPDATA", "APPDATA")', source)
        self.assertNotIn("sys.executable", source)
        self.assertIn("_queue_profile_save", source)

    def test_completed_upload_exposes_close_button_copy(self) -> None:
        self.assertIn("fermer", app._TEXT["fr"]["complete_close"].lower())
        self.assertIn("close", app._TEXT["en"]["complete_close"].lower())

    def test_footer_exposes_jptstar_and_github_project_link(self) -> None:
        self.assertIn("@jptstar", desktop.COPYRIGHT_TEXT)
        self.assertIn("GitHub", desktop.COPYRIGHT_TEXT)
        self.assertEqual(desktop.PROJECT_URL, "https://github.com/jptstar/tsun-local")

    def test_success_receipts_expose_only_worker_view_links(self) -> None:
        receipts = [
            {
                "report_id": "TSL-20260907-89ABCDEF",
                "path": "reports/2026/09/TSL-20260907-89ABCDEF.json",
                "view_url": "https://example.workers.dev/view/TSL-20260907-89ABCDEF?key=abc",
            },
            {
                "report_id": "TSL-20260907-01234567",
                "view_url": "https://example.workers.dev/view/TSL-20260907-01234567?key=def",
            },
        ]
        self.assertEqual(
            desktop.CleanDiagnosticApp._public_receipts(receipts),
            [
                (
                    "TSL-20260907-89ABCDEF",
                    "https://example.workers.dev/view/TSL-20260907-89ABCDEF?key=abc",
                ),
                (
                    "TSL-20260907-01234567",
                    "https://example.workers.dev/view/TSL-20260907-01234567?key=def",
                ),
            ],
        )

    def test_private_reports_repository_is_not_exposed_in_desktop_ui(self) -> None:
        source = Path(desktop.ui.__file__).read_text(encoding="utf-8")
        self.assertNotIn("jptstar/tsun-local-reports", source)
        self.assertNotIn("github_report_url", source)
        self.assertNotIn("open_github", source)
        self.assertIn("_main_report_links_host", source)
        self.assertIn('get("view_url")', source)

    def test_platform_assets_keep_windows_link_and_add_mac_linux(self) -> None:
        self.assertEqual(
            desktop.platform_release_asset(system="Windows", machine="AMD64"),
            "TSUN-Local-Diagnostic.exe",
        )
        self.assertEqual(
            desktop.platform_release_asset(system="Darwin", machine="arm64"),
            "TSUN-Local-Diagnostic-macOS-arm64.zip",
        )
        self.assertEqual(
            desktop.platform_release_asset(system="Darwin", machine="x86_64"),
            "TSUN-Local-Diagnostic-macOS-x86_64.zip",
        )
        self.assertEqual(
            desktop.platform_release_asset(system="Linux", machine="x86_64"),
            "TSUN-Local-Diagnostic-Linux-x86_64",
        )
        self.assertEqual(
            desktop.platform_release_asset(system="Linux", machine="aarch64"),
            "TSUN-Local-Diagnostic-Linux-arm64",
        )


if __name__ == "__main__":
    unittest.main()
