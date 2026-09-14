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

    def test_associates_unambiguous_inventory_and_tuya_leftover(self) -> None:
        diagnostics = [
            {"metadata": {"model_supplied_by_user": None}, "decoded_known_measurements": {"rated_power": 450}},
            {"metadata": {"model_supplied_by_user": None}, "decoded_known_measurements": {"rated_power": 300}},
            {"metadata": {"model_supplied_by_user": None}, "decoded_known_measurements": {"rated_power": 450}},
            {"metadata": {"model_supplied_by_user": None}, "decoded_known_measurements": {}},
        ]
        devices = [
            {"model": "TSOL-MX450", "quantity": 2},
            {"model": "TSOL-MS800", "quantity": 1},
            {"model": "TSOL-MS300", "quantity": 1},
        ]
        assigned = upload.associate_declared_models(diagnostics, devices)
        self.assertEqual(
            assigned,
            {
                0: "TSOL-MX450",
                1: "TSOL-MS300",
                2: "TSOL-MX450",
                3: "TSOL-MS800",
            },
        )
        self.assertEqual(
            diagnostics[3]["metadata"]["model_assignment"]["method"],
            "remaining_declared_inventory",
        )

    def test_same_power_families_remain_unassigned_when_ambiguous(self) -> None:
        diagnostics = [
            {"metadata": {"model_supplied_by_user": None}, "decoded_known_measurements": {"rated_power": 800}},
            {"metadata": {"model_supplied_by_user": None}, "decoded_known_measurements": {"rated_power": 800}},
        ]
        devices = [
            {"model": "TSOL-MS800", "quantity": 1},
            {"model": "TSOL-MX800", "quantity": 1},
        ]
        self.assertEqual(upload.associate_declared_models(diagnostics, devices), {})
        self.assertIsNone(diagnostics[0]["metadata"]["model_supplied_by_user"])
        self.assertIsNone(diagnostics[1]["metadata"]["model_supplied_by_user"])

    def test_inventory_count_mismatch_does_not_guess(self) -> None:
        diagnostics = [
            {"metadata": {"model_supplied_by_user": None}, "decoded_known_measurements": {"rated_power": 450}},
        ]
        devices = [{"model": "TSOL-MX450", "quantity": 2}]
        self.assertEqual(upload.associate_declared_models(diagnostics, devices), {})
        self.assertIsNone(diagnostics[0]["metadata"]["model_supplied_by_user"])

    def test_annotation_is_persisted_before_upload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tuya.json"
            path.write_text(
                json.dumps(
                    {
                        "metadata": {"model_supplied_by_user": None},
                        "decoded_known_measurements": {},
                    }
                ),
                encoding="utf-8",
            )
            assigned = upload.annotate_report_files(
                [path], [{"model": "TSOL-MS800", "quantity": 1}]
            )
            self.assertEqual(assigned, {path: "TSOL-MS800"})
            saved = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(saved["metadata"]["model_supplied_by_user"], "TSOL-MS800")
            self.assertEqual(
                saved["metadata"]["model_assignment"]["confidence"], "unambiguous"
            )

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
