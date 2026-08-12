#!/usr/bin/env python3
# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Diagnose metadata exposed by a TSUN logger local HTTP interface."""

from __future__ import annotations

import argparse
from base64 import b64encode
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
import http.client
import importlib.util
from pathlib import Path
import re
import sys
from types import ModuleType
from urllib.parse import urljoin, urlsplit


ROOT = Path(__file__).parents[1]


def _stub_module(name: str, **attributes: object) -> ModuleType:
    """Install the minimum imports required by the shared pure parser."""
    module = ModuleType(name)
    for key, value in attributes.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


_stub_module(
    "aiohttp",
    BasicAuth=lambda *_args: None,
    ClientError=OSError,
    ClientTimeout=lambda **_kwargs: None,
)
_stub_module(
    "yarl",
    URL=type("URL", (), {"build": staticmethod(lambda **_kwargs: "")}),
)
_stub_module("homeassistant")
_stub_module("homeassistant.core", HomeAssistant=object)
_stub_module("homeassistant.helpers")
_stub_module(
    "homeassistant.helpers.aiohttp_client",
    async_get_clientsession=lambda _hass: None,
)

LOGGER_WEB_PATH = (
    ROOT / "custom_components" / "tsun_local" / "logger_web.py"
)
LOGGER_WEB_SPEC = importlib.util.spec_from_file_location(
    "tsun_logger_web_diagnostic", LOGGER_WEB_PATH
)
assert LOGGER_WEB_SPEC is not None and LOGGER_WEB_SPEC.loader is not None
LOGGER_WEB = importlib.util.module_from_spec(LOGGER_WEB_SPEC)
sys.modules[LOGGER_WEB_SPEC.name] = LOGGER_WEB
LOGGER_WEB_SPEC.loader.exec_module(LOGGER_WEB)
LOGGER_STATUS_PATHS = LOGGER_WEB.LOGGER_STATUS_PATHS
MAX_LOGGER_PAGE_SIZE = LOGGER_WEB.MAX_LOGGER_PAGE_SIZE
parse_logger_web_data = LOGGER_WEB.parse_logger_web_data


TIMEOUT = 5
MAX_LINKED_FILES = 20
SENSITIVE_NUMBER = re.compile(r"(?<!\d)([1-9]\d{7,9})(?!\d)")
MAC = re.compile(r"(?i)(?<![0-9a-f])([0-9a-f]{2}(?:[:-][0-9a-f]{2}){5})(?![0-9a-f])")
INTERESTING_MARKERS = (
    "device serial",
    "webdata_sn",
    "cover_mid",
    "device_sn",
    "logger_sn",
    "monitor_sn",
    "firmware",
    "webdata_ver",
    "cover_ver",
    "mac address",
    "sta_mac",
    "ap_mac",
)


@dataclass(frozen=True, slots=True)
class FetchResult:
    """One HTTP response without retaining credentials."""

    path: str
    auth_mode: str
    status: int | None
    content_type: str | None
    body: bytes
    error: str | None = None


class _References(HTMLParser):
    """Collect same-device script and frame references from one page."""

    def __init__(self) -> None:
        super().__init__()
        self.paths: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        attributes = dict(attrs)
        value = None
        if tag in {"script", "iframe", "frame"}:
            value = attributes.get("src")
        elif tag == "a":
            value = attributes.get("href")
        if not value:
            return
        parsed = urlsplit(value)
        if parsed.scheme or parsed.netloc or value.startswith("javascript:"):
            return
        path = parsed.path
        if path and path not in self.paths:
            self.paths.append(path)


def _mask_sn(value: int | None) -> str:
    """Display enough digits to compare devices without exposing the SN."""
    if value is None:
        return "not found"
    rendered = str(value)
    return f"{'*' * max(0, len(rendered) - 4)}{rendered[-4:]}"


def _mask_mac(value: str | None) -> str:
    """Hide the device address while showing that parsing succeeded."""
    if value is None:
        return "not found"
    parts = value.split(":")
    return "XX:XX:XX:XX:" + ":".join(parts[-2:])


def _mask_inverter_serial(value: str | None) -> str:
    """Mask the inverter serial while retaining a comparison suffix."""
    if value is None:
        return "not found"
    return f"{'*' * max(0, len(value) - 4)}{value[-4:]}"


def _mask_text(value: str) -> str:
    """Redact identifiers from snippets before printing them."""
    value = SENSITIVE_NUMBER.sub(
        lambda match: "*" * (len(match.group(1)) - 4) + match.group(1)[-4:],
        value,
    )
    return MAC.sub("XX:XX:XX:XX:XX:XX", value)


