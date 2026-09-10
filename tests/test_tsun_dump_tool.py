# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for the standalone TSUN hardware validation dump tool."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


TOOL_PATH = Path(__file__).parents[1] / "tools" / "tsun_dump.py"
SPEC = importlib.util.spec_from_file_location("tsun_dump_tool_test", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
TOOL = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = TOOL
SPEC.loader.exec_module(TOOL)


class TsunDumpToolTests(unittest.TestCase):
    """Verify standalone packaging, privacy, plans and comparison behavior."""

    def test_tool_is_really_standalone(self) -> None:
        source = TOOL_PATH.read_text(encoding="utf-8")
        self.assertNotIn("custom_components", source)
        self.assertNotIn("importlib.util", source)
        self.assertNotIn("from tsun_local", source)
        self.assertTrue(TOOL.SOURCE_URL.endswith("/tools/tsun_dump.py"))
        self.assertEqual(TOOL.SCHEMA_VERSION, 3)
        self.assertEqual(TOOL.TOOL_VERSION, "2.7.5")
        self.assertEqual(TOOL.REPORT_EMAIL, "dev@jptstar.com")

    def test_bounded_network_parser_accepts_24(self) -> None:
        network = TOOL._parse_scan_network("10.89.10.0/24")
        self.assertEqual(str(network), "10.89.10.0/24")

    def test_bounded_network_parser_rejects_wide_network(self) -> None:
        with self.assertRaises(ValueError):
            TOOL._parse_scan_network("10.89.0.0/16")

    def test_network_around_discovered_host_is_24(self) -> None:
        self.assertEqual(
            str(TOOL._network_around_host("10.89.10.14")),
            "10.89.10.0/24",
        )

    def test_extracts_single_monitor_sn_from_json_discovery(self) -> None:
        payload = b'{"ip":"192.168.1.25","logger_sn":"1234567890"}'
        self.assertEqual(TOOL.serial_candidates_from_payload(payload), {1234567890})

    def test_ambiguous_text_discovery_keeps_all_candidates(self) -> None:
        payload = b"192.168.1.25,AA:BB:CC:DD:EE:FF,123456789,987654321"
        self.assertEqual(
            TOOL.serial_candidates_from_payload(payload),
            {123456789, 987654321},
        )

    def test_protocol_hint_from_logger_firmware(self) -> None:
        self.assertEqual(TOOL.protocol_from_firmware("LSW5_SSL_1511_1.03"), "1511")
        self.assertEqual(TOOL.protocol_from_firmware("LSW5_SSL_02B0_1.00"), "02b0")
        self.assertEqual(TOOL.protocol_from_firmware("LSW5_SSL_1097_1.00"), "1097")
        self.assertIsNone(TOOL.protocol_from_firmware("unknown"))

    def test_logger_web_identity_extracts_monitor_sn_and_protocol(self) -> None:
        document = (
            'var cover_mid="1234567890"; '
            'var cover_ver="LSW5_SSL_1511_1.03"; '
            'var webdata_sn="Y000000000000000";'
        )
        serials, firmware, hint, recognized = TOOL._web_identity_from_document(document)
        self.assertEqual(serials, {1234567890})
        self.assertEqual(firmware, "LSW5_SSL_1511_1.03")
        self.assertEqual(hint, "1511")
        self.assertTrue(recognized)

    def test_logger_web_capture_paths_include_profile_page(self) -> None:
        self.assertIn("/hide_set_edit.html", TOOL.LOGGER_WEB_CAPTURE_PATHS)

    def test_logger_web_anonymization_keeps_only_safe_identity_fragments(self) -> None:
        document = (
            'var webdata_sn="Y471234567890"; '
            'var cover_mid="1234567890"; '
            'var cover_ver="LSW5_SSL_02B0_1.00"; '
            'var inv_tp="TSOL-MX500"; '
            'var cover_sta_rssi="-70"; '
            'var mac="AA:BB:CC:DD:EE:FF"; '
            'var ip="192.168.1.25"; '
            'var ssid="MyWifi"; '
            'var password="TopSecret"; '
            'var email="owner@example.com";'
        )
        sanitized = TOOL.anonymize_web_document(document)
        metadata = TOOL._logger_web_metadata(document)
        self.assertIn('webdata_sn="Y47<REDACTED>"', sanitized)
        self.assertNotIn("Y471234567890", sanitized)
        self.assertNotIn("1234567890", sanitized)
        self.assertNotIn("192.168.1.25", sanitized)
        self.assertNotIn("AA:BB:CC:DD:EE:FF", sanitized)
        self.assertIn("AA:BB:CC:XX:XX:XX", sanitized)
        self.assertNotIn("MyWifi", sanitized)
        self.assertNotIn("TopSecret", sanitized)
        self.assertNotIn("owner@example.com", sanitized)
        self.assertEqual(metadata["inverter_serial_prefix"], "Y47")
        self.assertEqual(metadata["logger_mac_oui"], "AA:BB:CC")
        self.assertEqual(metadata["logger_raw_profile"], "TSOL-MX500")
        self.assertEqual(metadata["logger_wifi_signal"], -70)
        self.assertEqual(metadata["logger_wifi_signal_unit"], "dBm")
        self.assertEqual(metadata["logger_wifi_signal_source"], "cover_sta_rssi")

    def test_wifi_signal_variants_keep_unit_and_source(self) -> None:
        percent = TOOL._logger_web_metadata('var wifi_signal="72%";')
        self.assertEqual(percent["logger_wifi_signal"], 72)
        self.assertEqual(percent["logger_wifi_signal_unit"], "%")
        self.assertEqual(percent["logger_wifi_signal_source"], "wifi_signal")

        dbm = TOOL._logger_web_metadata('<div>WiFi Signal: -67 dBm</div>')
        self.assertEqual(dbm["logger_wifi_signal"], -67)
        self.assertEqual(dbm["logger_wifi_signal_unit"], "dBm")
        self.assertEqual(dbm["logger_wifi_signal_source"], "visible_wifi_label")

    def test_ms2000_web_metadata_ignores_help_placeholders_and_example_mac(self) -> None:
        help_document = (
            'Firmware version (main) '
            'Firmware version (slave) '
            'E.g. 00:01:02:AA:BB:CC'
        )
        help_metadata = TOOL._logger_web_metadata(help_document)
        self.assertIsNone(help_metadata["logger_firmware_version"])
        self.assertIsNone(help_metadata["logger_mac_oui"])

        status_document = (
            'var cover_ver="LSW5_SSL_02B0_1.05"; '
            'var cover_ap_mac="AA:BB:CC:11:22:33"; '
            'var cover_sta_mac="74:E9:D8:44:55:66"; '
            'var cover_sta_rssi="76%"; '
            'var webdata_sn="Y001234567890";'
        )
        status_metadata = TOOL._logger_web_metadata(status_document)
        self.assertEqual(status_metadata["logger_firmware_version"], "LSW5_SSL_02B0_1.05")
        self.assertEqual(status_metadata["logger_mac_oui"], "74:E9:D8")
        self.assertEqual(status_metadata["logger_wifi_signal"], 76)
        self.assertEqual(status_metadata["logger_wifi_signal_unit"], "%")
        self.assertEqual(status_metadata["inverter_serial_prefix"], "Y00")

        visible_firmware = TOOL._logger_web_metadata("Firmware version: V4.0.39")
        self.assertEqual(visible_firmware["logger_firmware_version"], "V4.0.39")

    def test_logger_web_link_discovery_is_local_bounded_and_passive(self) -> None:
        document = (
            '<a href="/wifi_status.html">WiFi</a>'
            '<a href="device.html">Device</a>'
            '<iframe src="/info.cgi"></iframe>'
            '<a href="/reboot.cgi">Reboot</a>'
            '<a href="https://example.com/status.html">External</a>'
            '<a href="javascript:reset()">JS</a>'
            '<a href="/image.png">Image</a>'
        )
        paths = TOOL._discover_local_web_paths(
            document, "/index.html", "192.168.1.25"
        )
        self.assertEqual(paths, ["/wifi_status.html", "/device.html", "/info.cgi"])
        self.assertEqual(TOOL.MAX_LOGGER_WEB_PATHS, 24)

    def test_research_capture_paths_include_network_and_upgrade_pages(self) -> None:
        self.assertEqual(len(TOOL.LOGGER_WEB_CAPTURE_PATHS), 10)
        for path in (
            "/wireless.html",
            "/wizard.html",
            "/remote.html",
            "/update.html",
            "/invupdate.html",
        ):
            self.assertIn(path, TOOL.LOGGER_WEB_CAPTURE_PATHS)

    def test_web_interface_summary_is_passive_and_privacy_safe(self) -> None:
        document = (
            '<form method="post" enctype="multipart/form-data" action="upgrade.cgi" '
            'onsubmit="return checkUpgrade()">'
            '<input type="file" name="firmware_file">'
            '<input type="hidden" name="ssid" value="SecretWifi">'
            '<button type="submit" onclick="startUpgrade()">Upload</button>'
            '</form>'
            '<script src="helper.js"></script>'
        )
        summary = TOOL.summarize_web_interface_read_only(
            document, "/update.html", "192.168.1.25"
        )
        self.assertTrue(summary["read_only"])
        self.assertFalse(summary["form_submission_performed"])
        self.assertFalse(summary["javascript_executed"])
        self.assertFalse(summary["upload_performed"])
        self.assertEqual(summary["forms"][0]["method"], "post")
        self.assertEqual(summary["forms"][0]["action"], "/upgrade.cgi")
        self.assertIn(
            {"name": "firmware_file", "type": "file"},
            summary["forms"][0]["fields"],
        )
        self.assertIn("checkUpgrade", summary["javascript_handlers"])
        self.assertIn("startUpgrade", summary["javascript_handlers"])
        self.assertNotIn("SecretWifi", repr(summary))

    def test_logger_firmware_fallback_rejects_plain_numeric_ui_value(self) -> None:
        self.assertIsNone(TOOL._extract_logger_firmware("Firmware version: 13"))
        self.assertEqual(
            TOOL._extract_logger_firmware('var cover_ver="LSW5_SSL_02B0_1.05"; Firmware version: 13'),
            "LSW5_SSL_02B0_1.05",
        )

    def test_js_research_extracts_target_body_without_execution_or_secrets(self) -> None:
        document = (
            'function sta_form_apply(){'
            'var dns=document.forms[0].wan_setting_dns.value;'
            'var password="TopSecret";'
            'document.forms[0].action="do_step_neth.html";'
            'document.forms[0].submit();'
            '}'
            'function unrelated(){return 1;}'
        )
        summaries = TOOL.summarize_js_research_functions(document)
        self.assertEqual(len(summaries), 1)
        summary = summaries[0]
        self.assertEqual(summary["name"], "sta_form_apply")
        self.assertTrue(summary["static_source_only"])
        self.assertFalse(summary["javascript_executed"])
        self.assertIn("wan_setting_dns", summary["body"])
        self.assertIn("do_step_neth.html", summary["body"])
        self.assertNotIn("TopSecret", summary["body"])
        self.assertNotIn("unrelated", repr(summaries))

    def test_js_function_parser_handles_nested_blocks(self) -> None:
        document = 'function sw_upload_apply(){if(true){while(false){x();}}return 1;}'
        body = TOOL._extract_js_function_body(document, "sw_upload_apply")
        self.assertIsNotNone(body)
        self.assertIn("while(false){x();}", body)
        self.assertIn("return 1", body)

    def test_dns_probe_command_is_get_only(self) -> None:
        self.assertEqual(TOOL.LOGGER_DNS_QUERY, b"AT+WSDNS\n")
        self.assertNotIn(b"=", TOOL.LOGGER_DNS_QUERY)

    def test_dns_probe_response_is_privacy_safe(self) -> None:
        summary = TOOL.summarize_logger_dns_response(
            b"+ok=192.168.1.1,8.8.8.8\r\n"
        )
        self.assertTrue(summary["supported"])
        self.assertTrue(summary["dns_server_present"])
        self.assertEqual(summary["address_count"], 2)
        self.assertEqual(summary["address_scopes"], ["private", "public"])
        rendered = repr(summary)
        self.assertNotIn("192.168.1.1", rendered)
        self.assertNotIn("8.8.8.8", rendered)

    def test_dns_probe_rejects_non_ok_response(self) -> None:
        summary = TOOL.summarize_logger_dns_response(b"+ERR=-1\r\n")
        self.assertFalse(summary["supported"])
        self.assertFalse(summary["dns_server_present"])

    def test_capture_plans_stay_read_only(self) -> None:
        for protocol in ("02b0", "1097", "1511"):
            dynamic, supplemental = TOOL.capture_plans(protocol, full=True)
            self.assertTrue(dynamic)
            self.assertTrue(supplemental)
            if protocol != "1511":
                for start, end in [*dynamic, *supplemental]:
                    self.assertLessEqual(end - start + 1, 16)

    def test_02b0_characterization_classifies_strict_16_limit(self) -> None:
        def record(test_id: str, successes: int) -> dict[str, object]:
            return {
                "id": test_id,
                "successes": successes,
                "attempts": [{"result": "success"}] if successes else [{"result": "failure"}],
            }

        tests = [
            record("start_3008_8", 1),
            record("cross_boundary_16", 1),
            record("cross_boundary_17", 0),
            record("legacy_v153_22", 0),
            record("current_v154_v160_23", 0),
            record("dynamic_3000_16", 1),
            record("dynamic_3010_16", 1),
            record("dynamic_3020_16", 1),
        ]
        analysis = TOOL.analyze_02b0_characterization(tests, [])
        self.assertEqual(
            analysis["size_limit_16"], "evidence_supports_max_16_registers"
        )
        self.assertTrue(analysis["register_0x3008_readable"])
        self.assertTrue(analysis["crosses_0x300F_boundary"])

    def test_02b0_characterization_rejects_strict_limit_if_17_succeeds(self) -> None:
        tests = [
            {"id": "cross_boundary_17", "successes": 1, "attempts": [{"result": "success"}]},
            {"id": "cross_boundary_16", "successes": 1, "attempts": [{"result": "success"}]},
            {"id": "dynamic_3010_16", "successes": 1, "attempts": [{"result": "success"}]},
        ]
        analysis = TOOL.analyze_02b0_characterization(tests, [])
        self.assertEqual(
            analysis["size_limit_16"], "not_a_strict_16_register_limit"
        )

    def test_02b0_characterization_preserves_short_marker_without_meaning(self) -> None:
        tests = [
            {
                "id": "current_v154_v160_23",
                "successes": 0,
                "attempts": [
                    {"result": "short_marker_only", "short_marker": "05 00"}
                ],
            }
        ]
        analysis = TOOL.analyze_02b0_characterization(tests, [])
        self.assertEqual(analysis["short_markers_seen"], ["05 00"])
        self.assertFalse(analysis["modbus_followup_after_short_marker_seen"])

    def test_1511_plan_uses_only_known_native_read_functions(self) -> None:
        dynamic, supplemental = TOOL.capture_plans("1511", full=True)
        functions = {block[1] for block in [*dynamic, *supplemental]}
        self.assertEqual(functions, {0x01, 0x02, 0x03, 0x04, 0x21})

    def test_compare_documents_reports_raw_changes(self) -> None:
        before = {
            "raw_registers": [
                {"key": "0x2048", "raw_decimal": 0},
                {"key": "0x2049", "raw_decimal": 1},
            ]
        }
        after = {
            "raw_registers": [
                {"key": "0x2048", "raw_decimal": 1},
                {"key": "0x2049", "raw_decimal": 1},
            ]
        }
        comparison = TOOL.compare_documents(before, after)
        self.assertEqual(len(comparison["changed_registers"]), 1)
        self.assertEqual(comparison["changed_registers"][0]["key"], "0x2048")


if __name__ == "__main__":
    unittest.main()
