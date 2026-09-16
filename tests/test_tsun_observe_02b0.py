from __future__ import annotations

from pathlib import Path
import sys
import unittest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import tsun_dump  # noqa: E402
import tsun_observe_02b0 as observer  # noqa: E402


class TsunObserve02B0Tests(unittest.TestCase):
    def test_compact_observation_keeps_length_and_crc_evidence(self) -> None:
        body = bytes((0x01, 0x03, 0x02, 0x12, 0x34))
        payload = body + tsun_dump.crc16_modbus(body)
        compact = observer.compact_observation(
            {
                "result": "success",
                "latency_ms": 12.5,
                "first_payload": payload.hex(" "),
                "first_payload_bytes": len(payload),
                "request_payload": "SHOULD NOT BE RETAINED",
            }
        )
        self.assertEqual(compact["result"], "success")
        self.assertNotIn("request_payload", compact)
        self.assertNotIn("first_payload", compact)
        metrics = compact["first_modbus"]
        self.assertEqual(metrics["announced_data_bytes"], 2)
        self.assertEqual(metrics["expected_response_bytes"], 7)
        self.assertTrue(metrics["length_matches"])
        self.assertTrue(metrics["crc_valid"])

    def test_compact_observation_exposes_truncated_length_before_crc_conclusion(self) -> None:
        compact = observer.compact_observation(
            {
                "result": "failure",
                "first_payload": "01 03 2E 00 01 00 02",
                "first_payload_bytes": 7,
                "error": {"type": "TsunProtocolError", "detail": "Invalid Modbus CRC"},
            }
        )
        metrics = compact["first_modbus"]
        self.assertEqual(metrics["announced_data_bytes"], 46)
        self.assertEqual(metrics["expected_response_bytes"], 51)
        self.assertFalse(metrics["length_matches"])
        self.assertFalse(metrics["crc_valid"])

    def test_summary_identifies_same_round_multi_device_failure(self) -> None:
        public_targets = [
            {"device_index": 1, "protocol": "02b0"},
            {"device_index": 2, "protocol": "02b0"},
            {"device_index": 3, "protocol": "02b0"},
        ]
        success = {"result": "success"}
        failure = {"result": "failure"}
        rounds = [
            {
                "round": 1,
                "timestamp_utc": "2026-09-16T20:00:00+00:00",
                "devices": [
                    {"device_index": 1, "minimal": success, "production": success},
                    {"device_index": 2, "minimal": success, "production": failure},
                    {"device_index": 3, "minimal": failure, "production": failure},
                ],
            }
        ]
        summary = observer.summarize_rounds(public_targets, rounds)
        self.assertEqual(
            summary["simultaneous_failure_rounds"][0]["failed_device_indexes"],
            [2, 3],
        )
        by_device = {item["device_index"]: item for item in summary["devices"]}
        self.assertEqual(by_device[1]["failed_rounds"], 0)
        self.assertEqual(by_device[2]["failed_rounds"], 1)
        self.assertEqual(by_device[3]["failed_rounds"], 1)

    def test_parser_rejects_high_rate_polling(self) -> None:
        parser = observer.build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(["--interval", "1"])


if __name__ == "__main__":
    unittest.main()
