# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Regression test for logger Wi-Fi signal page fallback."""

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
    spec = importlib.util.spec_from_file_location("tsun_logger_wifi_fallback", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


LOGGER_WEB = _load_logger_web()


class _ChunkedContent:
    def __init__(self, document: str) -> None:
        self._document = document

    async def iter_chunked(self, _size: int):
        yield self._document.encode()


class _Response:
    status = 200
    content_length = None

    def __init__(self, document: str) -> None:
        self.content = _ChunkedContent(document)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args: object) -> None:
        return None


class _Session:
    def __init__(self, *documents: str) -> None:
        self._responses = iter(_Response(document) for document in documents)

    def get(self, *_args: object, **_kwargs: object) -> _Response:
        return next(self._responses)


class LoggerWifiSignalFallbackTests(unittest.IsolatedAsyncioTestCase):
    async def test_continues_to_status_page_when_first_page_has_no_rssi(self) -> None:
        # Real LSW5 pattern: /index_cn.html is a valid shell page without RSSI;
        # /status.html contains cover_sta_rssi.
        original_session_factory = LOGGER_WEB.async_get_clientsession
        LOGGER_WEB.async_get_clientsession = lambda _hass: _Session(
            "<html>index shell without RSSI</html>",
            "<html>index shell without RSSI</html>",
            "<html>english shell without RSSI</html>",
            "<html>english shell without RSSI</html>",
            'var cover_sta_rssi = "16%";',
        )
        try:
            signal = await LOGGER_WEB.async_read_logger_wifi_signal(
                object(), "192.0.2.10"
            )
        finally:
            LOGGER_WEB.async_get_clientsession = original_session_factory

        self.assertEqual(signal, 16)


if __name__ == "__main__":
    unittest.main()
