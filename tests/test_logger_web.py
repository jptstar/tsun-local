# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for automatic Monitor SN / Logger SN extraction."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from types import ModuleType
import unittest


ROOT = Path(__file__).parents[1]


def _module(name: str, **attributes: object) -> ModuleType:
    module = ModuleType(name)
    for key, value in attributes.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


def _load_logger_web() -> ModuleType:
    _module(
        "aiohttp",
        BasicAuth=lambda *_args: None,
        ClientError=OSError,
        ClientTimeout=lambda **_kwargs: None,
    )
    _module("yarl", URL=type("URL", (), {"build": staticmethod(lambda **_kwargs: "")}))
    _module("homeassistant")
    _module("homeassistant.core", HomeAssistant=object)
    _module("homeassistant.helpers")
    _module(
        "homeassistant.helpers.aiohttp_client",
        async_get_clientsession=lambda _hass: None,
    )

    path = ROOT / "custom_components" / "tsun_local" / "logger_web.py"
    spec = importlib.util.spec_from_file_location("tsun_logger_web_tests", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


LOGGER_WEB = _load_logger_web()


class LoggerWebParserTests(unittest.TestCase):
    """Protect logger SN parsing and the manual-fallback decision."""

    def test_reads_device_serial_number(self) -> None:
        document = """
        <tr><td>Inverter serial number</td><td>MX500ABC123</td></tr>
        <tr><td>Device serial number</td><td>1234567890</td></tr>
        """
        self.assertEqual(LOGGER_WEB.parse_logger_sn(document), 1234567890)

    def test_reads_device_serial_number_split_by_html_tags(self) -> None:
        document = """
        <td>Device <strong>serial</strong> number</td>
        <td><span>1234567890</span></td>
        """
        self.assertEqual(LOGGER_WEB.parse_logger_sn(document), 1234567890)

    def test_reads_serial_from_access_point_name(self) -> None:
        self.assertEqual(
            LOGGER_WEB.parse_logger_sn("<span>SSID</span> AP_2345678901"),
            2345678901,
        )

    def test_reads_javascript_device_sn(self) -> None:
        self.assertEqual(
            LOGGER_WEB.parse_logger_sn('device_sn = "2345678901";'),
            2345678901,
        )

    def test_does_not_treat_inverter_webdata_sn_as_logger_sn(self) -> None:
        self.assertIsNone(
            LOGGER_WEB.parse_logger_sn('var webdata_sn = "TESTINVERTER0001";')
        )

    def test_reads_cover_mid_used_by_embedded_logger_pages(self) -> None:
        self.assertEqual(
            LOGGER_WEB.parse_logger_sn('var cover_mid = "3456789012";'),
            3456789012,
        )

    def test_prefers_cover_mid_over_inverter_serial(self) -> None:
        self.assertEqual(
            LOGGER_WEB.parse_logger_sn(
                'var webdata_sn = "TESTINVERTER0001"; '
                'var cover_mid = "3456789012";'
            ),
            3456789012,
        )

    def test_reads_device_firmware_and_mac_address(self) -> None:
        document = """
        <h3>Inverter information</h3>
        <div>Firmware version (main) INVERTER_FW</div>
        <h3>Device information</h3>
        <div>Device serial number 1234567890</div>
        <div>Firmware version LSW_TEST_1511_1.03</div>
        <div>MAC address 02:00:00:00:00:01</div>
        """
        metadata = LOGGER_WEB.parse_logger_web_data(document)

        self.assertEqual(metadata.logger_sn, 1234567890)
        self.assertEqual(metadata.firmware_version, "LSW_TEST_1511_1.03")
        self.assertEqual(metadata.mac_address, "02:00:00:00:00:01")

    def test_reads_firmware_and_normalizes_mac_from_javascript(self) -> None:
        document = """
        var webdata_ver = "LSW_TEST_1.00";
        var cover_sta_mac = "02-00-00-00-00-02";
        """
        metadata = LOGGER_WEB.parse_logger_web_data(document)

        self.assertEqual(metadata.firmware_version, "LSW_TEST_1.00")
        self.assertEqual(metadata.mac_address, "02:00:00:00:00:02")

    def test_reads_status_page_field_roles(self) -> None:
        document = """
        var webdata_sn = "TESTINVERTER0001 ";
        var cover_mid = "3456789012";
        var cover_ver = "LSW5_SSL_1511_1.03";
        var cover_sta_mac = "02:00:00:00:00:03";
        """

        metadata = LOGGER_WEB.parse_logger_web_data(document)

        self.assertEqual(metadata.logger_sn, 3456789012)
        self.assertEqual(
            metadata.inverter_serial_number, "TESTINVERTER0001"
        )
        self.assertEqual(metadata.firmware_version, "LSW5_SSL_1511_1.03")
        self.assertEqual(metadata.mac_address, "02:00:00:00:00:03")

    def test_does_not_use_inverter_serial_number(self) -> None:
        self.assertIsNone(
            LOGGER_WEB.parse_logger_sn(
                "Inverter serial number 2345678901; firmware 1511"
            )
        )


class _ChunkedContent:
    """Small asynchronous response body used to verify complete reads."""

    def __init__(self, *chunks: bytes) -> None:
        self._chunks = chunks

    async def iter_chunked(self, _size: int):
        for chunk in self._chunks:
            yield chunk


class _Response:
    """Minimal aiohttp response context manager."""

    status = 200
    content_length = None

    def __init__(self, document: str) -> None:
        self.content = _ChunkedContent(document.encode())

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args: object) -> None:
        return None


