# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Regression tests for TSUN network firmware discovery."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch


DISCOVERY_PATH = (
    Path(__file__).parents[1]
    / "custom_components"
    / "tsun_local"
    / "discovery.py"
)
SPEC = importlib.util.spec_from_file_location(
    "tsun_local_discovery_http_tests", DISCOVERY_PATH
)
assert SPEC is not None and SPEC.loader is not None
DISCOVERY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DISCOVERY)


class DiscoveryHttpTests(unittest.IsolatedAsyncioTestCase):
    """Protect firmware reads on embedded loggers that keep TCP open."""

    async def test_content_length_does_not_wait_for_connection_close(self) -> None:
        body = b'var cover_ver = "LSW5_SSL_1511_1.03";'
        header = (
            b"HTTP/1.1 200 OK\r\n"
            + f"Content-Length: {len(body)}\r\n".encode()
            + b"Connection: keep-alive\r\n\r\n"
        )

        class FakeReader:
            async def readuntil(self, separator: bytes) -> bytes:
                self.assert_separator = separator
                return header

            async def readexactly(self, size: int) -> bytes:
                self.assert_size = size
                return body

            async def read(self, _size: int) -> bytes:
                raise AssertionError("Discovery must not wait for EOF")

        class FakeWriter:
            def write(self, _request: bytes) -> None:
                pass

            async def drain(self) -> None:
                pass

            def close(self) -> None:
                pass

            async def wait_closed(self) -> None:
                pass

        async def open_connection(_host: str, _port: int):
            return FakeReader(), FakeWriter()

        with patch.object(
            DISCOVERY.asyncio, "open_connection", new=open_connection
        ):
            document = await DISCOVERY._async_read_status_document(
                "192.0.2.10", "/index_cn.html", authenticated=True
            )

        self.assertEqual(document, body.decode())
        self.assertEqual(
            DISCOVERY.protocol_from_firmware(
                DISCOVERY._firmware_version_from_document(document)
            ),
            "1511",
        )

    def test_known_real_firmware_tokens(self) -> None:
        self.assertEqual(
            DISCOVERY.protocol_from_firmware("LSW5_SSL_1511_1.03"), "1511"
        )
        self.assertEqual(
            DISCOVERY.protocol_from_firmware("LSW5BLE_17_02B0_1.08-D1"),
            "02b0",
        )
        self.assertIsNone(
            DISCOVERY.protocol_from_firmware("LSW3_15_FFFF_1.0.9E")
        )


if __name__ == "__main__":
    unittest.main()
