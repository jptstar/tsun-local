from __future__ import annotations

import json
from pathlib import Path
import sys
import types
import unittest
from unittest import mock

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import tsun_1097_research_probe as probe  # noqa: E402


class Research1097ProbeTests(unittest.TestCase):
    def _args(self, *, protocol: str = "auto", full: bool = True):
        return types.SimpleNamespace(
            protocol=protocol,
            full=full,
            timeout=1.0,
            tcp_scan_timeout=0.1,
            http_page_timeout=0.5,
            interval=0.0,
            model=None,
            port=8899,
        )

    def _discovery(self, **overrides):
        value = {
            "attempted": True,
            "devices_found": 1,
            "host_discovered": True,
            "monitor_sn_discovered": False,
            "target_index": 1,
            "multi_device_scan": False,
            "sources": ["http80"],
            "firmware_version": "LSW5_01_1097_SS_05_02.00.00.0F",
            "protocol_hint": "1097",
        }
        value.update(overrides)
        return value

    def test_trigger_requires_exact_transport_change_shape(self) -> None:
        error = RuntimeError(
            "No supported TSUN local protocol detected after 3 attempts per protocol"
        )
        self.assertTrue(probe._is_eligible_failure(self._args(), self._discovery(), error))
        self.assertFalse(
            probe._is_eligible_failure(
                self._args(), self._discovery(sources=["http80", "tcp8899"]), error
            )
        )
        self.assertFalse(
            probe._is_eligible_failure(
                self._args(),
                self._discovery(
                    firmware_version="LSW5_SSL_02B0_1.04", protocol_hint="02b0"
                ),
                error,
            )
        )
        self.assertFalse(
            probe._is_eligible_failure(
                self._args(protocol="02b0"), self._discovery(), error
            )
        )
        self.assertFalse(
            probe._is_eligible_failure(
                self._args(), self._discovery(), RuntimeError("different failure")
            )
        )

    def test_successful_normal_capture_is_never_replaced(self) -> None:
        expected = {"metadata": {"detected_protocol": "1097"}}
        fake = types.SimpleNamespace(
            capture=mock.Mock(return_value=expected),
            _research_1097_probe_installed=False,
        )
        probe.install(fake)
        with mock.patch.object(probe, "capture_research") as research:
            result = fake.capture(self._args(), "192.0.2.50", 1234, self._discovery())
        self.assertIs(result, expected)
        research.assert_not_called()

    def test_non_1097_failure_is_reraised_without_research(self) -> None:
        failure = RuntimeError(
            "No supported TSUN local protocol detected after 3 attempts per protocol"
        )
        fake = types.SimpleNamespace(
            capture=mock.Mock(side_effect=failure),
            _research_1097_probe_installed=False,
        )
        probe.install(fake)
        discovery = self._discovery(
            firmware_version="LSW5_SSL_02B0_1.04", protocol_hint="02b0"
        )
        with mock.patch.object(probe, "capture_research") as research:
            with self.assertRaises(RuntimeError):
                fake.capture(self._args(), "192.0.2.50", 1234, discovery)
        research.assert_not_called()

    def test_eligible_1097_failure_switches_to_isolated_research(self) -> None:
        failure = RuntimeError(
            "No supported TSUN local protocol detected after 3 attempts per protocol"
        )
        fake = types.SimpleNamespace(
            capture=mock.Mock(side_effect=failure),
            _research_1097_probe_installed=False,
        )
        expected = {"metadata": {"detected_protocol": "1097-research"}}
        probe.install(fake)
        with mock.patch.object(probe, "capture_research", return_value=expected) as research:
            result = fake.capture(self._args(), "192.0.2.50", 1234, self._discovery())
        self.assertIs(result, expected)
        research.assert_called_once()

    def test_bounded_scan_never_becomes_a_65535_port_scan(self) -> None:
        standard = probe._ports_to_scan(False)
        extended = probe._ports_to_scan(True)
        self.assertLess(len(standard), 40)
        self.assertLess(len(extended), 3000)
        self.assertIn(8899, standard)
        self.assertIn(48899, standard)
        self.assertIn(49999, standard)
        self.assertNotEqual(len(extended), 65535)

    def test_only_safe_udp_discovery_command_is_defined(self) -> None:
        self.assertEqual(probe.SMARTLINKFIND_PAYLOAD, b"smartlinkfind")
        source = Path(probe.__file__).read_text(encoding="utf-8")
        self.assertNotIn('b"smart_config"', source)
        self.assertNotIn('b"config_ack"', source)
        self.assertEqual(probe.AT_UPURL_QUERY, b"AT+UPURL\n")
        self.assertNotIn(b"=", probe.AT_UPURL_QUERY)

    def test_research_report_keeps_network_evidence_anonymous_and_read_only(self) -> None:
        fake_dump = types.SimpleNamespace(
            DUMP_FORMAT="tsun-local-hardware-dump",
            SCHEMA_VERSION=3,
            TOOL_VERSION="2.8.5",
            SOURCE_URL="https://example.invalid/tsun_dump.py",
            analyze_snapshots=lambda snapshots: {
                "changing_registers": [],
                "stable_registers": [],
                "zero_registers": [],
                "ffff_registers": [],
                "incomplete_registers": [],
            },
            capture_logger_web_pages=lambda host, timeout: {
                "attempted": True,
                "pages_found": 1,
                "privacy": {
                    "raw_html_stored": False,
                    "host_ip_stored": False,
                },
            },
        )
        host = "192.0.2.50"
        with (
            mock.patch.object(
                probe,
                "_smartlinkfind_probe",
                return_value={
                    "attempted": True,
                    "request": "smartlinkfind",
                    "response_count": 1,
                    "responses": [
                        {
                            "length": 31,
                            "sha256_12": "0123456789ab",
                            "kind": "text",
                            "known_markers": ["1097"],
                            "raw_payload_stored": False,
                        }
                    ],
                    "configuration_write_performed": False,
                    "raw_response_payload_stored": False,
                },
            ),
            mock.patch.object(
                probe,
                "_query_upurl_read_only",
                return_value={
                    "attempted": True,
                    "read_only": True,
                    "command": "AT+UPURL",
                    "getter_form_only": True,
                    "assignment_sent": False,
                    "ota_trigger_sent": False,
                    "external_url_contacted": False,
                    "supported": True,
                    "candidate_count": 1,
                    "url_candidates": [
                        {
                            "scheme": "https",
                            "hostname": "fw.example.com",
                            "path": "/LSW5_01_1097_SS_05_02.00.00.0F-u.bin",
                            "filename": "LSW5_01_1097_SS_05_02.00.00.0F-u.bin",
                            "sanitized_url": "https://fw.example.com/LSW5_01_1097_SS_05_02.00.00.0F-u.bin",
                            "query_stripped": True,
                            "credentials_stripped": False,
                            "fragment_stripped": False,
                            "external_url_contacted": False,
                        }
                    ],
                    "raw_response_stored": False,
                },
            ),
            mock.patch.object(
                probe,
                "_scan_tcp_ports",
                return_value={
                    "attempted": True,
                    "mode": "bounded_extended",
                    "ports_tested": 2500,
                    "open_ports": [80, 8890],
                    "per_port_timeout_seconds": 0.1,
                    "full_65535_scan_performed": False,
                },
            ),
            mock.patch.object(
                probe,
                "_http_probe",
                return_value={
                    "port": 80,
                    "status": 200,
                    "body_length": 123,
                    "body_sha256_12": "abcdef012345",
                    "body_stored": False,
                    "method": "GET",
                },
            ),
            mock.patch.object(probe, "_tls_probe") as tls_probe,
            mock.patch.object(probe, "_passive_banner_probe", return_value=None),
        ):
            document = probe.capture_research(
                fake_dump,
                self._args(),
                host,
                self._discovery(),
                "failure mentioning 192.0.2.50 must not be copied",
            )

        tls_probe.assert_not_called()
        encoded = json.dumps(document, sort_keys=True)
        self.assertNotIn(host, encoded)
        self.assertNotIn("failure mentioning", encoded)
        self.assertEqual(document["metadata"]["detected_protocol"], "1097-research")
        self.assertEqual(document["metadata"]["capture_status"], "partial_success")
        self.assertFalse(document["metadata"]["measurements_available"])
        ota = document["transport_research"]["firmware_update_url_query"]
        self.assertEqual(ota["command"], "AT+UPURL")
        self.assertTrue(ota["getter_form_only"])
        self.assertFalse(ota["assignment_sent"])
        self.assertFalse(ota["external_url_contacted"])
        safety = document["transport_research"]["safety"]
        self.assertTrue(safety["read_only"])
        self.assertTrue(safety["upurl_query_only"])
        self.assertFalse(safety["upurl_assignment_sent"])
        self.assertFalse(safety["external_firmware_url_contacted"])
        self.assertFalse(safety["smart_config_sent"])
        self.assertFalse(safety["config_ack_sent"])
        self.assertFalse(safety["http_post_performed"])
        self.assertFalse(safety["configuration_write_performed"])
        self.assertFalse(safety["inverter_write_performed"])
        self.assertFalse(safety["reboot_performed"])
        self.assertFalse(safety["firmware_update_performed"])
        self.assertFalse(safety["ota_performed"])
        self.assertFalse(safety["full_65535_tcp_scan_performed"])


if __name__ == "__main__":
    unittest.main()
