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
        self.assertEqual(TOOL.TOOL_VERSION, "2.4.0")

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
            'var cover_mid="3890384117"; '
            'var cover_ver="LSW5BLE_17_02B0_1.08-D1"; '
            'var webdata_sn="Y47ABCDEF1234567"; '
            'var cover_sta_rssi="42"; '
            'var inv_tp="MX450"; '
            'var cover_sta_mac="AA:BB:CC:DD:EE:FF"; '
            'var cover_sta_ssid="PrivateWifi"; '
            'var cover_sta_psk="VerySecretPassword"; '
            'var local_ip="192.168.1.50"; '
            'var contact="owner@example.com";'
        )
        metadata = TOOL._logger_web_metadata(document)
        self.assertEqual(metadata["logger_firmware_version"], "LSW5BLE_17_02B0_1.08-D1")
        self.assertEqual(metadata["logger_wifi_signal"], 42)
        self.assertEqual(metadata["logger_raw_profile"], "MX450")
        self.assertEqual(metadata["logger_mac_oui"], "AA:BB:CC")
        self.assertEqual(metadata["inverter_serial_prefix"], "Y47")

        sanitized = TOOL.anonymize_web_document(document)
        self.assertIn("Y47<REDACTED>", sanitized)
        self.assertIn("AA:BB:CC:XX:XX:XX", sanitized)
        self.assertNotIn("Y47ABCDEF1234567", sanitized)
        self.assertNotIn("3890384117", sanitized)
        self.assertNotIn("AA:BB:CC:DD:EE:FF", sanitized)
        self.assertNotIn("192.168.1.50", sanitized)
        self.assertNotIn("PrivateWifi", sanitized)
        self.assertNotIn("VerySecretPassword", sanitized)
        self.assertNotIn("owner@example.com", sanitized)

    def test_logger_web_capture_deduplicates_same_authenticated_page(self) -> None:
        document = (
            'var cover_mid="1234567890"; '
            'var cover_ver="LSW5_SSL_02B0_1.00"; '
            'var webdata_sn="Y471234567890123";'
        )
        original = TOOL._http_document
        try:
            TOOL._http_document = lambda host, path, timeout, authenticated: (
                document if path == "/status.html" else None
            )
            result = TOOL.capture_logger_web_pages("192.0.2.10", 1.0)
        finally:
            TOOL._http_document = original

        self.assertEqual(result["pages_found"], 1)
        self.assertEqual(result["summary"]["inverter_serial_prefix"], "Y47")
        self.assertNotIn("1234567890", result["pages"][0]["content"])
        self.assertNotIn("Y471234567890123", result["pages"][0]["content"])

    def test_ap_identity_extraction_uses_envelope_sn(self) -> None:
        payload = TOOL.build_modbus_request(0x3000, 0x3000)
        frame = TOOL.build_ap_frame(1234567890, payload)
        self.assertEqual(TOOL.extract_ap_logger_sn(frame), 1234567890)

    def test_modbus_capture_plans_are_bounded_fc03_ranges(self) -> None:
        for protocol in ("02b0", "1097"):
            for full in (False, True):
                dynamic, supplemental = TOOL.capture_plans(protocol, full)
                for start, end in (*dynamic, *supplemental):
                    self.assertLessEqual(start, end)
                    self.assertLessEqual(
                        end - start + 1,
                        TOOL.MAX_MODBUS_REGISTERS_PER_READ,
                    )

    def test_1097_plan_excludes_serial_number_words(self) -> None:
        _dynamic, supplemental = TOOL.capture_plans("1097", True)
        addresses = {
            address
            for start, end in supplemental
            for address in range(start, end + 1)
        }
        self.assertFalse(any(address in addresses for address in range(0x1000, 0x1008)))
        self.assertIn(0x1008, addresses)

    def test_1511_plan_uses_only_known_native_read_blocks(self) -> None:
        dynamic, supplemental = TOOL.capture_plans("1511", True)
        self.assertEqual(
            dynamic,
            [
                (0xA1, 0x01, 0x0BB8, 0x0BD7),
                (0xA2, 0x02, 0x0CE4, 0x0CE7),
                (0xA3, 0x03, 0x0E10, 0x0E2D),
                (0xA4, 0x04, 0x0ED8, 0x0EF5),
            ],
        )
        self.assertEqual(supplemental, [(0xA1, 0x21, 0x07D0, 0x082F)])

    def test_full_02b0_plan_covers_zero_export_research_area(self) -> None:
        _dynamic, supplemental = TOOL.capture_plans("02b0", True)
        addresses = {
            address
            for start, end in supplemental
            for address in range(start, end + 1)
        }
        self.assertIn(0x2047, addresses)
        self.assertIn(0x2048, addresses)
        self.assertIn(0x204A, addresses)

    def test_snapshot_analysis_separates_dynamic_and_stable_values(self) -> None:
        snapshots = [
            {"registers": {"0x3009": 2300, "0x300F": 5000, "0x2007": 800, "0x2048": 0}},
            {"registers": {"0x3009": 2301, "0x300F": 5100, "0x2007": 800, "0x2048": 0}},
            {"registers": {"0x3009": 2299, "0x300F": 5050, "0x2007": 800, "0x2048": 0}},
        ]
        result = TOOL.analyze_snapshots(snapshots)
        self.assertEqual(result["changing_registers"], ["0x3009", "0x300F"])
        self.assertEqual(result["stable_registers"], ["0x2007"])
        self.assertEqual(result["zero_registers"], ["0x2048"])

    def test_compare_reports_raw_changes_without_semantic_guess(self) -> None:
        before = {
            "metadata": {"detected_protocol": "02b0"},
            "raw_registers": [
                {"key": "0x2007", "raw_decimal": 800},
                {"key": "0x2048", "raw_decimal": 0},
            ],
        }
        after = {
            "metadata": {"detected_protocol": "02b0"},
            "raw_registers": [
                {"key": "0x2007", "raw_decimal": 800},
                {"key": "0x2048", "raw_decimal": 1},
            ],
        }
        result = TOOL.compare_documents(before, after)
        self.assertEqual(
            result["changed_registers"],
            [
                {
                    "key": "0x2048",
                    "before": 0,
                    "before_hex": "0x0000",
                    "after": 1,
                    "after_hex": "0x0001",
                }
            ],
        )
        self.assertNotIn("name", result["changed_registers"][0])

    def test_output_filename_is_sanitized(self) -> None:
        from datetime import UTC, datetime

        path = TOOL.default_output_path(
            "TSOL-MS800 / test",
            "02b0",
            datetime(2026, 8, 20, 8, 0, tzinfo=UTC),
        )
        self.assertEqual(path.name, "tsun_tsol-ms800-test_02b0_20260820T080000Z.json")

    def test_multi_device_output_names_are_unique(self) -> None:
        from datetime import UTC, datetime

        stamp = datetime(2026, 8, 20, 8, 0, tzinfo=UTC)
        first = TOOL.default_output_path("TSOL-MS800", "02b0", stamp, device_index=1)
        second = TOOL.default_output_path("TSOL-MS800", "02b0", stamp, device_index=2)
        self.assertNotEqual(first, second)
        self.assertIn("device-01", first.name)
        self.assertIn("device-02", second.name)

    def test_multi_device_explicit_output_gets_index_suffix(self) -> None:
        from datetime import UTC, datetime

        path = TOOL.output_path_for_target(
            Path("dump.json"),
            None,
            "1097",
            datetime(2026, 8, 20, 8, 0, tzinfo=UTC),
            device_index=2,
            total_targets=3,
        )
        self.assertEqual(path.name, "dump_device-02.json")

    def test_known_1511_firmware_decoder(self) -> None:
        self.assertEqual(TOOL.firmware_version(0x1172), "V1.1.72")
        self.assertEqual(TOOL.firmware_version(0x1154), "V1.1.54")


if __name__ == "__main__":
    unittest.main()
