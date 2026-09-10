# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for the standalone Python diagnostic submission workflow."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from unittest import mock
import unittest


ROOT = Path(__file__).parents[1]
TOOL_PATH = ROOT / "tools" / "tsun_dump.py"
SPEC = importlib.util.spec_from_file_location("tsun_dump_upload_test", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
TOOL = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = TOOL
SPEC.loader.exec_module(TOOL)


class _Response:
    def __init__(self, payload: dict[str, object]) -> None:
        self._body = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self, _limit: int) -> bytes:
        return self._body


class TsunDumpUploadTests(unittest.TestCase):
    def test_local_privacy_gate_rejects_forbidden_fields(self) -> None:
        with self.assertRaises(TOOL.ReportUploadError):
            TOOL.validate_diagnostic_for_upload(
                {"metadata": {"safe": True}, "nested": [{"ssid": "private"}]}
            )

    def test_upload_requires_explicit_consent(self) -> None:
        with self.assertRaises(TOOL.ReportUploadError):
            TOOL.upload_diagnostic_report({"metadata": {}}, consent=False)

    def test_secure_upload_uses_worker_schema(self) -> None:
        response = _Response(
            {
                "ok": True,
                "report_id": "TSL-20260910-ABCDEF01",
                "view_url": "https://example.invalid/view/token",
            }
        )
        with mock.patch.object(TOOL.urllib.request, "urlopen", return_value=response) as urlopen:
            result = TOOL.upload_diagnostic_report(
                {"metadata": {"privacy": {"host_in_output": False}}},
                consent=True,
            )

        self.assertEqual(result["report_id"], "TSL-20260910-ABCDEF01")
        request = urlopen.call_args.args[0]
        payload = json.loads(request.data.decode("utf-8"))
        self.assertTrue(payload["consent"])
        self.assertEqual(payload["tester_profile"], {"name": "", "declared_devices": []})
        self.assertIn("diagnostic", payload)
        self.assertEqual(request.full_url, TOOL.REPORT_UPLOAD_URL)

    def test_all_files_are_privacy_checked_before_first_network_call(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            safe = Path(directory) / "safe.json"
            unsafe = Path(directory) / "unsafe.json"
            safe.write_text(json.dumps({"metadata": {"safe": True}}), encoding="utf-8")
            unsafe.write_text(json.dumps({"metadata": {"password": "secret"}}), encoding="utf-8")
            with mock.patch.object(TOOL.urllib.request, "urlopen") as urlopen:
                with self.assertRaises(TOOL.ReportUploadError):
                    TOOL._submit_completed_reports([safe, unsafe])
            urlopen.assert_not_called()

    def test_submit_and_no_submit_are_mutually_exclusive(self) -> None:
        parser = TOOL.build_parser()
        self.assertTrue(parser.parse_args(["--submit"]).submit)
        self.assertTrue(parser.parse_args(["--upload"]).submit)
        self.assertTrue(parser.parse_args(["--no-submit"]).no_submit)
        with self.assertRaises(SystemExit):
            parser.parse_args(["--submit", "--no-submit"])

    def test_desktop_engine_disables_second_cli_prompt(self) -> None:
        source = (ROOT / "tools" / "tsun_diagnostic_gui.py").read_text(encoding="utf-8")
        self.assertIn('["tsun_dump.py", "--full", "--no-submit"]', source)

    def test_explicit_submit_flag_uses_submission_path_without_prompt(self) -> None:
        args = argparse.Namespace(submit=True, no_submit=False)
        path = Path("report.json")
        with mock.patch.object(TOOL, "_submit_completed_reports") as submit:
            result = TOOL._handle_report_delivery([path], args)
        self.assertEqual(result, 0)
        submit.assert_called_once_with([path])


if __name__ == "__main__":
    unittest.main()
