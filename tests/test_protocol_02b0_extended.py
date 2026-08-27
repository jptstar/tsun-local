# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for the extended read-only 02B0 diagnostics added in 1.5.4."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

PROTOCOLS_PATH = (
    Path(__file__).parents[1]
    / "custom_components"
    / "tsun_local"
    / "protocols"
)
SPEC = importlib.util.spec_from_file_location(
    "tsun_local_02b0_extended_tests",
    PROTOCOLS_PATH / "__init__.py",
    submodule_search_locations=[str(PROTOCOLS_PATH)],
)
assert SPEC is not None and SPEC.loader is not None
PKG = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PKG
SPEC.loader.exec_module(PKG)

from tsun_local_02b0_extended_tests.protocol_02b0 import (  # noqa: E402
    DIAGNOSTIC_BLOCKS,
    Tsun02b0Client,
    build_modbus_request,
    decode_device_diagnostics,
    decode_measurements,
    firmware_version,
)


class Protocol02b0ExtendedTests(unittest.TestCase):
    """Protect the additional read-only GEN3 / GEN3 PLUS fields."""

    def test_extended_diagnostic_block_is_read_only_fc03(self) -> None:
        self.assertIn((0x03, 0x2000, 0x2010), DIAGNOSTIC_BLOCKS)
        self.assertEqual(
            build_modbus_request(0x03, 0x2000, 0x2010),
            bytes.fromhex("01 03 20 00 00 11 8E 06"),
        )

    def test_exposes_all_extended_02b0_keys(self) -> None:
        keys = Tsun02b0Client("192.0.2.10", 8899, 123456).measurement_keys
        for key in (
            "inverter_firmware_version",
            "inverter_temperature",
            "boot_status_raw",
            "dsp_status_raw",
            "work_mode_raw",
            "output_shutdown_raw",
            "rated_level_raw",
            "input_coefficient",
            "product_compliance_type_raw",
        ):
            self.assertIn(key, keys)

    def test_decodes_firmware_and_temperature(self) -> None:
        registers = {address: 0 for address in range(0x3008, 0x302B)}
        registers.update(
            {
                0x3008: 0x4010,
                0x3009: 2300,
                0x300A: 100,
                0x300B: 5000,
                0x300C: 65,
                0x300E: 800,
                0x300F: 4000,
                0x301C: 100,
                0x301D: 0,
                0x301E: 12345,
                0x3010: 400,
                0x3011: 100,
                0x3012: 4000,
                0x301F: 100,
                0x3020: 0,
                0x3021: 12345,
            }
        )
        data = decode_measurements(registers, 1)
        self.assertEqual(firmware_version(0x4010), "V4.0.10")
        self.assertEqual(data["inverter_firmware_version"], "V4.0.10")
        self.assertEqual(data["inverter_temperature"], 25)

    def test_decodes_status_coefficient_and_raw_compliance_type(self) -> None:
        data = decode_device_diagnostics(
            {
                0x2000: 1,
                0x2001: 2,
                0x2003: 3,
                0x2006: 0,
                0x2008: 4,
                0x2009: 512,
                0x2010: 6,
            }
        )
        self.assertEqual(data["boot_status_raw"], 1)
        self.assertEqual(data["dsp_status_raw"], 2)
        self.assertEqual(data["work_mode_raw"], 3)
        self.assertEqual(data["output_shutdown_raw"], 0)
        self.assertEqual(data["rated_level_raw"], 4)
        self.assertEqual(data["input_coefficient"], 50.0)
        self.assertEqual(data["product_compliance_type_raw"], 6)


if __name__ == "__main__":
    unittest.main()
