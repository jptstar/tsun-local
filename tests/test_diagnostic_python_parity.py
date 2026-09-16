from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import tsun_diagnostic as desktop  # noqa: E402
import tsun_diagnostic_cli as python_cli  # noqa: E402
import tsun_diagnostic_runtime as runtime  # noqa: E402
import tsun_dump  # noqa: E402
import tsun_report_upload as report_upload  # noqa: E402


class DiagnosticPythonParityTests(unittest.TestCase):
    def test_python_and_desktop_publish_same_application_version(self) -> None:
        self.assertEqual(python_cli.APP_VERSION, desktop.APP_VERSION)

    def test_python_uses_exact_desktop_runtime_pipeline(self) -> None:
        self.assertIs(python_cli.runtime, runtime)
        self.assertEqual(
            python_cli.runtime.pipeline_stage_names(),
            runtime.pipeline_stage_names(),
        )
        desktop_source = Path(desktop.__file__).read_text(encoding="utf-8")
        python_source = Path(python_cli.__file__).read_text(encoding="utf-8")
        self.assertIn("runtime.configure_dump_extensions", desktop_source)
        self.assertIn("runtime.configure_dump_extensions", python_source)
        self.assertIn("getpass(prompt)", python_source)

    def test_python_routes_upload_through_canonical_retry_uploader(self) -> None:
        original_submit = tsun_dump._submit_completed_reports
        had_marker = hasattr(tsun_dump, "_full_python_upload_installed")
        original_marker = getattr(tsun_dump, "_full_python_upload_installed", None)
        try:
            if had_marker:
                delattr(tsun_dump, "_full_python_upload_installed")
            with (
                mock.patch.object(report_upload, "annotate_report_files") as annotate,
                mock.patch.object(
                    report_upload,
                    "upload_file",
                    return_value={
                        "ok": True,
                        "report_id": "TSL-PARITY",
                        "view_url": "https://example.invalid/report/TSL-PARITY",
                    },
                ) as upload,
            ):
                python_cli._install_canonical_upload()
                tsun_dump._submit_completed_reports(
                    [Path("report.json")],
                    tester_name="tester",
                    declared_devices=[{"model": "TSOL-MS800", "quantity": 1}],
                )
                annotate.assert_called_once()
                kwargs = upload.call_args.kwargs
                self.assertTrue(kwargs["consent"])
                self.assertEqual(kwargs["tester_name"], "tester")
                self.assertEqual(
                    kwargs["declared_devices"],
                    [{"model": "TSOL-MS800", "quantity": 1}],
                )
                self.assertEqual(
                    kwargs["user_agent"],
                    f"TSUN-Local-Diagnostic-Python/{desktop.APP_VERSION}",
                )
                self.assertIs(kwargs["on_retry"], python_cli._retry_notice)
        finally:
            tsun_dump._submit_completed_reports = original_submit
            if had_marker:
                tsun_dump._full_python_upload_installed = original_marker
            elif hasattr(tsun_dump, "_full_python_upload_installed"):
                delattr(tsun_dump, "_full_python_upload_installed")

    def test_python_update_component_is_full_bundle_not_legacy_dump(self) -> None:
        self.assertEqual(python_cli.PYTHON_UPDATE_COMPONENT, "python_full")
        self.assertEqual(
            python_cli.PYTHON_RELEASE_ASSET,
            "TSUN-Local-Diagnostic-Python.zip",
        )

    def test_official_build_uses_same_tuya_backend_on_windows_and_macos(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "build-diagnostic-exe.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("tinytuya==1.20.0", workflow)
        self.assertIn("--collect-all tinytuya", workflow)

    def test_community_macos_build_keeps_same_tuya_backend(self) -> None:
        workflow = (
            ROOT / ".github" / "workflows" / "build-diagnostic-macos-community.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("tinytuya==1.20.0", workflow)
        self.assertIn("--collect-all tinytuya", workflow)

    def test_python_bundle_is_built_from_same_runtime_sources(self) -> None:
        workflow = (
            ROOT / ".github" / "workflows" / "build-diagnostic-python.yml"
        ).read_text(encoding="utf-8")
        for filename in (
            "tsun_dump.py",
            "tsun_diagnostic_cli.py",
            "tsun_diagnostic_runtime.py",
            "tsun_diagnostic_version.py",
            "tsun_1097_research_probe.py",
            "tsun_1097_transport_extension.py",
            "tsun_tuya_probe.py",
            "tsun_report_upload.py",
        ):
            self.assertIn(filename, workflow)
        self.assertIn("tinytuya==1.20.0", workflow)
        self.assertIn("python_full", workflow)
        self.assertIn("TSUN-Local-Diagnostic-Python.zip", workflow)


if __name__ == "__main__":
    unittest.main()
