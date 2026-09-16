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
        self.assertEqual(retry.DEFAULT_UPLOAD_ATTEMPTS, 5)
        self.assertEqual(retry.DEFAULT_RETRY_DELAYS, (0.75, 2.0, 5.0, 10.0))

    def test_transport_failure_is_retried_and_then_succeeds(self) -> None:
        transient = base.ReportUploadError("upload service is unreachable")
        transient.__cause__ = error.URLError("temporary DNS failure")
        success = {"ok": True, "report_id": "TSL-TEST"}
        with mock.patch.object(
            retry,
            "_ORIGINAL_UPLOAD_FILE",
            side_effect=[transient, transient, success],
        ) as original:
            sleeps: list[float] = []
            result = retry.upload_file_with_retry(
                Path("report.json"),
                consent=True,
                attempts=3,
                retry_delays=(0.1, 0.2),
                sleep=sleeps.append,
            )
        self.assertEqual(result, success)
        self.assertEqual(original.call_count, 3)
        self.assertEqual(sleeps, [0.1, 0.2])

    def test_retry_callback_reports_attempt_and_delay(self) -> None:
        transient = base.ReportUploadError("upload service is unreachable")
        transient.__cause__ = error.URLError("temporary DNS failure")
        success = {"ok": True, "report_id": "TSL-TEST"}
        retry_events: list[tuple[int, int, float]] = []
        with mock.patch.object(
            retry,
            "_ORIGINAL_UPLOAD_FILE",
            side_effect=[transient, success],
        ):
            retry.upload_file_with_retry(
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
        transient = base.ReportUploadError("upload service is unreachable")
        transient.__cause__ = error.URLError("temporary DNS failure")
        with mock.patch.object(
            retry,
            "_ORIGINAL_UPLOAD_FILE",
            side_effect=transient,
        ):
            with self.assertRaisesRegex(
                base.ReportUploadError,
                "Network/timeout: upload service could not be reached.*still saved locally",
            ):
                retry.upload_file_with_retry(
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
        with mock.patch.object(
            retry,
            "_ORIGINAL_UPLOAD_FILE",
            side_effect=permanent,
        ) as original:
            with self.assertRaises(base.ReportUploadError):
                retry.upload_file_with_retry(
                    Path("report.json"),
                    consent=True,
                    attempts=3,
                    retry_delays=(),
                )
        self.assertEqual(original.call_count, 1)

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
        with mock.patch.object(
            retry,
            "_ORIGINAL_UPLOAD_FILE",
            side_effect=transient,
        ) as original:
            with self.assertRaisesRegex(
                base.ReportUploadError,
                r"Upload service reached but temporarily unavailable \(HTTP 503\).*still saved locally",
            ):
                retry.upload_file_with_retry(
                    Path("diagnostic.json"),
                    consent=True,
                    attempts=3,
                    retry_delays=(),
                )
        self.assertEqual(original.call_count, 3)

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
        with mock.patch.object(
            retry,
            "_ORIGINAL_UPLOAD_FILE",
            side_effect=[transient, success],
        ):
            result = retry.upload_file_with_retry(
                Path("report.json"),
                consent=True,
                attempts=2,
                retry_delays=(0.1,),
                sleep=sleeps.append,
            )
        self.assertEqual(result, success)
        self.assertEqual(sleeps, [retry.MAX_RETRY_AFTER_SECONDS])

    def test_desktop_entry_point_installs_retry_wrapper(self) -> None:
        import tsun_diagnostic as desktop

        self.assertIs(base.upload_file, retry.upload_file_with_retry)
        self.assertEqual(desktop.APP_VERSION, "1.5.19")


if __name__ == "__main__":
    unittest.main()
