from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest import mock

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import tsun_1097_research_probe as probe  # noqa: E402


class _FakeUdpSocket:
    def __init__(self, responses: list[bytes]) -> None:
        self.responses = list(responses)
        self.sent: list[bytes] = []
        self.connected = None
        self.timeout = None
        self.closed = False

    def settimeout(self, value: float) -> None:
        self.timeout = value

    def connect(self, address) -> None:
        self.connected = address

    def send(self, payload: bytes) -> int:
        self.sent.append(payload)
        return len(payload)

    def recv(self, _size: int) -> bytes:
        if not self.responses:
            raise AssertionError("unexpected recv")
        return self.responses.pop(0)

    def close(self) -> None:
        self.closed = True


class Research1097UpurlTests(unittest.TestCase):
    def test_upurl_command_is_getter_only(self) -> None:
        self.assertEqual(probe.AT_UPURL_QUERY, b"AT+UPURL\n")
        self.assertNotIn(b"=", probe.AT_UPURL_QUERY)
        source = Path(probe.__file__).read_text(encoding="utf-8")
        self.assertNotIn('b"AT+UPURL=', source)

    def test_update_url_sanitizer_keeps_firmware_path_but_strips_secrets(self) -> None:
        value = (
            "https://user:secret@fw.example.com:8443/tsun/"
            "LSW5_01_1097_SS_05_02.00.00.0F-u.bin?token=abc#download"
        )
        result = probe._sanitize_update_url(value)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["hostname"], "fw.example.com")
        self.assertEqual(result["port"], 8443)
        self.assertEqual(
            result["filename"],
            "LSW5_01_1097_SS_05_02.00.00.0F-u.bin",
        )
        self.assertEqual(
            result["sanitized_url"],
            "https://fw.example.com:8443/tsun/LSW5_01_1097_SS_05_02.00.00.0F-u.bin",
        )
        self.assertTrue(result["credentials_stripped"])
        self.assertTrue(result["query_stripped"])
        self.assertTrue(result["fragment_stripped"])
        self.assertFalse(result["external_url_contacted"])
        rendered = str(result)
        self.assertNotIn("secret", rendered)
        self.assertNotIn("token=abc", rendered)

    def test_upurl_response_extracts_only_sanitized_url(self) -> None:
        response = (
            b"+ok=https://fw.example.com/releases/"
            b"LSW5_01_1097_SS_05_02.00.00.0F-u.bin?sig=private\r\n"
        )
        result = probe._summarize_upurl_response(response)
        self.assertTrue(result["supported"])
        self.assertEqual(result["candidate_count"], 1)
        candidate = result["url_candidates"][0]
        self.assertEqual(
            candidate["sanitized_url"],
            "https://fw.example.com/releases/LSW5_01_1097_SS_05_02.00.00.0F-u.bin",
        )
        self.assertTrue(candidate["query_stripped"])
        self.assertFalse(result["raw_response_stored"])
        self.assertNotIn("sig=private", str(result))

    def test_probe_sends_only_handshake_ack_getter_and_quit(self) -> None:
        fake = _FakeUdpSocket(
            [
                b"192.0.2.10,AA:BB:CC:DD:EE:FF,HF-LPX70",
                b"+ok=https://fw.example.com/LSW5_01_1097_SS_05_02.00.00.0F-u.bin\r\n",
            ]
        )
        with (
            mock.patch.object(probe.socket, "socket", return_value=fake),
            mock.patch.object(probe.time, "sleep"),
        ):
            result = probe._query_upurl_read_only("192.0.2.10", 1.0)

        self.assertTrue(result["supported"])
        self.assertTrue(result["getter_form_only"])
        self.assertFalse(result["assignment_sent"])
        self.assertFalse(result["ota_trigger_sent"])
        self.assertFalse(result["external_url_contacted"])
        self.assertEqual(
            fake.sent,
            [
                probe.AT_DISCOVERY_MESSAGES[0],
                b"+ok",
                probe.AT_UPURL_QUERY,
                probe.AT_QUIT,
            ],
        )
        self.assertNotIn(b"=", probe.AT_UPURL_QUERY)


if __name__ == "__main__":
    unittest.main()
