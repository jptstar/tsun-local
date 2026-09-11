from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


PROBE_PATH = Path(__file__).resolve().parents[1] / "tools" / "y4z_3026_readonly_probe.py"
SPEC = importlib.util.spec_from_file_location("y4z_3026_probe", PROBE_PATH)
assert SPEC is not None and SPEC.loader is not None
PROBE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROBE)


class Y4Z3026ProbeTests(unittest.TestCase):
    def test_modbus_read_is_function_03_and_valid_crc(self) -> None:
        frame = PROBE.build_modbus_read(0x0000, 45)
        self.assertEqual(frame[:6], b"\x01\x03\x00\x00\x00\x2d")
        self.assertEqual(PROBE.crc16_modbus(frame[:-2]), frame[-2:])

    def test_ap_request_uses_3026_sensor_list(self) -> None:
        payload = PROBE.build_modbus_read(0x0000, 45)
        frame = PROBE.build_ap_request(1234567890, payload)
        self.assertEqual(frame[0], 0xA5)
        self.assertEqual(frame[-1], 0x15)
        self.assertEqual(frame[11], 0x02)
        self.assertEqual(int.from_bytes(frame[12:14], "little"), 0x3026)
        self.assertEqual(PROBE.checksum_ap(frame[1:-2]), frame[-2])

    def test_parse_modbus_reply_preserves_raw_registers(self) -> None:
        values = list(range(45))
        data = b"".join(value.to_bytes(2, "big") for value in values)
        body = bytes((1, 3, len(data))) + data
        payload = body + PROBE.crc16_modbus(body)
        parsed = PROBE.parse_modbus_reply(payload, 0x0000, 45)
        self.assertEqual(parsed[0x0000], 0)
        self.assertEqual(parsed[0x0001], 1)
        self.assertEqual(parsed[0x002C], 44)

    def test_changed_registers_only_reports_changes(self) -> None:
        sample1 = PROBE.Sample("a", {"0x0000": 1, "0x0001": 2})
        sample2 = PROBE.Sample("b", {"0x0000": 1, "0x0001": 3})
        self.assertEqual(
            PROBE.changed_registers([sample1, sample2]),
            [{"register": "0x0001", "values": [2, 3]}],
        )


if __name__ == "__main__":
    unittest.main()
