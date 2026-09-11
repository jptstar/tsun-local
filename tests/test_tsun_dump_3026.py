from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

TOOL_PATH = Path(__file__).resolve().parents[1] / "tools" / "tsun_dump.py"
SPEC = importlib.util.spec_from_file_location("tsun_dump_3026_test", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
TOOL = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = TOOL
SPEC.loader.exec_module(TOOL)


class Experimental3026DiagnosticTests(unittest.TestCase):
    def test_3026_is_available_to_generic_diagnostic(self) -> None:
        self.assertIn("3026", TOOL.SUPPORTED_PROTOCOLS)
        self.assertIn("3026", TOOL.EXPERIMENTAL_PROTOCOLS)

    def test_3026_firmware_hint_is_recognized(self) -> None:
        self.assertEqual(TOOL.protocol_from_firmware("LSW5_SSL_3026_1.00"), "3026")

    def test_3026_capture_covers_45_raw_registers(self) -> None:
        dynamic, supplemental = TOOL.capture_plans("3026", full=True)
        self.assertEqual(
            dynamic,
            [(0x0000, 0x000F), (0x0010, 0x001F), (0x0020, 0x002C)],
        )
        self.assertEqual(supplemental, [])

    def test_3026_probe_uses_sensor_list(self) -> None:
        with patch.object(TOOL, "read_modbus_block") as reader:
            reader.return_value = ({0: 1}, b"request", b"response")
            TOOL._probe_protocol("3026", "192.0.2.10", 8899, 1234567890, 1.0)
        reader.assert_called_once_with(
            "192.0.2.10",
            8899,
            1234567890,
            0x0000,
            0x0000,
            sensor_list=0x3026,
            timeout=1.0,
        )

    def test_3026_decoding_stays_raw_only(self) -> None:
        decoded = TOOL.decode_known("3026", {"0x0000": 123, "0x0001": 456})
        self.assertTrue(decoded["experimental_protocol"])
        self.assertEqual(decoded["candidate_sensor_list"], "0x3026")
        self.assertEqual(
            decoded["mapping_status"],
            "raw_only_pending_hardware_validation",
        )
        self.assertEqual(decoded["detected_pv_count"], 0)
        self.assertNotIn("ac_power", decoded)
        self.assertNotIn("battery_soc", decoded)


if __name__ == "__main__":
    unittest.main()
