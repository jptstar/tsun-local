from __future__ import annotations

import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
from urllib import error

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import tsun_report_upload as upload  # noqa: E402


class _Response:
    def __init__(self, body: dict[str, object]) -> None:
        self._data = json.dumps(body).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def read(self, _limit: int = -1) -> bytes:
        return self._data


class DiagnosticReportUploadTests(unittest.TestCase):
    def test_parses_and_merges_declared_devices(self) -> None:
        devices = upload.parse_declared_devices(
            "TSOL-MX500\nTSOL-MP3000 x2\n2x tsol-mx500\n"
        )
        self.assertEqual(
            devices,
            [
                {"model": "TSOL-MP3000", "quantity": 2},
                {"model": "TSOL-MX500", "quantity": 3},
            ],
        )

    def test_rejects_excessive_merged_quantity(self) -> None:
        with self.assertRaises(upload.ReportUploadError):
            upload.parse_declared_devices("TSOL-MX500 x99\nTSOL-MX500")

    def test_requires_explicit_consent(self) -> None:
        with self.assertRaisesRegex(upload.ReportUploadError, "consent"):
            upload.build_payload({"safe": True}, consent=False)

    def test_rejects_forbidden_privacy_key_before_network(self) -> None:
        with self.assertRaisesRegex(upload.ReportUploadError, "forbidden privacy field"):
            upload.build_payload(
                {"nested": {"serial_number": "redacted"}},
                consent=True,
            )

    def test_load_file_rejects_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text("{", encoding="utf-8")
            with self.assertRaisesRegex(upload.ReportUploadError, "not valid JSON"):
                upload.load_diagnostic(path)

    def test_upload_success_returns_report_receipt(self) -> None:
        response = _Response(
            {
                "ok": True,
                "report_id": "TSL-20260907-ABCDEF12",
                "path": "reports/2026/09/TSL-20260907-ABCDEF12.json",
            }
        )
        with mock.patch.object(upload.request, "urlopen", return_value=response) as urlopen:
            result = upload.upload_diagnostic(
                {"format": "tsun-local-hardware-validation", "privacy": {"ok": True}},
                consent=True,
                tester_name="tester",
                declared_devices=[{"model": "TSOL-MX500", "quantity": 1}],
            )
        self.assertEqual(result["report_id"], "TSL-20260907-ABCDEF12")
        req = urlopen.call_args.args[0]
        sent = json.loads(req.data.decode("utf-8"))
        self.assertTrue(sent["consent"])
        self.assertEqual(sent["tester_profile"]["name"], "tester")
        self.assertEqual(sent["diagnostic"]["privacy"]["ok"], True)

    def test_upload_http_error_uses_server_message(self) -> None:
        exc = error.HTTPError(
            upload.REPORT_UPLOAD_URL,
            400,
            "Bad Request",
            hdrs=None,
            fp=io.BytesIO(b'{"ok":false,"error":"forbidden field: $.mac"}'),
        )
        with mock.patch.object(upload.request, "urlopen", side_effect=exc):
            with self.assertRaisesRegex(upload.ReportUploadError, "forbidden field"):
                upload.upload_diagnostic({"safe": True}, consent=True)


if __name__ == "__main__":
    unittest.main()