class _Session:
    """Return one page per HTTP request."""

    def __init__(self, *documents: str) -> None:
        self._responses = iter(_Response(document) for document in documents)

    def get(self, *_args: object, **_kwargs: object) -> _Response:
        return next(self._responses)


class LoggerWebReaderTests(unittest.IsolatedAsyncioTestCase):
    """Protect complete bounded reads of embedded status pages."""

    async def test_reads_all_chunks_before_parsing(self) -> None:
        content = await LOGGER_WEB._async_read_limited(
            _ChunkedContent(
                b"<html><body>Device serial ",
                b"number 3456789012</body></html>",
            )
        )

        self.assertIsNotNone(content)
        self.assertEqual(
            LOGGER_WEB.parse_logger_sn(content.decode()),
            3456789012,
        )

    async def test_rejects_oversized_page(self) -> None:
        content = await LOGGER_WEB._async_read_limited(
            _ChunkedContent(b"x" * (LOGGER_WEB.MAX_LOGGER_PAGE_SIZE + 1))
        )
        self.assertIsNone(content)

    async def test_reads_authenticated_page_when_public_page_has_no_inverter_sn(
        self,
    ) -> None:
        public_page = """
        var cover_mid = "3456789012";
        var cover_ver = "LSW_TEST_1.00";
        var cover_sta_mac = "02:00:00:00:00:04";
        var webdata_sn = "";
        """
        authenticated_page = 'var webdata_sn = "TESTINVERTER0001";'
        original_session_factory = LOGGER_WEB.async_get_clientsession
        LOGGER_WEB.async_get_clientsession = lambda _hass: _Session(
            public_page, authenticated_page
        )
        try:
            metadata = await LOGGER_WEB.async_read_logger_web_data(
                object(), "192.0.2.10"
            )
        finally:
            LOGGER_WEB.async_get_clientsession = original_session_factory

        self.assertEqual(metadata.logger_sn, 3456789012)
        self.assertEqual(
            metadata.inverter_serial_number, "TESTINVERTER0001"
        )
        self.assertEqual(metadata.firmware_version, "LSW_TEST_1.00")
        self.assertEqual(metadata.mac_address, "02:00:00:00:00:04")

    def test_rejects_value_outside_unsigned_32_bit_range(self) -> None:
        self.assertIsNone(
            LOGGER_WEB.parse_logger_sn(
                "Device serial number 9999999999; SSID AP_9999999999"
            )
        )


if __name__ == "__main__":
    unittest.main()
