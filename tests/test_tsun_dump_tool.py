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
        self.assertEqual(TOOL.TOOL_VERSION, "2.5.0")
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
        self.assertEqual(TOOL.MAX_LOGGER_WEB_PATHS, 10)

    def test_capture_plans_stay_read_only(self) -> None:
        for protocol in ("02b0", "1097", "1511"):
            dynamic, supplemental = TOOL.capture_plans(protocol, full=True)
            self.assertTrue(dynamic)
            self.assertTrue(supplemental)
            if protocol != "1511":
                for start, end in [*dynamic, *supplemental]:
                    self.assertLessEqual(end - start + 1, 16)

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
