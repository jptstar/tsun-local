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

    def test_web_transport_snapshot_extracts_config_without_server_hosts(self) -> None:
        document = """
        <script>
        var yz_tmode = "cmd";
        var server_a = ",iot.example.invalid,10443,TCP";
        var server_b = "192.0.2.77,,9000,UDP";
        var uart_setting_baud = "115200";
        var uart_setting_data = "databit_8";
        var uart_setting_parity = "none";
        var uart_setting_stop = "stopbit_1";
        var uart_setting_fc = "NFC";
        var net_setting_pro = "TCP";
        var net_setting_cs = "SERVER";
        var net_setting_port = "8899";
        var net_setting_ip = "192.0.2.50";
        var net_setting_to = "300";
        var inv_set = "4247,1,1";
        var apsta_mode = "0";
        var inv_tp = "4247:Tengsheng_G4";
        var inv_tp_seld = "";
        </script>
        """
        result = probe._extract_logger_web_transport_settings(
            {
                "pages": [
                    {
                        "path": "/hide_set_edit.html",
                        "authenticated": False,
                        "content": document,
                    }
                ]
            }
        )
        self.assertTrue(result["found"])
        self.assertEqual(result["transport_mode"], "cmd")
        self.assertEqual(result["local_network"]["protocol"], "TCP")
        self.assertEqual(result["local_network"]["role"], "SERVER")
        self.assertEqual(result["local_network"]["port"], 8899)
        self.assertEqual(result["local_network"]["timeout_seconds"], 300)
        self.assertEqual(result["uart"]["baud"], 115200)
        self.assertEqual(result["inverter_profile"]["id"], "4247")
        self.assertEqual(result["inverter_profile"]["name"], "Tengsheng_G4")
        self.assertEqual(result["cloud_server_a"]["endpoint_kind"], "hostname")
        self.assertEqual(result["cloud_server_a"]["port"], 10443)
        self.assertEqual(result["cloud_server_b"]["endpoint_kind"], "ip")
        self.assertEqual(result["cloud_server_b"]["port"], 9000)
        encoded = json.dumps(result, sort_keys=True)
        self.assertNotIn("iot.example.invalid", encoded)
        self.assertNotIn("192.0.2.77", encoded)
        self.assertNotIn("192.0.2.50", encoded)

    def test_status_snapshot_extracts_apsta_without_storing_ap_address(self) -> None:
        document = """
        <script>
        var webdata_sn = "Y00SECRET";
        var webdata_msvn = "";
        var webdata_ssvn = "";
        var webdata_pv_type = "";
        var webdata_rate_p = "";
        var webdata_now_p = "0";
        var webdata_today_e = "0.0";
        var webdata_total_e = "12.3";
        var webdata_alarm = "";
        var webdata_utime = "1";
        var cover_wmode = "APSTA";
        var cover_ap_ip = "10.10.100.254";
        var status_a = "1";
        var status_b = "0";
        var status_c = "0";
        </script>
        """
        safe, ap_ip = probe._extract_status_runtime_snapshot(document)
        self.assertEqual(ap_ip, "10.10.100.254")
        self.assertEqual(safe["wireless_mode"], "APSTA")
        self.assertTrue(safe["ap_address_present"])
        self.assertTrue(safe["ap_address_private_ipv4"])
        self.assertEqual(safe["remote_status_flags"]["a"], 1)
        self.assertFalse(safe["remote_status_flags"]["semantics_assumed"])
        self.assertTrue(safe["inverter_webdata_presence"]["serial_present"])
        self.assertFalse(safe["inverter_webdata_presence"]["main_software_version_present"])
        self.assertTrue(safe["inverter_webdata_presence"]["total_energy_nonzero"])
        encoded = json.dumps(safe, sort_keys=True)
        self.assertNotIn("10.10.100.254", encoded)
        self.assertNotIn("Y00SECRET", encoded)

    def test_service_watch_is_connection_only_and_bounded(self) -> None:
        with (
            mock.patch.object(
                probe,
                "_one_tcp_open",
                side_effect=[None, 8899, 8899, None, None, None],
            ) as one_tcp_open,
            mock.patch.object(probe.time, "sleep") as sleep,
        ):
            result = probe._watch_tcp_service(
                "192.0.2.50", 8899, full=False, timeout=0.1
            )
        self.assertEqual(result["attempts"], 6)
        self.assertEqual(one_tcp_open.call_count, 6)
        self.assertEqual(sleep.call_count, 5)
        self.assertEqual(result["successful_connections"], 2)
        self.assertTrue(result["observed_open"])
        self.assertEqual(result["first_open_offset_seconds"], 1.0)
        self.assertEqual(result["state_transitions"], 2)
        self.assertTrue(result["connection_only"])
        self.assertFalse(result["application_data_sent"])
        self.assertFalse(result["configuration_write_performed"])

    def test_ap_interface_probe_can_identify_ap_only_service(self) -> None:
        with (
            mock.patch.object(
                probe,
                "_one_tcp_open",
                side_effect=[80, None, 8899, None],
            ) as one_tcp_open,
            mock.patch.object(probe.time, "sleep") as sleep,
        ):
            result = probe._probe_ap_interface(
                "10.10.100.254",
                8899,
                wireless_mode="APSTA",
                timeout=0.1,
            )
        self.assertEqual(one_tcp_open.call_count, 4)
        self.assertEqual(sleep.call_count, 2)
        self.assertTrue(result["reachability_confirmed"])
        self.assertTrue(result["configured_port_open"])
        self.assertEqual(result["configured_port_successes"], 1)
        self.assertEqual(
            result["outcome"], "configured_service_observed_on_ap_interface"
        )
        self.assertNotIn("10.10.100.254", json.dumps(result, sort_keys=True))
        self.assertTrue(result["connection_only"])
        self.assertFalse(result["application_data_sent"])

    def test_ap_probe_unreachable_does_not_claim_port_closed(self) -> None:
        with (
            mock.patch.object(probe, "_one_tcp_open", return_value=None),
            mock.patch.object(probe.time, "sleep"),
        ):
            ap_probe = probe._probe_ap_interface(
                "10.10.100.254",
                8899,
                wireless_mode="APSTA",
                timeout=0.1,
            )
        assessment = probe._classify_local_access(
            {
                "inventory_observed_open": False,
                "watch_observed_open": False,
            },
            ap_probe,
        )
        self.assertFalse(ap_probe["reachability_confirmed"])
        self.assertFalse(ap_probe["configured_port_open"])
        self.assertEqual(
            ap_probe["outcome"],
            "ap_interface_not_reachable_from_current_network_or_services_closed",
        )
        self.assertEqual(
            assessment["status"], "ap_follow_up_requires_direct_ap_connection"
        )

    def test_configured_server_mismatch_is_explicit(self) -> None:
        settings = {
            "local_network": {"protocol": "TCP", "role": "SERVER", "port": 8899}
        }
        result = probe._compare_configured_service(
            settings,
            {"open_ports": [80]},
            {"observed_open": False},
        )
        self.assertTrue(result["configured_as_tcp_server"])
        self.assertTrue(result["configuration_runtime_mismatch"])
        self.assertEqual(result["status"], "configured_but_not_observed")

    def test_research_report_keeps_network_evidence_anonymous_and_read_only(self) -> None:
        fake_web_document = """
        <script>
        var yz_tmode = "cmd";
        var server_a = ",iot.example.invalid,10443,TCP";
        var server_b = ",iot.example.invalid,10443,TCP";
        var uart_setting_baud = "115200";
        var uart_setting_data = "databit_8";
        var uart_setting_parity = "none";
        var uart_setting_stop = "stopbit_1";
        var uart_setting_fc = "NFC";
        var net_setting_pro = "TCP";
        var net_setting_cs = "SERVER";
        var net_setting_port = "8899";
        var net_setting_ip = "<IP>";
        var net_setting_to = "300";
        var inv_set = "4247,1,1";
        var apsta_mode = "0";
        var inv_tp = "4247:Tengsheng_G4";
        var inv_tp_seld = "";
        </script>
        """
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
                "pages": [
                    {
                        "path": "/hide_set_edit.html",
                        "authenticated": False,
                        "content": fake_web_document,
                    }
                ],
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
            mock.patch.object(
                probe,
                "_watch_tcp_service",
                return_value={
                    "attempted": True,
                    "port": 8899,
                    "duration_seconds": 20.0,
                    "interval_seconds": 1.0,
                    "attempts": 21,
                    "successful_connections": 0,
                    "observed_open": False,
                    "first_open_offset_seconds": None,
                    "state_transitions": 0,
                    "observations": [],
                    "connection_only": True,
                    "application_data_sent": False,
                    "configuration_write_performed": False,
                },
            ),
            mock.patch.object(
                probe,
                "_capture_logger_status_runtime",
                return_value=(
                    {
                        "attempted": True,
                        "found": True,
                        "wireless_mode": "APSTA",
                        "ap_address_present": True,
                        "ap_address_private_ipv4": True,
                        "ap_address_value_stored": False,
                        "remote_status_flags": {
                            "a": 1,
                            "b": 0,
                            "c": 0,
                            "semantics_assumed": False,
                        },
                        "inverter_webdata_presence": {
                            "serial_present": True,
                            "main_software_version_present": False,
                            "slave_software_version_present": False,
                            "pv_type_present": False,
                            "rated_power_present": False,
                            "alarm_present": False,
                            "uptime_present": True,
                            "power_nonzero": False,
                            "today_energy_nonzero": False,
                            "total_energy_nonzero": False,
                        },
                        "raw_status_html_stored": False,
                    },
                    "10.10.100.254",
                ),
            ),
            mock.patch.object(
                probe,
                "_probe_ap_interface",
                return_value={
                    "attempted": True,
                    "wireless_mode": "APSTA",
                    "ap_address_private_ipv4": True,
                    "ap_address_value_stored": False,
                    "http_port_80_open": False,
                    "reachability_confirmed": False,
                    "configured_port": 8899,
                    "configured_port_attempts": 3,
                    "configured_port_successes": 0,
                    "configured_port_open": False,
                    "outcome": "ap_interface_not_reachable_from_current_network_or_services_closed",
                    "connection_only": True,
                    "application_data_sent": False,
                    "configuration_write_performed": False,
                },
            ),
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
        self.assertNotIn("10.10.100.254", encoded)
        structured = json.dumps(
            document["transport_research"]["logger_transport_settings"],
            sort_keys=True,
        )
        self.assertNotIn("iot.example.invalid", structured)
        self.assertEqual(document["metadata"]["detected_protocol"], "1097-research")
        self.assertEqual(document["metadata"]["capture_status"], "partial_success")
        self.assertFalse(document["metadata"]["measurements_available"])
        research = document["transport_research"]
        self.assertEqual(research["probe_revision"], probe.PROBE_REVISION)
        self.assertEqual(research["logger_transport_settings"]["transport_mode"], "cmd")
        self.assertEqual(research["logger_transport_settings"]["local_network"]["port"], 8899)
        self.assertTrue(
            research["configuration_vs_runtime"]["configuration_runtime_mismatch"]
        )
        self.assertEqual(research["logger_status_runtime"]["wireless_mode"], "APSTA")
        self.assertEqual(
            research["local_access_assessment"]["status"],
            "ap_follow_up_requires_direct_ap_connection",
        )
        ota = research["firmware_update_url_query"]
        self.assertEqual(ota["command"], "AT+UPURL")
        self.assertTrue(ota["getter_form_only"])
        self.assertFalse(ota["assignment_sent"])
        self.assertFalse(ota["external_url_contacted"])
        safety = research["safety"]
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
        self.assertTrue(safety["service_watch_connection_only"])
        self.assertFalse(safety["service_watch_application_data_sent"])
        self.assertTrue(safety["status_snapshot_get_only"])
        self.assertTrue(safety["ap_interface_probe_connection_only"])
        self.assertFalse(safety["ap_interface_probe_application_data_sent"])


if __name__ == "__main__":
    unittest.main()
