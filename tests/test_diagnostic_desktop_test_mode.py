from __future__ import annotations

from pathlib import Path
import sys
import unittest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import tsun_diagnostic as desktop  # noqa: E402
import tsun_diagnostic_runtime as runtime  # noqa: E402


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
        self.assertEqual(desktop.APP_VERSION, "1.5.21")
        self.assertEqual(desktop.previous.legacy.base.APP_VERSION, "1.5.21")
        self.assertEqual(desktop.previous.legacy.upload_app.APP_VERSION, "1.5.21")

    def test_tuya_local_key_prompt_is_masked(self) -> None:
        source = Path(desktop.__file__).read_text(encoding="utf-8")
        self.assertIn("runtime.SECRET_PROMPT_PREFIX", source)
        self.assertIn('kwargs.setdefault("show", "*")', source)
        runtime_source = Path(runtime.__file__).read_text(encoding="utf-8")
        self.assertIn("tsun_tuya_probe.install", runtime_source)

    def test_research_extensions_have_one_explicit_runtime_order(self) -> None:
        self.assertEqual(
            runtime.pipeline_stage_names(),
            (
                "1097-research-fallback",
                "1097-transport-enrichment",
                "tuya-authenticated-status",
            ),
        )
        source = Path(desktop.__file__).read_text(encoding="utf-8")
        self.assertIn("_configure_diagnostic_runtime()", source)
        self.assertNotIn("tsun_1097_research_probe.install(tsun_dump)", source)
        self.assertNotIn("tsun_1097_transport_extension.install(tsun_dump)", source)
        self.assertNotIn("tsun_tuya_probe.install(", source)

    def test_supported_update_components_are_canonical(self) -> None:
        self.assertEqual(
            desktop.platform_update_component(system="Windows", machine="AMD64"),
            "windows_gui",
        )
        for system, machine in (
            ("Darwin", "arm64"),
            ("Darwin", "x86_64"),
            ("Linux", "x86_64"),
            ("Linux", "aarch64"),
        ):
            self.assertEqual(
                desktop.platform_update_component(system=system, machine=machine),
                "python_full",
            )


if __name__ == "__main__":
    unittest.main()
