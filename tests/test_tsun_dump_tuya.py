# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Regression tests for experimental Tuya/ThingClips diagnostic discovery."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


TOOL_PATH = Path(__file__).parents[1] / "tools" / "tsun_dump.py"
SPEC = importlib.util.spec_from_file_location("tsun_dump_tuya_test", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
TOOL = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = TOOL
SPEC.loader.exec_module(TOOL)


class TuyaDiagnosticTests(unittest.TestCase):
    """Keep Tuya OEM detection bounded, private and read-only."""

    def test_tuya_transport_constants_and_framing(self) -> None:
        self.assertEqual(TOOL.TUYA_TCP_PORT, 6668)
        self.assertEqual(TOOL.TUYA_UDP_PORTS, (6666, 6667, 7000))
        self.assertEqual(TOOL._tuya_framing(b"\x00\x00\x55\xaa\x00", 6666), "tuya-55aa")
        self.assertEqual(TOOL._tuya_framing(b"\x00\x00\x66\x99\x00", 7000), "tuya-6699")

    def test_tuya_candidate_does_not_require_tsun_monitor_sn(self) -> None:
        device = TOOL.DiscoveryDevice(host="192.0.2.10")
        device.tuya_6668_open = True
        self.assertTrue(TOOL._is_tuya_candidate(device))
        metadata = TOOL._tuya_candidate_metadata(device)
        self.assertEqual(metadata["transport_kind"], "tuya_oem_candidate")
        self.assertTrue(metadata["tuya_tcp_6668"])

    def test_tuya_capture_contract_excludes_secrets_and_writes(self) -> None:
        source = TOOL_PATH.read_text(encoding="utf-8")
        self.assertIn('"tuya_local_key_in_output": False', source)
        self.assertIn('"tuya_device_id_in_output": False', source)
        self.assertIn('"configuration_write_performed": False', source)
        self.assertIn('"application_payload_sent": False', source)


if __name__ == "__main__":
    unittest.main()
