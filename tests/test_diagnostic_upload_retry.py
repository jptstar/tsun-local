from __future__ import annotations

from email.message import Message
from pathlib import Path
import sys
import unittest
from unittest import mock
from urllib import error

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import tsun_report_upload as base  # noqa: E402
import tsun_report_upload_retry as retry  # noqa: E402


class DiagnosticUploadRetryTests(unittest.TestCase):
    def test_defaults_allow_five_attempts(self) -> None:
        self.assertEqual(base.DEFAULT_UPLOAD_ATTEMPTS, 5)
        self.assertEqual(base.DEFAULT_RETRY_DELAYS, (0.75, 2.0, 5.0, 10.0))
        self.assertEqual(retry.DEFAULT_UPLOAD_ATTEMPTS, base.DEFAULT_UPLOAD_ATTEMPTS)
        self.assertEqual(retry.DEFAULT_RETRY_DELAYS, base.DEFAULT_RETRY_DELAYS)

    @staticmethod
    def _transient_network_error() -> base.ReportUploadError:
        transient = base.ReportUploadError("upload service is unreachable")
        transient.__cause__ = error.URLError("temporary DNS failure")
        return transient

    def test_canonical_upload_retries_transport_failure_then_succeeds(self) -> None:
        transient = self._transient_network_error()
        success = {"ok": True, "report_id": "TSL-TEST"}
        sleeps: list[float] = []
        with (
            mock.patch.object(base, "load_diagnostic", return_value={"safe": True}),
            mock.patch.object(
                base,
                "upload_diagnostic",
                side_effect=[transient, transient, success],
            ) as upload_once,
        ):
            result = base.upload_file(
                Path("report.json"),
                consent=True,
                attempts=3,
                retry_delays=(0.1, 0.2),
                sleep=sleeps.append,
            )
        self.assertEqual(result, success)
        self.assertEqual(upload_once.call_count, 3)
        self.assertEqual(sleeps, [0.1, 0.2])

    def test_retry_callback_reports_attempt_and_delay(self) -> None:
        transient = self._transient_network_error()
        success = {"ok": True, "report_id": "TSL-TEST"}
        retry_events: list[tuple[int, int, float]] = []
        with (
            mock.patch.object(base, "load_diagnostic", return_value={"safe": True}),
            mock.patch.object(base, "upload_diagnostic", side_effect=[transient, success]),
        ):
            base.upload_file(
                Path("report.json"),
                consent=True,
                attempts=2,
                retry_delays=(0.25,),
                sleep=lambda _delay: None,
                on_retry=lambda attempt, attempts, delay: retry_events.append(
                    (attempt, attempts, delay)
                ),
            )
        self.assertEqual(retry_events, [(1, 2, 0.25)])

    def test_transport_failure_identifies_network_stage_after_final_retry(self) -> None:
        transient = self._transient_network_error()
        with (
            mock.patch.object(base, "load_diagnostic", return_value={"safe": True}),
            mock.patch.object(base, "upload_diagnostic", side_effect=transient),
        ):
            with self.assertRaisesRegex(
                base.ReportUploadError,
                "Network/timeout: upload service could not be reached.*still saved locally",
            ):
                base.upload_file(
                    Path("diagnostic.json"),
                    consent=True,
                    attempts=3,
                    retry_delays=(),
                )

    def test_permanent_http_400_is_not_retried(self) -> None:
        http_error = error.HTTPError(
            base.REPORT_UPLOAD_URL,
            400,
            "Bad Request",
            hdrs=None,
            fp=None,
        )
        permanent = base.ReportUploadError("upload rejected: HTTP 400")
        permanent.__cause__ = http_error
        with (
            mock.patch.object(base, "load_diagnostic", return_value={"safe": True}),
            mock.patch.object(base, "upload_diagnostic", side_effect=permanent) as upload_once,
        ):
            with self.assertRaises(base.ReportUploadError):
                base.upload_file(
                    Path("report.json"),
                    consent=True,
                    attempts=3,
                    retry_delays=(),
                )
        self.assertEqual(upload_once.call_count, 1)

    def test_http_503_is_retried_and_identifies_reachable_service(self) -> None:
        http_error = error.HTTPError(
            base.REPORT_UPLOAD_URL,
            503,
            "Service Unavailable",
            hdrs=None,
            fp=None,
        )
        transient = base.ReportUploadError("upload rejected: HTTP 503")
        transient.__cause__ = http_error
        with (
            mock.patch.object(base, "load_diagnostic", return_value={"safe": True}),
            mock.patch.object(base, "upload_diagnostic", side_effect=transient) as upload_once,
        ):
            with self.assertRaisesRegex(
                base.ReportUploadError,
                r"Upload service reached but temporarily unavailable \(HTTP 503\).*still saved locally",
            ):
                base.upload_file(
                    Path("diagnostic.json"),
                    consent=True,
                    attempts=3,
                    retry_delays=(),
                )
        self.assertEqual(upload_once.call_count, 3)

    def test_retry_after_header_overrides_local_backoff_and_is_bounded(self) -> None:
        headers = Message()
        headers["Retry-After"] = "120"
        http_error = error.HTTPError(
            base.REPORT_UPLOAD_URL,
            429,
            "Too Many Requests",
            hdrs=headers,
            fp=None,
        )
        transient = base.ReportUploadError("upload rejected: HTTP 429")
        transient.__cause__ = http_error
        success = {"ok": True, "report_id": "TSL-TEST"}
        sleeps: list[float] = []
        with (
            mock.patch.object(base, "load_diagnostic", return_value={"safe": True}),
            mock.patch.object(base, "upload_diagnostic", side_effect=[transient, success]),
        ):
            result = base.upload_file(
                Path("report.json"),
                consent=True,
                attempts=2,
                retry_delays=(0.1,),
                sleep=sleeps.append,
            )
        self.assertEqual(result, success)
        self.assertEqual(sleeps, [base.MAX_RETRY_AFTER_SECONDS])

    def test_legacy_retry_module_delegates_to_canonical_uploader(self) -> None:
        success = {"ok": True, "report_id": "TSL-COMPAT"}
        with mock.patch.object(base, "upload_file", return_value=success) as canonical:
            result = retry.upload_file_with_retry(
                Path("report.json"),
                consent=True,
                attempts=2,
                retry_delays=(0.1,),
            )
        self.assertEqual(result, success)
        canonical.assert_called_once()

    def test_desktop_no_longer_monkey_patches_upload_function(self) -> None:
        import tsun_diagnostic as desktop

        source = Path(desktop.__file__).read_text(encoding="utf-8")
        self.assertNotIn("report_upload.upload_file =", source)
        self.assertEqual(desktop.APP_VERSION, "1.5.21")


if __name__ == "__main__":
    unittest.main()
