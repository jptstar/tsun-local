# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for passive Cloud Guard capability discovery."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from types import ModuleType
import unittest

ROOT = Path(__file__).parents[1]


def _load_cloud_guard() -> ModuleType:
    path = ROOT / "custom_components" / "tsun_local" / "cloud_guard.py"
    spec = importlib.util.spec_from_file_location("tsun_cloud_guard_tests", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


CLOUD_GUARD = _load_cloud_guard()


class CloudGuardParserTests(unittest.TestCase):
    """Protect the read-only Cloud Guard research parser."""

    def test_detects_1511_ssl_cloud_and_local_update_forms(self) -> None:
        remote = """
        <input name="server_a" value=",iot.talent-monitoring.com,10443,TCP">
        <input name="server_b" value=",iot.talent-monitoring.com,10443,TCP">
        <script>function server_setting_apply(num) { return num; }</script>
        """
        wireless = """
        <input name="wan_setting_dns" value="192.168.1.1">
        <script>function sta_form_apply() {}</script>
        """
        logger_update = """
        <input type="hidden" name="CMD" value="SW_UPLOAD">
        <input type="file" name="files">
        """
        inverter_update = """
        <input type="hidden" name="CMD" value="NBQ_UPLOAD">
        <input type="file" name="files">
        """

        result = CLOUD_GUARD.parse_cloud_guard_capabilities(
            remote_document=remote,
            wireless_document=wireless,
            logger_update_document=logger_update,
            inverter_update_document=inverter_update,
        )

        self.assertTrue(result.remote_server_configurable)
        self.assertTrue(result.dns_configurable)
        self.assertTrue(result.logger_firmware_upload_available)
        self.assertTrue(result.inverter_firmware_upload_available)
        self.assertEqual(result.configured_server_ports, (10443,))
        self.assertTrue(result.ssl_cloud_configured)
        self.assertFalse(result.write_operations_performed)

    def test_detects_02b0_port_without_marking_ssl(self) -> None:
        remote = """
        <script>function server_setting_apply(num) {}</script>
        <script>
        var server_a = ",iot.talent-monitoring.com,10000,TCP";
        var server_b = ",iot.talent-monitoring.com,10000,TCP";
        </script>
        """

        result = CLOUD_GUARD.parse_cloud_guard_capabilities(
            remote_document=remote,
            wireless_document=None,
            logger_update_document=None,
            inverter_update_document=None,
        )

        self.assertTrue(result.remote_server_configurable)
        self.assertEqual(result.configured_server_ports, (10000,))
        self.assertFalse(result.ssl_cloud_configured)
        self.assertFalse(result.write_operations_performed)

    def test_never_returns_server_hostname_or_dns_address(self) -> None:
        remote = """
        <script>function server_setting_apply(num) {}</script>
        <input name="server_a" value=",private.example,5005,TCP">
        """
        wireless = """
        <input name="wan_setting_dns" value="10.0.0.53">
        <script>function sta_form_apply() {}</script>
        """

        result = CLOUD_GUARD.parse_cloud_guard_capabilities(
            remote_document=remote,
            wireless_document=wireless,
            logger_update_document=None,
            inverter_update_document=None,
        )

        rendered = repr(result)
        self.assertNotIn("private.example", rendered)
        self.assertNotIn("10.0.0.53", rendered)
        self.assertEqual(result.configured_server_ports, (5005,))

    def test_missing_pages_mean_unknown_capability_not_a_write(self) -> None:
        result = CLOUD_GUARD.parse_cloud_guard_capabilities(
            remote_document=None,
            wireless_document=None,
            logger_update_document=None,
            inverter_update_document=None,
        )

        self.assertFalse(result.remote_server_configurable)
        self.assertFalse(result.dns_configurable)
        self.assertFalse(result.logger_firmware_upload_available)
        self.assertFalse(result.inverter_firmware_upload_available)
        self.assertEqual(result.configured_server_ports, ())
        self.assertFalse(result.write_operations_performed)


if __name__ == "__main__":
    unittest.main()