def _fetch(
    host: str,
    port: int,
    path: str,
    username: str,
    password: str,
    authenticated: bool,
) -> FetchResult:
    """Fetch a bounded local HTTP resource."""
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/javascript,*/*",
        "Connection": "close",
        "User-Agent": "TSUN-Local-diagnostic/1.0",
    }
    auth_mode = "Basic admin:***" if authenticated else "no authentication"
    if authenticated:
        token = b64encode(f"{username}:{password}".encode()).decode()
        headers["Authorization"] = f"Basic {token}"
    connection = http.client.HTTPConnection(host, port, timeout=TIMEOUT)
    try:
        connection.request("GET", path, headers=headers)
        response = connection.getresponse()
        content_type = response.getheader("Content-Type")
        body = response.read(MAX_LOGGER_PAGE_SIZE + 1)
        if len(body) > MAX_LOGGER_PAGE_SIZE:
            return FetchResult(
                path,
                auth_mode,
                response.status,
                content_type,
                b"",
                "response exceeds the 512 KiB safety limit",
            )
        return FetchResult(path, auth_mode, response.status, content_type, body)
    except (OSError, http.client.HTTPException) as error:
        return FetchResult(
            path,
            auth_mode,
            None,
            None,
            b"",
            type(error).__name__,
        )
    finally:
        connection.close()


def _decode(body: bytes, content_type: str | None) -> tuple[str, str]:
    """Decode common embedded-page encodings."""
    candidates: list[str] = []
    if content_type:
        if match := re.search(r"charset\s*=\s*[\"']?([^;\s\"']+)", content_type, re.I):
            candidates.append(match.group(1))
    if match := re.search(br"charset\s*=\s*[\"']?([A-Za-z0-9_-]+)", body[:4096], re.I):
        candidates.append(match.group(1).decode("ascii", errors="ignore"))
    candidates.extend(("utf-8", "gb18030", "latin-1"))
    for encoding in dict.fromkeys(candidates):
        try:
            return body.decode(encoding), encoding
        except (LookupError, UnicodeDecodeError):
            continue
    return body.decode("utf-8", errors="replace"), "utf-8 with replacements"


def _print_result(result: FetchResult) -> tuple[bool, list[str]]:
    """Print one safe result and return whether metadata was detected."""
    status = result.status if result.status is not None else "connection failed"
    print(f"\n[{result.auth_mode}] {result.path} -> {status}")
    if result.error:
        print(f"  Error: {result.error}")
        return False, []
    print(f"  Content-Type: {result.content_type or 'not supplied'}")
    print(f"  Complete body read: {len(result.body)} bytes")
    if result.status != 200 or not result.body:
        return False, []

    document, encoding = _decode(result.body, result.content_type)
    print(f"  Decoding: {encoding}")
    metadata = parse_logger_web_data(document)
    print(f"  Logger SN: {_mask_sn(metadata.logger_sn)}")
    print(
        "  Inverter serial number: "
        f"{_mask_inverter_serial(metadata.inverter_serial_number)}"
    )
    print(f"  Firmware: {metadata.firmware_version or 'not found'}")
    print(f"  MAC address: {_mask_mac(metadata.mac_address)}")

    lowered = document.lower()
    markers = [marker for marker in INTERESTING_MARKERS if marker in lowered]
    print(f"  Known markers: {', '.join(markers) if markers else 'none'}")

    snippets: list[str] = []
    visible = unescape(re.sub(r"<[^>]*>", " ", document))
    for keyword in ("device serial", "firmware", "mac address", "webdata_sn", "cover_mid"):
        position = visible.lower().find(keyword)
        if position < 0:
            position = lowered.find(keyword)
            source = document
        else:
            source = visible
        if position >= 0:
            snippet = re.sub(r"\s+", " ", source[position : position + 180]).strip()
            snippets.append(_mask_text(snippet))
    for snippet in dict.fromkeys(snippets):
        print(f"  Safe snippet: {snippet}")

    references = _References()
    try:
        references.feed(document)
    except Exception:
        pass
    detected = any(
        (
            metadata.logger_sn,
            metadata.inverter_serial_number,
            metadata.firmware_version,
            metadata.mac_address,
        )
    )
    return detected, references.paths[:MAX_LINKED_FILES]


def main() -> int:
    """Run a privacy-safe diagnostic against one local logger."""
    parser = argparse.ArgumentParser(
        description="Diagnose automatic TSUN logger metadata detection"
    )
    parser.add_argument("--host", required=True, help="Logger IP address")
    parser.add_argument("--http-port", type=int, default=80)
    parser.add_argument("--username", default="admin")
    parser.add_argument("--password", default="admin")
    args = parser.parse_args()

    print("TSUN Local - logger web metadata diagnostic")
    print("Identifiers are masked; credentials and raw pages are never printed or saved.")
    print(f"Target: {args.host}:{args.http_port}")

    paths = list(LOGGER_STATUS_PATHS)
    seen: set[tuple[str, bool]] = set()
    found = False
    index = 0
    while index < len(paths) and index < len(LOGGER_STATUS_PATHS) + MAX_LINKED_FILES:
        path = urljoin("/", paths[index])
        index += 1
        for authenticated in (False, True):
            key = (path, authenticated)
            if key in seen:
                continue
            seen.add(key)
            result = _fetch(
                args.host,
                args.http_port,
                path,
                args.username,
                args.password,
                authenticated,
            )
            detected, references = _print_result(result)
            found = found or detected
            for reference in references:
                resolved = urljoin(path, reference)
                if resolved not in paths:
                    paths.append(resolved)

    print("\nResult:")
    if found:
        print("  The local web interface exposes at least one usable metadata value.")
        print("  Copy the full diagnostic output above into the Codex conversation.")
        return 0
    print("  No logger SN, firmware, or MAC address was parsed from the tested resources.")
    print("  Copy the full diagnostic output above into the Codex conversation.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
