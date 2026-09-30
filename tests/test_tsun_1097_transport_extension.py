from __future__ import annotations

import json
from pathlib import Path
import sys
import types
import unittest
from unittest import mock

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import tsun_1097_transport_extension as ext  # noqa: E402


class Transport1097ExtensionTests(unittest.TestCase):
    def _args(self, *, full: bool = True):
        return types.SimpleNamespace(
            full=full,
            timeout=0.2,
            tcp_scan_timeout=0.05,
        )

    def _research_document(self):
        return {
            "metadata": {
                "detected_protocol": "1097-research",
                "capture_limitation": "legacy_tcp_8899_unavailable",
            },
            "logger_web": {
                "pages": [
                    {
                        "content": (
                            'var yz_tmode = "cmd";\n'
                            'var server_a = ",iot.example.invalid,10443,TCP";\n'
                            'var uart_setting_baud = "115200";\n'
                            'var uart_setting_data = "databit_8";\n'
                            'var uart_setting_parity = "none";\n'
                            'var uart_setting_stop = "stopbit_1";\n'
                            'var uart_setting_fc = "NFC";\n'
                            'var net_setting_pro = "TCP";\n'
                            'var net_setting_cs = "SERVER";\n'
                            'var net_setting_port = "8899";\n'
                            'var net_setting_ip = "192.168.1.176";\n'
                            'var net_setting_to = "300";\n'
                            'var inv_set = "4247,1,1";\n'
                            'var inv_tp = "4247:Tengsheng_G4";\n'
                        )
                    }
                ]
            },
            "transport_research": {"tcp_inventory": {"open_ports": [80]}},
        }

    def test_static_config_extracts_transport_without_private_values(self) -> None:
        config = ext.extract_static_logger_config(self._research_document()["logger_web"])
        self.assertEqual(config["network"]["protocol"], "TCP")
        self.assertEqual(config["network"]["role"], "SERVER")
        self.assertEqual(config["network"]["port"], 8899)
        self.assertEqual(config["uart"]["baud"], 115200)
        self.assertEqual(config["inverter_profile"]["profile"], "4247:Tengsheng_G4")
        encoded = json.dumps(config)
        self.assertNotIn("192.168.1.176", encoded)
        self.assertNotIn("iot.example.invalid", encoded)
        self.assertFalse(config["raw_ip_stored"])
        self.assertFalse(config["raw_remote_hostname_stored"])

    def test_at_catalog_contains_getters_only(self) -> None:
        self.assertGreaterEqual(len(ext.AT_QUERY_CATALOG), 8)
        commands = [command for _name, command in ext.AT_QUERY_CATALOG]
        self.assertTrue(all(b"=" not in command for command in commands))
        rendered = b" ".join(commands).upper()
        for forbidden in (b"ENTM", b"TCPDIS", b"RELD", b"AT+Z"):
            self.assertNotIn(forbidden, rendered)

    def test_full_extra_scan_is_bounded(self) -> None:
        standard = ext._ports(False, 8899)
        full = ext._ports(True, 8899)
        self.assertLess(len(standard), 40)
        self.assertGreater(len(full), len(standard))
        self.assertLess(len(full), 10000)
        self.assertIn(8899, full)
        self.assertIn(10443, full)
        self.assertNotEqual(len(full), 65535)

    def test_active_1097_probes_skip_unrelated_service_ports(self) -> None:
        fake_dump = types.SimpleNamespace(
            detect_protocol=mock.Mock(side_effect=RuntimeError("no")),
        )
        ext.alternate_1097(
            fake_dump,
            "192.0.2.10",
            1234,
            [22, 80, 443, 1883, 502, 5000, 8883, 9000, 10443, 48899],
            0.2,
        )
        called_ports = [call.args[2] for call in fake_dump.detect_protocol.call_args_list]
        self.assertEqual(called_ports, [502, 5000, 9000])

    def test_status_parser_extracts_measurements_without_serial_number(self) -> None:
        parsed = ext.parse_status_measurements(
            b'''<script>
var webdata_sn = "Y001234567";
var webdata_msvn = "MAIN_1";
var webdata_ssvn = "SLAVE_1";
var webdata_pv_type = "MX500";
var webdata_rate_p = "500";
var webdata_now_p = "123";
var webdata_today_e = "2.4";
var webdata_total_e = "321.6";
var webdata_alarm = "";
var webdata_utime = "4";
var status_a = "1";
</script>'''
        )
        self.assertEqual(parsed["values"]["current_power_w"], 123)
        self.assertEqual(parsed["values"]["yield_today_kwh"], 2.4)
        self.assertEqual(parsed["values"]["inverter_model"], "MX500")
        self.assertNotIn("webdata_sn", parsed["variables_found"])
        self.assertNotIn("Y001234567", json.dumps(parsed))
        self.assertFalse(parsed["serial_number_stored"])
        self.assertFalse(parsed["raw_html_stored"])

    def test_http_sampling_validates_changing_live_measurements(self) -> None:
        bodies = []
        for power in (100, 120, 130):
            bodies.append(
                (
                    'var webdata_rate_p="500"; '
                    f'var webdata_now_p="{power}"; '
                    'var webdata_today_e="1.2"; '
                    'var webdata_total_e="42.0"; '
                    'var webdata_utime="1";'
                ).encode()
            )
        rows = [
            {
                "status": 200,
                "content_type": "text/html",
                "body_length": len(body),
                "body_sha256_12": "abc",
                "body": body,
            }
            for body in bodies
        ]
        with (
            mock.patch.object(ext, "_http_fetch", side_effect=rows),
            mock.patch.object(ext, "HTTP_SAMPLE_STANDARD_COUNT", 3),
        ):
            result = ext.sample_http_measurements(
                "192.0.2.10",
                0.2,
                full=False,
                sleep_fn=lambda _seconds: None,
            )
        self.assertEqual(result["conclusion"], "live_http_measurements_validated")
        self.assertTrue(result["http_live_measurements_validated"])
        self.assertIn("current_power_w", result["changing_fields"])
        self.assertFalse(result["privacy"]["raw_html_stored"])
        self.assertFalse(result["safety"]["http_post_performed"])

    def test_http_sampling_zero_values_remain_a_candidate(self) -> None:
        body = (
            b'var webdata_rate_p=""; var webdata_now_p="0"; '
            b'var webdata_today_e="0.0"; var webdata_total_e="0.0"; '
            b'var webdata_utime="0";'
        )
        row = {
            "status": 200,
            "content_type": "text/html",
            "body_length": len(body),
            "body_sha256_12": "abc",
            "body": body,
        }
        with (
            mock.patch.object(ext, "_http_fetch", return_value=row),
            mock.patch.object(ext, "HTTP_SAMPLE_STANDARD_COUNT", 2),
        ):
            result = ext.sample_http_measurements(
                "192.0.2.10",
                0.2,
                full=False,
                sleep_fn=lambda _seconds: None,
            )
        self.assertEqual(result["conclusion"], "http_measurements_zero_during_sampling")
        self.assertTrue(result["http_measurements_candidate"])
        self.assertFalse(result["http_live_measurements_validated"])

    def test_normal_capture_is_not_extended(self) -> None:
        expected = {"metadata": {"detected_protocol": "1097"}}
        fake = types.SimpleNamespace(capture=mock.Mock(return_value=expected))
        ext.install(fake)
        with mock.patch.object(ext, "extend_document") as extended:
            result = fake.capture(self._args(), "192.0.2.10", 1234, {})
        self.assertIs(result, expected)
        extended.assert_not_called()

    def test_research_extension_failure_never_breaks_partial_report(self) -> None:
        document = self._research_document()
        fake = types.SimpleNamespace(capture=mock.Mock(return_value=document))
        ext.install(fake)
        with mock.patch.object(ext, "extend_document", side_effect=RuntimeError("boom")):
            result = fake.capture(self._args(), "192.0.2.10", 1234, {})
        self.assertIs(result, document)
        evidence = result["transport_research"]["extended_1097"]
        self.assertEqual(evidence["error"], "RuntimeError")
        self.assertTrue(evidence["safety"]["read_only"])
        self.assertFalse(evidence["safety"]["configuration_write_performed"])

    def test_extended_document_records_fc03_only_and_safety(self) -> None:
        document = self._research_document()
        fake_dump = types.SimpleNamespace(
            build_modbus_read_request=mock.Mock(return_value=b"read"),
            build_ap_frame=mock.Mock(return_value=b"frame"),
            _summarize_v5_frame=mock.Mock(
                return_value={
                    "valid": True,
                    "control": "0x1510",
                    "control_name": "RESPONSE",
                }
            ),
            detect_protocol=mock.Mock(side_effect=RuntimeError("no")),
        )
        lifecycle = {
            "attempted": True,
            "port": 8899,
            "attempt_count": 1,
            "open_count": 0,
            "results": [],
        }
        sampling = {
            "http_measurements_candidate": True,
            "http_live_measurements_validated": True,
            "measurement_fields_seen": ["current_power_w"],
            "conclusion": "live_http_measurements_validated",
        }
        with (
            mock.patch.object(ext, "tcp_lifecycle", return_value=lifecycle),
            mock.patch.object(ext, "sample_http_measurements", return_value=sampling),
            mock.patch.object(ext, "_http_get", return_value={"status": 200, "method": "GET"}),
            mock.patch.object(
                ext,
                "query_at_getters",
                return_value={"attempted": True, "queries": [], "assignment_sent": False},
            ),
            mock.patch.object(
                ext,
                "udp_1097_read",
                return_value={
                    "attempted": True,
                    "function": "0x03",
                    "attempts": [],
                    "write_function_sent": False,
                },
            ),
            mock.patch.object(
                ext,
                "extra_tcp_inventory",
                return_value={
                    "attempted": True,
                    "open_ports": [80],
                    "ports_tested": 10,
                    "full_65535_scan_performed": False,
                },
            ),
            mock.patch.object(ext, "alternate_1097", return_value=[]),
        ):
            result = ext.extend_document(
                fake_dump,
                self._args(),
                "192.0.2.10",
                1234,
                document,
            )
        evidence = result["transport_research"]["extended_1097"]
        self.assertEqual(evidence["version"], 2)
        self.assertEqual(evidence["phase_order"][2], "http_measurement_sampling")
        self.assertTrue(evidence["summary"]["logger_reports_tcp_server_8899"])
        self.assertTrue(evidence["summary"]["http_live_measurements_validated"])
        self.assertEqual(evidence["summary"]["recommended_transport"], "http_status_page")
        self.assertEqual(
            evidence["summary"]["next_step"],
            "implement_and_validate_1097_http_transport",
        )
        self.assertEqual(evidence["udp_1097_fc03_probe"]["function"], "0x03")
        self.assertEqual(evidence["safety"]["modbus_functions_sent"], ["0x03"])
        self.assertFalse(evidence["safety"]["modbus_write_sent"])
        self.assertFalse(evidence["safety"]["http_post_performed"])
        self.assertFalse(evidence["safety"]["full_65535_tcp_scan_performed"])
        self.assertFalse(evidence["safety"]["raw_http_body_stored"])


if __name__ == "__main__":
    unittest.main()
