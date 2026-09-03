#!/usr/bin/env python3
# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Standalone, privacy-safe, strictly read-only TSUN hardware dump tool.

The tool uses only the Python standard library. It supports the local TSUN
protocol families currently researched by TSUN Local: 1511, 02B0 and 1097.

Discovery deliberately uses several independent read-only paths because TSUN
logger generations do not all answer the same discovery service reliably:
UDP 48899, bounded TCP 8899 scanning, local HTTP identity pages and an AP
identity probe with logger SN=0. No inverter configuration write operation is
implemented anywhere in this file.
"""

from __future__ import annotations

import argparse
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import http.client
from ipaddress import IPv4Address, IPv4Network, ip_network
import json
import math
from pathlib import Path
import re
import socket
import sys
import time
from typing import Any, Callable, Iterable


TOOL_VERSION = "2.4.0"
DUMP_FORMAT = "tsun-local-hardware-dump"
SCHEMA_VERSION = 3
SOURCE_URL = "https://raw.githubusercontent.com/jptstar/tsun-local/main/tools/tsun_dump.py"

DEFAULT_PORT = 8899
DEFAULT_DISCOVERY_PORT = 48899
DEFAULT_DISCOVERY_TIMEOUT = 4.0
DEFAULT_TCP_SCAN_TIMEOUT = 0.45
DEFAULT_HTTP_SCAN_TIMEOUT = 0.35
DEFAULT_HTTP_PAGE_TIMEOUT = 1.5
DEFAULT_TIMEOUT = 6.0
DEFAULT_DISCOVERY_CONCURRENCY = 64
DEFAULT_SNAPSHOTS = 3
DEFAULT_SNAPSHOT_INTERVAL = 3.0
MAX_MODBUS_REGISTERS_PER_READ = 16
MAX_HTTP_PAGE_SIZE = 512 * 1024
MIN_SCAN_PREFIX = 24
PROTOCOL_PROBE_RETRIES = 3
PROTOCOL_RETRY_DELAY = 0.4
SUPPORTED_PROTOCOLS = ("1511", "02b0", "1097")

DISCOVERY_MESSAGES = (
    b"WIFIKIT-214028-READ",
    b"HF-A11ASSISTHREAD",
    b"devicelinkfind",
)
LOGGER_STATUS_PATHS = ("/index_cn.html", "/index.html", "/status.html", "/")
LOGGER_PROFILE_PATHS = ("/hide_set_edit.html",)
LOGGER_WEB_CAPTURE_PATHS = (*LOGGER_STATUS_PATHS, *LOGGER_PROFILE_PATHS)
LOGGER_WEB_AUTH = base64.b64encode(b"admin:admin").decode("ascii")

_SERIAL_TOKEN = re.compile(r"(?<!\d)(\d{8,10})(?!\d)")
_SAFE_NAME = re.compile(r"[^a-z0-9._-]+")
_FIRMWARE_PROTOCOL_TOKEN = re.compile(
    r"(?:^|[_-])(1511|1097|02b0)(?=[_-]|$)", re.IGNORECASE
)
_FIRMWARE_PATTERNS = (
    re.compile(
        r"\b(?:webdata|cover)[_-]ver\s*[:=]\s*[\"']"
        r"([A-Za-z0-9][A-Za-z0-9._-]{1,79})",
        re.IGNORECASE,
    ),
    re.compile(
        r"firmware\s*version[^A-Za-z0-9]+"
        r"([A-Za-z0-9][A-Za-z0-9._-]{1,79})",
        re.IGNORECASE,
    ),
)
_LOGGER_SN_PATTERNS = (
    re.compile(
        r"\bcover[_-]mid\b[\s\S]{0,160}?([1-9]\d{7,9})",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:device|logger|monitor)[_-]?(?:serial(?:_number)?|sn)\b"
        r"[\s\S]{0,160}?([1-9]\d{7,9})",
        re.IGNORECASE,
    ),
    re.compile(r"\bAP_([1-9]\d{7,9})\b", re.IGNORECASE),
)

_MAC_TOKEN = re.compile(
    r"\b([0-9A-F]{2})[:-]([0-9A-F]{2})[:-]([0-9A-F]{2})[:-]"
    r"([0-9A-F]{2})[:-]([0-9A-F]{2})[:-]([0-9A-F]{2})\b",
    re.IGNORECASE,
)
_IPV4_TOKEN = re.compile(
    r"(?<!\d)(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}"
    r"(?:25[0-5]|2[0-4]\d|1?\d?\d)(?!\d)"
)
_EMAIL_TOKEN = re.compile(
    r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE
)
_INVERTER_SERIAL_PATTERNS = (
    re.compile(
        r"\bwebdata[_-]sn\s*[:=]\s*[\"']\s*"
        r"([A-Za-z0-9][A-Za-z0-9_-]{3,63})\s*[\"']",
        re.IGNORECASE,
    ),
    re.compile(
        r"\binverter[_-]?(?:serial(?:_number)?|sn)\b\s*[:=]\s*[\"']\s*"
        r"([A-Za-z0-9][A-Za-z0-9_-]{3,63})\s*[\"']",
        re.IGNORECASE,
    ),
)
_RAW_PROFILE_PATTERNS = (
    re.compile(
        r"\binv_tp\b\s*[:=]\s*[\"']\s*([^\"']{1,127}?)\s*[\"']",
        re.IGNORECASE,
    ),
)
_WIFI_SIGNAL_PATTERNS = (
    re.compile(
        r"\bcover_sta_rssi\b\s*[:=]\s*[\"']?\s*(-?\d{1,3})",
        re.IGNORECASE,
    ),
)
_SENSITIVE_FIELD_NAME = (
    r"[A-Za-z0-9_-]*(?:ssid|password|passwd|pwd|psk|token|secret|"
    r"api[_-]?key|access[_-]?key|username|user_name|email)[A-Za-z0-9_-]*"
)
_SENSITIVE_ASSIGNMENT = re.compile(
    rf"(?P<prefix>\b{_SENSITIVE_FIELD_NAME}\b\s*[:=]\s*)"
    r"(?P<quote>[\"'])(?P<value>.*?)(?P=quote)",
    re.IGNORECASE | re.DOTALL,
)
_SENSITIVE_HTML_NAME_VALUE = re.compile(
    rf"(?P<prefix><[^>]*\b(?:name|id)\s*=\s*[\"']{_SENSITIVE_FIELD_NAME}[\"']"
    r"[^>]*\bvalue\s*=\s*)(?P<quote>[\"'])(?P<value>.*?)(?P=quote)",
    re.IGNORECASE | re.DOTALL,
)


class TsunProtocolError(Exception):
    """Raised when a TSUN protocol frame is invalid."""


@dataclass(slots=True)
class DiscoveryDevice:
    """One logger candidate discovered by one or more read-only methods."""

    host: str
    serial_candidates: set[int] = field(default_factory=set)
    replies: int = 0
    sources: set[str] = field(default_factory=set)
    firmware_version: str | None = None
    protocol_hint: str | None = None
    tcp_8899_open: bool = False
    http_open: bool = False


def safe_error_details(error: Exception) -> dict[str, str]:
    """Return useful error details without addresses, serials or payload IDs."""
    result = {"type": type(error).__name__}
    if isinstance(error, TsunProtocolError):
        result["detail"] = str(error)
    elif isinstance(error, TimeoutError):
        result["detail"] = "timeout waiting for device response"
    elif isinstance(error, ConnectionResetError):
        result["detail"] = "connection reset by device"
    elif isinstance(error, ConnectionRefusedError):
        result["detail"] = "connection refused by device"
    return result


# ---------------------------------------------------------------------------
# AP envelope + protocol framing (READ ONLY)
# ---------------------------------------------------------------------------

def checksum_ap(data: bytes) -> int:
    return sum(data) & 0xFF


def build_ap_frame(logger_sn: int, payload: bytes, sensor_list: int = 0) -> bytes:
    if logger_sn != 0 and not _valid_monitor_sn(logger_sn):
        raise ValueError("Monitor SN must fit the four-byte logger field")
    if not 0 <= sensor_list <= 0xFFFF:
        raise ValueError("sensor_list must fit the two-byte AP field")
    data = b"\x02" + sensor_list.to_bytes(2, "little") + bytes(12) + payload
    scope = (
        len(data).to_bytes(2, "little")
        + b"\x10\x45\x00\x00"
        + logger_sn.to_bytes(4, "little")
        + data
    )
    return b"\xA5" + scope + bytes((checksum_ap(scope), 0x15))


def _recv_exact(sock: socket.socket, count: int) -> bytes:
    data = bytearray()
    while len(data) < count:
        chunk = sock.recv(count - len(data))
        if not chunk:
            raise TsunProtocolError("Unexpected end of TCP stream")
        data.extend(chunk)
    return bytes(data)


def read_ap_frame(sock: socket.socket) -> bytes:
    header = _recv_exact(sock, 3)
    if header[0] != 0xA5:
        raise TsunProtocolError("Invalid AP start marker")
    remaining = int.from_bytes(header[1:3], "little") + 10
    return header + _recv_exact(sock, remaining)


def _validate_ap_frame(frame: bytes) -> None:
    if len(frame) < 27 or frame[0] != 0xA5 or frame[-1] != 0x15:
        raise TsunProtocolError("Invalid AP frame markers or length")
    expected = int.from_bytes(frame[1:3], "little") + 13
    if len(frame) != expected:
        raise TsunProtocolError("Invalid AP frame length")
    if checksum_ap(frame[1:-2]) != frame[-2]:
        raise TsunProtocolError("Invalid AP checksum")


def extract_ap_logger_sn(frame: bytes) -> int:
    """Return the logger identity carried by a validated AP response."""
    _validate_ap_frame(frame)
    logger_sn = int.from_bytes(frame[7:11], "little")
    if not _valid_monitor_sn(logger_sn):
        raise TsunProtocolError("AP response does not contain a logger identifier")
    return logger_sn


def parse_ap_frame(frame: bytes) -> bytes:
    _validate_ap_frame(frame)
    if frame[11] != 0x02:
        raise TsunProtocolError("Unexpected AP frame type")
    if frame[12] != 0x01:
        raise TsunProtocolError(f"AP returned status 0x{frame[12]:02X}")
    return frame[25:-2]


def crc16_modbus(data: bytes) -> bytes:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc.to_bytes(2, "little")


def build_modbus_request(start: int, end: int) -> bytes:
    """Build an FC03 Modbus RTU read request."""
    count = end - start + 1
    body = b"\x01\x03" + start.to_bytes(2, "big") + count.to_bytes(2, "big")
    return body + crc16_modbus(body)


def parse_modbus_response(frame: bytes, start: int, end: int) -> dict[int, int]:
    if len(frame) < 5 or frame[0] != 0x01:
        raise TsunProtocolError("Invalid Modbus frame")
    if crc16_modbus(frame[:-2]) != frame[-2:]:
        raise TsunProtocolError("Invalid Modbus CRC")
    if frame[1] == 0x83:
        raise TsunProtocolError(f"Modbus exception 0x{frame[2]:02X}")
    if frame[1] != 0x03:
        raise TsunProtocolError("Unexpected Modbus function")
    count = end - start + 1
    data_length = frame[2]
    if data_length != count * 2 or len(frame) != 3 + data_length + 2:
        raise TsunProtocolError("Unexpected Modbus data length")
    values = frame[3 : 3 + data_length]
    return {
        start + index: int.from_bytes(values[index * 2 : index * 2 + 2], "big")
        for index in range(count)
    }


def crc16_1511(data: bytes) -> bytes:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc.to_bytes(2, "big")


def build_1511_request(address_tag: int, function: int, start: int, end: int) -> bytes:
    count = end - start + 1
    body = bytes((address_tag, function, 0x00)) + start.to_bytes(2, "big")
    body += b"\x00\x02" + count.to_bytes(2, "big")
    return body + crc16_1511(body)


def parse_1511_response(
    frame: bytes, address_tag: int, function: int, start: int, end: int
) -> dict[int, int]:
    if len(frame) < 11 or frame[0] != 0x7E:
        raise TsunProtocolError("Invalid 1511 frame")
    if crc16_1511(frame[1:-2]) != frame[-2:]:
        raise TsunProtocolError("Invalid 1511 CRC")
    if frame[1] != address_tag or frame[2] != (function | 0x80):
        raise TsunProtocolError("Unexpected 1511 address or response function")
    if frame[3] != 0x01:
        raise TsunProtocolError(f"1511 returned status 0x{frame[3]:02X}")
    if int.from_bytes(frame[4:6], "big") != start:
        raise TsunProtocolError("Unexpected 1511 start address")
    data_length = int.from_bytes(frame[6:8], "big")
    count = end - start + 1
    if data_length != count * 2 or len(frame) != 8 + data_length + 2:
        raise TsunProtocolError("Unexpected 1511 data length")
    values = frame[8 : 8 + data_length]
    return {
        start + index: int.from_bytes(values[index * 2 : index * 2 + 2], "little")
        for index in range(count)
    }


def exchange_ap(
    host: str,
    port: int,
    logger_sn: int,
    payload: bytes,
    *,
    sensor_list: int = 0,
    timeout: float = DEFAULT_TIMEOUT,
) -> bytes:
    request = build_ap_frame(logger_sn, payload, sensor_list=sensor_list)
    with socket.create_connection((host, port), timeout=timeout) as sock:
        sock.settimeout(timeout)
        sock.sendall(request)
        return parse_ap_frame(read_ap_frame(sock))


def read_modbus_block(
    host: str,
    port: int,
    logger_sn: int,
    start: int,
    end: int,
    *,
    sensor_list: int,
    timeout: float,
) -> tuple[dict[int, int], bytes, bytes]:
    payload = build_modbus_request(start, end)
    response = exchange_ap(
        host, port, logger_sn, payload, sensor_list=sensor_list, timeout=timeout
    )
    return parse_modbus_response(response, start, end), payload, response


def read_1511_block(
    host: str,
    port: int,
    logger_sn: int,
    address_tag: int,
    function: int,
    start: int,
    end: int,
    *,
    timeout: float,
) -> tuple[dict[int, int], bytes, bytes]:
    payload = build_1511_request(address_tag, function, start, end)
    response = exchange_ap(host, port, logger_sn, payload, timeout=timeout)
    return (
        parse_1511_response(response, address_tag, function, start, end),
        payload,
        response,
    )


# ---------------------------------------------------------------------------
# Network discovery / target resolution
# ---------------------------------------------------------------------------

def _valid_monitor_sn(value: int) -> bool:
    return 0 < value <= 0xFFFFFFFF


def _serial_candidates_from_object(value: Any, key_hint: str = "") -> set[int]:
    found: set[int] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            found.update(_serial_candidates_from_object(child, str(key).lower()))
        return found
    if isinstance(value, list):
        for child in value:
            found.update(_serial_candidates_from_object(child, key_hint))
        return found
    if any(token in key_hint for token in ("serial", "logger", "monitor", "sn")):
        try:
            candidate = int(str(value).strip())
        except (TypeError, ValueError):
            return found
        if _valid_monitor_sn(candidate):
            found.add(candidate)
    return found


def serial_candidates_from_payload(payload: bytes) -> set[int]:
    """Extract plausible Monitor SN values from a discovery response."""
    text = payload.decode("utf-8", errors="replace").strip("\x00\r\n ")
    found: set[int] = set()
    try:
        parsed = json.loads(text)
    except (TypeError, ValueError):
        parsed = None
    if parsed is not None:
        found.update(_serial_candidates_from_object(parsed))
    else:
        for match in _SERIAL_TOKEN.finditer(text):
            candidate = int(match.group(1))
            if _valid_monitor_sn(candidate):
                found.add(candidate)
    return found


def _host_sort_key(host: str) -> tuple[int, int, int, int]:
    return tuple(int(part) for part in host.split("."))  # type: ignore[return-value]


def protocol_from_firmware(firmware: str | None) -> str | None:
    if not firmware:
        return None
    match = _FIRMWARE_PROTOCOL_TOKEN.search(firmware)
    return match.group(1).lower() if match else None


def _merge_device(target: DiscoveryDevice, incoming: DiscoveryDevice) -> None:
    target.serial_candidates.update(incoming.serial_candidates)
    target.replies += incoming.replies
    target.sources.update(incoming.sources)
    target.tcp_8899_open = target.tcp_8899_open or incoming.tcp_8899_open
    target.http_open = target.http_open or incoming.http_open
    target.firmware_version = target.firmware_version or incoming.firmware_version
    target.protocol_hint = target.protocol_hint or incoming.protocol_hint


def discover_udp_targets(
    targets: Iterable[str],
    *,
    port: int = DEFAULT_DISCOVERY_PORT,
    timeout: float = DEFAULT_DISCOVERY_TIMEOUT,
) -> list[DiscoveryDevice]:
    """Collect every logger answering the known read-only UDP probes."""
    devices: dict[str, DiscoveryDevice] = {}
    destinations = tuple(dict.fromkeys(targets))
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    try:
        sock.bind(("", port))
        for attempt in range(2):
            for target in destinations:
                for message in DISCOVERY_MESSAGES:
                    try:
                        sock.sendto(message, (target, port))
                    except OSError:
                        continue
            if attempt == 0:
                time.sleep(0.12)
        deadline = time.monotonic() + timeout
        while (remaining := deadline - time.monotonic()) > 0:
            sock.settimeout(remaining)
            try:
                payload, (source, _source_port) = sock.recvfrom(4096)
            except socket.timeout:
                break
            if payload in DISCOVERY_MESSAGES:
                continue
            device = devices.setdefault(source, DiscoveryDevice(host=source))
            device.replies += 1
            device.sources.add("udp48899")
            device.serial_candidates.update(serial_candidates_from_payload(payload))
    except OSError:
        return []
    finally:
        sock.close()
    return sorted(devices.values(), key=lambda item: _host_sort_key(item.host))


def discover_devices(
    *, port: int = DEFAULT_DISCOVERY_PORT, timeout: float = DEFAULT_DISCOVERY_TIMEOUT
) -> list[DiscoveryDevice]:
    """Backward-compatible global-broadcast UDP discovery helper."""
    return discover_udp_targets(("255.255.255.255",), port=port, timeout=timeout)


def _parse_scan_network(value: str) -> IPv4Network:
    network = ip_network(value.strip(), strict=False)
    if not isinstance(network, IPv4Network):
        raise ValueError("An IPv4 network is required")
    if network.prefixlen < MIN_SCAN_PREFIX:
        raise ValueError("Discovery network must be /24 or smaller")
    return network


def _network_around_host(host: str) -> IPv4Network:
    return ip_network(f"{IPv4Address(host)}/{MIN_SCAN_PREFIX}", strict=False)


def local_ipv4_networks() -> set[IPv4Network]:
    """Infer local private /24 networks without shell commands or packages."""
    addresses: set[str] = set()
    try:
        for item in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            addresses.add(item[4][0])
    except OSError:
        pass

    route_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # UDP connect selects a route but sends no application payload.
        route_socket.connect(("192.0.2.1", 9))
        addresses.add(route_socket.getsockname()[0])
    except OSError:
        pass
    finally:
        route_socket.close()

    networks: set[IPv4Network] = set()
    for value in addresses:
        try:
            address = IPv4Address(value)
        except ValueError:
            continue
        if (
            not address.is_private
            or address.is_loopback
            or address.is_link_local
            or address.is_multicast
            or address.is_unspecified
        ):
            continue
        networks.add(_network_around_host(str(address)))
    return networks


def _tcp_port_open(host: str, port: int, timeout: float) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def scan_tcp_network(
    network: IPv4Network,
    port: int,
    *,
    timeout: float = DEFAULT_TCP_SCAN_TIMEOUT,
) -> list[str]:
    """Find hosts accepting one TCP port without sending application data."""
    hosts = [str(host) for host in network.hosts()]
    if not hosts:
        return []
    found: list[str] = []
    workers = min(DEFAULT_DISCOVERY_CONCURRENCY, len(hosts))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(_tcp_port_open, host, port, timeout): host for host in hosts}
        for future in as_completed(futures):
            host = futures[future]
            try:
                if future.result():
                    found.append(host)
            except OSError:
                pass
    return sorted(found, key=_host_sort_key)


def _http_document(
    host: str, path: str, timeout: float, authenticated: bool
) -> str | None:
    connection = http.client.HTTPConnection(host, 80, timeout=timeout)
    headers = {
        "User-Agent": "TSUN-Local-Dump-Discovery",
        "Connection": "close",
    }
    if authenticated:
        headers["Authorization"] = f"Basic {LOGGER_WEB_AUTH}"
    try:
        connection.request("GET", path, headers=headers)
        response = connection.getresponse()
        if response.status != 200:
            response.read()
            return None
        body = response.read(MAX_HTTP_PAGE_SIZE + 1)
        if len(body) > MAX_HTTP_PAGE_SIZE:
            return None
        return body.decode("utf-8", errors="replace")
    except (OSError, http.client.HTTPException):
        return None
    finally:
        connection.close()


def _first_web_match(patterns: tuple[re.Pattern[str], ...], document: str) -> str | None:
    for pattern in patterns:
        if match := pattern.search(document):
            value = match.group(1).strip()
            if value:
                return value
    return None


def _logger_web_metadata(document: str) -> dict[str, Any]:
    """Extract non-identifying logger metadata plus a 3-character inverter prefix."""
    firmware: str | None = None
    for pattern in _FIRMWARE_PATTERNS:
        if match := pattern.search(document):
            firmware = match.group(1)
            break

    inverter_serial = _first_web_match(_INVERTER_SERIAL_PATTERNS, document)
    raw_profile = _first_web_match(_RAW_PROFILE_PATTERNS, document)
    wifi_raw = _first_web_match(_WIFI_SIGNAL_PATTERNS, document)
    wifi_signal: int | None = None
    if wifi_raw is not None:
        candidate = int(wifi_raw)
        if -100 <= candidate <= 100:
            wifi_signal = candidate

    mac_match = _MAC_TOKEN.search(document)
    mac_oui = None
    if mac_match:
        mac_oui = ":".join(part.upper() for part in mac_match.groups()[:3])

    return {
        "logger_firmware_version": firmware,
        "logger_wifi_signal": wifi_signal,
        "logger_raw_profile": raw_profile,
        "logger_mac_oui": mac_oui,
        "inverter_serial_prefix": (inverter_serial[:3] if inverter_serial else None),
    }


def anonymize_web_document(document: str) -> str:
    """Return a research-useful web snapshot with device/user identifiers removed."""
    sanitized = document.replace("\r\n", "\n").replace("\r", "\n")

    inverter_serial = _first_web_match(_INVERTER_SERIAL_PATTERNS, document)
    if inverter_serial:
        replacement = f"{inverter_serial[:3]}<REDACTED>"
        sanitized = sanitized.replace(inverter_serial, replacement)

    # Remove any discovered Monitor/logger SN everywhere it appears, then also
    # scrub standalone 8-10 digit candidates to protect alternate firmware pages.
    logger_serials: set[str] = set()
    for pattern in _LOGGER_SN_PATTERNS:
        logger_serials.update(match.group(1) for match in pattern.finditer(document))
    for value in logger_serials:
        sanitized = sanitized.replace(value, "<LOGGER_SN>")
    sanitized = _SERIAL_TOKEN.sub("<LOGGER_SN>", sanitized)

    # Preserve only the MAC OUI (first three octets), never the complete address.
    def _mac_replacement(match: re.Match[str]) -> str:
        oui = ":".join(part.upper() for part in match.groups()[:3])
        return f"{oui}:XX:XX:XX"

    sanitized = _MAC_TOKEN.sub(_mac_replacement, sanitized)
    sanitized = _IPV4_TOKEN.sub("<IP>", sanitized)
    sanitized = _EMAIL_TOKEN.sub("<EMAIL>", sanitized)

    # Collect sensitive values first so duplicate visible copies are also removed.
    sensitive_values = {
        match.group("value")
        for pattern in (_SENSITIVE_ASSIGNMENT, _SENSITIVE_HTML_NAME_VALUE)
        for match in pattern.finditer(document)
        if match.group("value")
    }
    for value in sorted(sensitive_values, key=len, reverse=True):
        sanitized = sanitized.replace(value, "<REDACTED>")

    return sanitized


def capture_logger_web_pages(host: str, timeout: float) -> dict[str, Any]:
    """Capture known local logger pages as anonymized, read-only research evidence."""
    pages: list[dict[str, Any]] = []
    summary: dict[str, Any] = {
        "logger_firmware_version": None,
        "logger_wifi_signal": None,
        "logger_raw_profile": None,
        "logger_mac_oui": None,
        "inverter_serial_prefix": None,
    }

    for path in LOGGER_WEB_CAPTURE_PATHS:
        seen_hashes: set[str] = set()
        for authenticated in (False, True):
            document = _http_document(host, path, timeout, authenticated)
            if document is None:
                continue

            metadata = _logger_web_metadata(document)
            for key, value in metadata.items():
                if summary[key] is None and value is not None:
                    summary[key] = value

            sanitized = anonymize_web_document(document)
            digest = hashlib.sha256(sanitized.encode("utf-8")).hexdigest()
            if digest in seen_hashes:
                continue
            seen_hashes.add(digest)
            pages.append(
                {
                    "path": path,
                    "authenticated": authenticated,
                    "content_sha256": digest,
                    "content": sanitized,
                }
            )

    return {
        "attempted": True,
        "pages_found": len(pages),
        "summary": summary,
        "pages": pages,
        "privacy": {
            "raw_html_stored": False,
            "anonymized_html_stored": True,
            "logger_sn_stored": False,
            "host_ip_stored": False,
            "full_inverter_serial_stored": False,
            "inverter_serial_prefix_characters": 3,
            "full_mac_stored": False,
            "mac_oui_stored": True,
            "wifi_credentials_stored": False,
        },
    }


def _web_identity_from_document(
    document: str,
) -> tuple[set[int], str | None, str | None, bool]:
    serials: set[int] = set()
    for pattern in _LOGGER_SN_PATTERNS:
        for match in pattern.finditer(document):
            candidate = int(match.group(1))
            if _valid_monitor_sn(candidate):
                serials.add(candidate)

    firmware: str | None = None
    for pattern in _FIRMWARE_PATTERNS:
        match = pattern.search(document)
        if match:
            firmware = match.group(1)
            break
    hint = protocol_from_firmware(firmware)
    recognized = bool(
        serials
        or hint
        or re.search(
            r"\b(?:webdata|cover)[_-](?:ver|mid|sn)\b",
            document,
            re.IGNORECASE,
        )
    )
    return serials, firmware, hint, recognized


def probe_logger_web(
    host: str,
    timeout: float,
    *,
    allow_authenticated: bool = False,
) -> DiscoveryDevice | None:
    """Identify a TSUN logger from local web pages without credential spraying."""
    aggregate = DiscoveryDevice(host=host, http_open=True)
    recognized = False
    for path in LOGGER_STATUS_PATHS:
        document = _http_document(host, path, timeout, False)
        if document is not None:
            serials, firmware, hint, is_tsun = _web_identity_from_document(document)
            aggregate.serial_candidates.update(serials)
            aggregate.firmware_version = aggregate.firmware_version or firmware
            aggregate.protocol_hint = aggregate.protocol_hint or hint
            recognized = recognized or is_tsun

        # Only send the legacy admin:admin credential to an explicitly targeted
        # host, or after the unauthenticated page has already identified TSUN.
        if (allow_authenticated or recognized) and not (
            aggregate.serial_candidates and aggregate.protocol_hint
        ):
            document = _http_document(host, path, timeout, True)
            if document is not None:
                serials, firmware, hint, is_tsun = _web_identity_from_document(document)
                aggregate.serial_candidates.update(serials)
                aggregate.firmware_version = aggregate.firmware_version or firmware
                aggregate.protocol_hint = aggregate.protocol_hint or hint
                recognized = recognized or is_tsun

        if aggregate.serial_candidates and aggregate.protocol_hint:
            break
    if not recognized:
        return None
    aggregate.sources.add("http80")
    return aggregate


def probe_ap_identity(host: str, port: int, timeout: float) -> int | None:
    """Retrieve logger SN from AP response identity using read-only SN=0 probes."""
    probes = (
        (build_1511_request(0xA1, 0x01, 0x0BB8, 0x0BD0), 0),
        (build_modbus_request(0x3009, 0x301E), 0),
        (build_modbus_request(0x1100, 0x1100), 0x1097),
    )
    for payload, sensor_list in probes:
        try:
            request = build_ap_frame(0, payload, sensor_list=sensor_list)
            with socket.create_connection((host, port), timeout=timeout) as sock:
                sock.settimeout(timeout)
                sock.sendall(request)
                frame = read_ap_frame(sock)
            return extract_ap_logger_sn(frame)
        except (OSError, TsunProtocolError, ValueError):
            continue
    return None


def _parallel_map(
    hosts: Iterable[str], function: Callable[[str], Any], *, workers: int = 24
) -> dict[str, Any]:
    host_list = list(dict.fromkeys(hosts))
    if not host_list:
        return {}
    result: dict[str, Any] = {}
    with ThreadPoolExecutor(max_workers=min(workers, len(host_list))) as executor:
        futures = {executor.submit(function, host): host for host in host_list}
        for future in as_completed(futures):
            host = futures[future]
            try:
                result[host] = future.result()
            except Exception:
                result[host] = None
    return result


def discover_candidates(
    args: argparse.Namespace,
) -> tuple[list[DiscoveryDevice], dict[str, int]]:
    """Combine every safe discovery path into one candidate set."""
    explicit_networks = {_parse_scan_network(value) for value in (args.network or [])}
    networks = set(explicit_networks)
    networks.update(local_ipv4_networks())

    udp_targets = {"255.255.255.255"}
    udp_targets.update(str(network.broadcast_address) for network in networks)
    initial_udp = discover_udp_targets(udp_targets, timeout=args.discovery_timeout)

    devices: dict[str, DiscoveryDevice] = {}
    for incoming in initial_udp:
        current = devices.setdefault(incoming.host, DiscoveryDevice(host=incoming.host))
        _merge_device(current, incoming)
        networks.add(_network_around_host(incoming.host))

    tcp_hosts: set[str] = set()
    http_hosts: set[str] = set()
    for network in sorted(networks, key=lambda item: (int(item.network_address), item.prefixlen)):
        print(f"Network discovery: scanning {network} on TCP {args.port} and HTTP 80...")
        tcp_hosts.update(
            scan_tcp_network(network, args.port, timeout=args.tcp_scan_timeout)
        )
        http_hosts.update(
            scan_tcp_network(network, 80, timeout=args.http_scan_timeout)
        )

    candidate_hosts = sorted(tcp_hosts | http_hosts, key=_host_sort_key)
    if candidate_hosts:
        directed = discover_udp_targets(
            candidate_hosts,
            timeout=min(args.discovery_timeout, 2.5),
        )
        for incoming in directed:
            current = devices.setdefault(incoming.host, DiscoveryDevice(host=incoming.host))
            _merge_device(current, incoming)

    web_results = _parallel_map(
        sorted(http_hosts, key=_host_sort_key),
        lambda host: probe_logger_web(host, args.http_page_timeout),
    )
    for host, incoming in web_results.items():
        if incoming is None:
            continue
        current = devices.setdefault(host, DiscoveryDevice(host=host))
        _merge_device(current, incoming)

    ap_results = _parallel_map(
        sorted(tcp_hosts, key=_host_sort_key),
        lambda host: probe_ap_identity(host, args.port, min(args.timeout, 3.0)),
    )
    for host, logger_sn in ap_results.items():
        if logger_sn is None:
            continue
        current = devices.setdefault(host, DiscoveryDevice(host=host))
        current.serial_candidates.add(int(logger_sn))
        current.sources.add("ap_identity")

    # Keep 8899 candidates even when a busy logger missed all identity probes.
    # They are still verified later by a real read-only protocol transaction.
    for host in tcp_hosts:
        current = devices.setdefault(host, DiscoveryDevice(host=host))
        current.tcp_8899_open = True
        current.sources.add("tcp8899")
    for host in http_hosts:
        if host in devices:
            devices[host].http_open = True

    return (
        sorted(devices.values(), key=lambda item: _host_sort_key(item.host)),
        {
            "udp_devices": len(initial_udp),
            "tcp_candidates": len(tcp_hosts),
            "http_candidates": len(http_hosts),
            "identified_candidates": len(devices),
            "networks_scanned": len(networks),
        },
    )


def resolve_single_host_identity(args: argparse.Namespace, host: str) -> DiscoveryDevice:
    """Resolve one explicit host through UDP, web and AP identity paths."""
    device = DiscoveryDevice(host=host)
    for incoming in discover_udp_targets(
        (host,), timeout=min(args.discovery_timeout, 2.5)
    ):
        if incoming.host == host:
            _merge_device(device, incoming)

    web = probe_logger_web(host, args.http_page_timeout, allow_authenticated=True)
    if web is not None:
        _merge_device(device, web)

    if _tcp_port_open(host, args.port, args.tcp_scan_timeout):
        device.tcp_8899_open = True
        device.sources.add("tcp8899")
        logger_sn = probe_ap_identity(host, args.port, min(args.timeout, 3.0))
        if logger_sn is not None:
            device.serial_candidates.add(logger_sn)
            device.sources.add("ap_identity")
    return device


def _prompt_monitor_sn(
    prompt: str = "Monitor SN: ", *, allow_skip: bool = False
) -> int | None:
    """Read a Monitor SN using ordinary stdin for reliable Windows terminals."""
    while True:
        answer = input(prompt).strip()
        if allow_skip and not answer:
            return None
        try:
            number = int(answer)
        except ValueError:
            print(
                "Monitor SN must be numeric."
                + (" Press Enter to skip." if allow_skip else "")
            )
            continue
        if _valid_monitor_sn(number):
            return number
        print("Monitor SN must fit the four-byte logger field.")


def resolve_targets(
    args: argparse.Namespace,
) -> tuple[list[tuple[str, int, dict[str, Any]]], dict[str, int]]:
    """Resolve all candidates; --host deliberately restricts to one."""
    summary = {"devices_found": 0, "targets_resolved": 0, "targets_skipped": 0}

    if args.host is not None:
        host = args.host.strip()
        if not host:
            raise ValueError("A logger IP address is required")
        print("Identifying the supplied logger (UDP + TCP + HTTP + AP identity)...")
        device = resolve_single_host_identity(args, host)
        monitor_sn = args.serial
        discovered_sn = False
        if monitor_sn is None and len(device.serial_candidates) == 1:
            monitor_sn = next(iter(device.serial_candidates))
            discovered_sn = True
        if monitor_sn is None:
            print("Monitor SN could not be resolved automatically.")
            monitor_sn = _prompt_monitor_sn()
        assert monitor_sn is not None
        summary["devices_found"] = 1
        summary["targets_resolved"] = 1
        report = {
            "attempted": True,
            "devices_found": 1,
            "host_discovered": bool(device.sources),
            "monitor_sn_discovered": discovered_sn,
            "target_index": 1,
            "multi_device_scan": False,
            "sources": sorted(device.sources),
            "firmware_version": device.firmware_version,
            "protocol_hint": device.protocol_hint,
        }
        return [(host, monitor_sn, report)], summary

    print("Searching for TSUN loggers (UDP + TCP 8899 + HTTP + AP identity)...")
    devices, stats = discover_candidates(args)
    summary["devices_found"] = len(devices)
    print(
        "Discovery results: "
        f"UDP={stats['udp_devices']}, TCP8899={stats['tcp_candidates']}, "
        f"HTTP={stats['http_candidates']}, identified={stats['identified_candidates']}, "
        f"networks={stats['networks_scanned']}"
    )

    if not devices:
        host = input("Logger IP address: ").strip()
        if not host:
            raise ValueError("A logger IP address is required")
        device = resolve_single_host_identity(args, host)
        monitor_sn = args.serial
        discovered_sn = False
        if monitor_sn is None and len(device.serial_candidates) == 1:
            monitor_sn = next(iter(device.serial_candidates))
            discovered_sn = True
        if monitor_sn is None:
            print("Monitor SN could not be resolved automatically.")
            monitor_sn = _prompt_monitor_sn()
        assert monitor_sn is not None
        summary["devices_found"] = 1
        summary["targets_resolved"] = 1
        report = {
            "attempted": True,
            "devices_found": 1,
            "host_discovered": bool(device.sources),
            "monitor_sn_discovered": discovered_sn,
            "target_index": 1,
            "multi_device_scan": False,
            "sources": sorted(device.sources),
            "firmware_version": device.firmware_version,
            "protocol_hint": device.protocol_hint,
        }
        return [(host, monitor_sn, report)], summary

    if args.serial is not None and len(devices) > 1:
        raise ValueError(
            "--serial/--monitor-sn without --host is ambiguous when several loggers "
            "are found; omit it or add --host"
        )

    print(f"{len(devices)} candidate logger(s) found. Every candidate will be validated.")
    targets: list[tuple[str, int, dict[str, Any]]] = []
    multi = len(devices) > 1
    for index, device in enumerate(devices, 1):
        sources = ", ".join(sorted(device.sources)) or "network scan"
        hint = f", firmware hint={device.protocol_hint}" if device.protocol_hint else ""
        print(f"Logger {index}/{len(devices)}: {device.host} [{sources}{hint}]")

        monitor_sn: int | None = None
        discovered_sn = False
        if args.serial is not None and len(devices) == 1:
            monitor_sn = args.serial
        elif len(device.serial_candidates) == 1:
            monitor_sn = next(iter(device.serial_candidates))
            discovered_sn = True
        else:
            state = "ambiguous" if device.serial_candidates else "missing"
            print(f"  Monitor SN {state}.")
            prompt = (
                f"Monitor SN for logger {index}/{len(devices)} at {device.host}"
                + (" (Enter to skip): " if multi else ": ")
            )
            monitor_sn = _prompt_monitor_sn(prompt, allow_skip=multi)
            if monitor_sn is None:
                print(f"Skipping logger {index}/{len(devices)}; no Monitor SN supplied.")
                summary["targets_skipped"] += 1
                continue

        report = {
            "attempted": True,
            "devices_found": len(devices),
            "host_discovered": True,
            "monitor_sn_discovered": discovered_sn,
            "target_index": index,
            "multi_device_scan": multi,
            "sources": sorted(device.sources),
            "firmware_version": device.firmware_version,
            "protocol_hint": device.protocol_hint,
        }
        targets.append((device.host, monitor_sn, report))

    if not targets:
        raise ValueError("No discovered logger has a usable Monitor SN")
    summary["targets_resolved"] = len(targets)
    return targets, summary


# ---------------------------------------------------------------------------
# Capture plans / protocol detection
# ---------------------------------------------------------------------------

def split_modbus_range(start: int, end: int) -> list[tuple[int, int]]:
    blocks: list[tuple[int, int]] = []
    cursor = start
    while cursor <= end:
        chunk_end = min(end, cursor + MAX_MODBUS_REGISTERS_PER_READ - 1)
        blocks.append((cursor, chunk_end))
        cursor = chunk_end + 1
    return blocks


def capture_plans(protocol: str, full: bool) -> tuple[list[tuple], list[tuple]]:
    if protocol == "02b0":
        dynamic = split_modbus_range(0x3000, 0x302F)
        supplemental = (
            split_modbus_range(0x2000, 0x204F)
            if full
            else [(0x2007, 0x2007), *split_modbus_range(0x2014, 0x202C)]
        )
        return dynamic, supplemental

    if protocol == "1097":
        dynamic = [
            *split_modbus_range(0x1100, 0x110F),
            *split_modbus_range(0x1200, 0x121F),
            *split_modbus_range(0x1300, 0x132F),
        ]
        supplemental = (
            [
                *split_modbus_range(0x1008, 0x100F),
                *split_modbus_range(0x1400, 0x143F),
            ]
            if full
            else [
                *split_modbus_range(0x1008, 0x100F),
                (0x1400, 0x1400),
                (0x1423, 0x1423),
                (0x1437, 0x1437),
            ]
        )
        return dynamic, supplemental

    if protocol == "1511":
        dynamic = [
            (0xA1, 0x01, 0x0BB8, 0x0BD7),
            (0xA2, 0x02, 0x0CE4, 0x0CE7),
            (0xA3, 0x03, 0x0E10, 0x0E2D),
            (0xA4, 0x04, 0x0ED8, 0x0EF5),
        ]
        return dynamic, [(0xA1, 0x21, 0x07D0, 0x082F)]

    raise ValueError(f"Unsupported protocol: {protocol}")


def _probe_protocol(
    protocol: str, host: str, port: int, sn: int, timeout: float
) -> None:
    if protocol == "1511":
        read_1511_block(
            host, port, sn, 0xA1, 0x01, 0x0BB8, 0x0BB8, timeout=timeout
        )
    elif protocol == "02b0":
        read_modbus_block(
            host,
            port,
            sn,
            0x3000,
            0x3000,
            sensor_list=0,
            timeout=timeout,
        )
    elif protocol == "1097":
        read_modbus_block(
            host,
            port,
            sn,
            0x1100,
            0x1100,
            sensor_list=0x1097,
            timeout=timeout,
        )
    else:
        raise ValueError(f"Unsupported protocol: {protocol}")


def detect_protocol(
    requested: str,
    host: str,
    port: int,
    sn: int,
    timeout: float,
    hint: str | None = None,
) -> tuple[str, list[dict[str, Any]]]:
    attempts: list[dict[str, Any]] = []
    if requested != "auto":
        candidates = (requested,)
    elif hint in SUPPORTED_PROTOCOLS:
        candidates = (hint, *(item for item in SUPPORTED_PROTOCOLS if item != hint))
    else:
        candidates = SUPPORTED_PROTOCOLS

    last_error: Exception | None = None
    for protocol in candidates:
        failures: list[dict[str, Any]] = []
        for attempt in range(1, PROTOCOL_PROBE_RETRIES + 1):
            try:
                _probe_protocol(protocol, host, port, sn, timeout)
            except Exception as err:
                last_error = err
                failures.append(
                    {"attempt": attempt, "error": safe_error_details(err)}
                )
                if attempt < PROTOCOL_PROBE_RETRIES:
                    time.sleep(PROTOCOL_RETRY_DELAY)
                continue
            attempts.append(
                {"protocol": protocol, "result": "success", "attempt": attempt}
            )
            return protocol, attempts
        attempts.append(
            {"protocol": protocol, "result": "failure", "attempts": failures}
        )

    raise RuntimeError(
        "No supported TSUN local protocol detected after "
        f"{PROTOCOL_PROBE_RETRIES} attempts per protocol"
    ) from last_error


def register_key(protocol: str, block: tuple, address: int) -> str:
    if protocol == "1511":
        tag, function, _start, _end = block
        return f"{tag:02X}/{function:02X}:0x{address:04X}"
    return f"0x{address:04X}"


def _block_descriptor(protocol: str, block: tuple) -> dict[str, Any]:
    if protocol == "1511":
        tag, function, start, end = block
        return {
            "address_tag": f"0x{tag:02X}",
            "function": f"0x{function:02X}",
            "start": f"0x{start:04X}",
            "end": f"0x{end:04X}",
        }
    start, end = block
    return {
        "function": "0x03",
        "start": f"0x{start:04X}",
        "end": f"0x{end:04X}",
    }


def read_plan(
    protocol: str,
    host: str,
    port: int,
    sn: int,
    plan: Iterable[tuple],
    timeout: float,
) -> tuple[dict[str, int], list[dict[str, Any]], list[dict[str, Any]]]:
    registers: dict[str, int] = {}
    blocks: list[dict[str, Any]] = []
    trace: list[dict[str, Any]] = []

    for block in plan:
        record = _block_descriptor(protocol, block)
        try:
            if protocol == "1511":
                tag, function, start, end = block
                values, request_payload, response_payload = read_1511_block(
                    host,
                    port,
                    sn,
                    tag,
                    function,
                    start,
                    end,
                    timeout=timeout,
                )
            else:
                start, end = block
                sensor_list = 0x1097 if protocol == "1097" else 0
                values, request_payload, response_payload = read_modbus_block(
                    host,
                    port,
                    sn,
                    start,
                    end,
                    sensor_list=sensor_list,
                    timeout=timeout,
                )
        except Exception as err:
            record["result"] = "failure"
            record["error"] = safe_error_details(err)
            trace.append({**record, "stage": "failure"})
        else:
            record["result"] = "success"
            record["register_count"] = len(values)
            record["registers"] = [
                {
                    "key": register_key(protocol, block, address),
                    "address": address,
                    "address_hex": f"0x{address:04X}",
                    "raw_decimal": value,
                    "raw_hex": f"0x{value:04X}",
                }
                for address, value in sorted(values.items())
            ]
            for address, value in values.items():
                registers[register_key(protocol, block, address)] = value
            trace.append(
                {
                    **record,
                    "stage": "complete",
                    "request_payload": request_payload.hex(" ").upper(),
                    "response_payload": response_payload.hex(" ").upper(),
                }
            )
        blocks.append(record)

    return registers, blocks, trace


# ---------------------------------------------------------------------------
# Analysis / established decoding
# ---------------------------------------------------------------------------

def analyze_snapshots(snapshots: list[dict[str, Any]]) -> dict[str, list[str]]:
    result = {
        "changing_registers": [],
        "stable_registers": [],
        "zero_registers": [],
        "ffff_registers": [],
        "incomplete_registers": [],
    }
    if not snapshots:
        return result

    maps = [snapshot.get("registers", {}) for snapshot in snapshots]
    all_keys = sorted(set().union(*(mapping.keys() for mapping in maps)))
    for key in all_keys:
        if not all(key in mapping for mapping in maps):
            result["incomplete_registers"].append(key)
            continue
        values = [mapping[key] for mapping in maps]
        if len(set(values)) > 1:
            result["changing_registers"].append(key)
        elif values[0] == 0:
            result["zero_registers"].append(key)
        elif values[0] == 0xFFFF:
            result["ffff_registers"].append(key)
        else:
            result["stable_registers"].append(key)
    return result


def _address_map(raw: dict[str, int]) -> dict[int, int]:
    result: dict[int, int] = {}
    for key, value in raw.items():
        try:
            address = int(key.rsplit("0x", 1)[1], 16)
        except (IndexError, ValueError):
            continue
        result[address] = value
    return result


def _u32(registers: dict[int, int], high: int) -> int | None:
    if high not in registers or high + 1 not in registers:
        return None
    return (registers[high] << 16) | registers[high + 1]


def firmware_version(value: int) -> str:
    raw = f"{value:04X}"
    return f"V{raw[0]}.{raw[1]}.{raw[2:]}"


def _detect_pv_count(protocol: str, r: dict[int, int]) -> int:
    if protocol == "1511":
        bases = (0x0E10, 0x0E17, 0x0E1E, 0x0ED8, 0x0EDF, 0x0EE6)
        totals = (0x0E28, 0x0E2A, 0x0E2C, 0x0EF0, 0x0EF2, 0x0EF4)
        detected = 1
        for number, (base, total) in enumerate(zip(bases, totals), 1):
            if any(
                0 < r.get(address, 0) < 0xFFFF
                for address in (
                    base,
                    base + 1,
                    base + 2,
                    base + 5,
                    total,
                    total + 1,
                )
            ):
                detected = number
        return detected

    if protocol == "1097":
        detected = 0
        for number in range(1, 7):
            base = 0x1302 + (number - 1) * 7
            if any(
                0 < r.get(address, 0) < 0xFFFF
                for address in range(base, base + 7)
            ):
                detected = number
        return max(detected, 1)

    detected = 1
    for number in range(1, 5):
        base = 0x3010 + (number - 1) * 3
        energy = 0x301F + (number - 1) * 3
        if any(
            0 < r.get(address, 0) < 0xFFFF
            for address in (base, base + 1, base + 2, energy)
        ):
            detected = number
    return detected


def decode_known(protocol: str, raw: dict[str, int]) -> dict[str, Any]:
    """Decode established fields only; research candidates stay raw."""
    r = _address_map(raw)
    data: dict[str, Any] = {}
    pv_count = _detect_pv_count(protocol, r)

    if protocol == "02b0":
        mapping = {
            "inverter_status_raw": (0x3000, 1),
            "ac_voltage": (0x3009, 0.1),
            "ac_current": (0x300A, 0.01),
            "ac_frequency": (0x300B, 0.01),
            "inverter_temperature": (0x300C, 1),
            "rated_power": (0x300E, 1),
            "ac_power": (0x300F, 0.1),
            "ac_energy_today": (0x301C, 0.01),
            "max_designed_power": (0x2007, 1),
        }
        for key, (address, scale) in mapping.items():
            if address not in r:
                continue
            value: float | int = r[address] * scale
            if key == "inverter_temperature":
                value = r[address] - 40
            data[key] = round(value, 3) if isinstance(value, float) else value
        if 0x202C in r:
            data["output_coefficient"] = round(r[0x202C] * 100 / 1024, 2)
        for number in range(1, pv_count + 1):
            base = 0x3010 + (number - 1) * 3
            if base + 2 in r:
                data[f"pv{number}_voltage"] = round(r[base] * 0.1, 2)
                data[f"pv{number}_current"] = round(r[base + 1] * 0.01, 2)
                data[f"pv{number}_power"] = round(r[base + 2] * 0.1, 2)
        data["note_02b0_total_energy"] = (
            "Total-energy width is intentionally left raw so device variants "
            "can be validated independently."
        )

    elif protocol == "1097":
        if 0x100A in r:
            data["protocol_version"] = firmware_version(r[0x100A])
        if 0x100C in r:
            data["inverter_version"] = firmware_version(r[0x100C])
        mapping = {
            "inverter_status_raw": (0x1100, 1),
            "ac_voltage": (0x1200, 0.1),
            "ac_current": (0x1201, 0.01),
            "ac_power": (0x1202, 0.1),
            "ac_frequency": (0x1209, 0.01),
            "rated_power": (0x1210, 1),
            "ac_energy_today": (0x1212, 0.01),
        }
        for key, (address, scale) in mapping.items():
            if address in r:
                data[key] = round(r[address] * scale, 3)
        total = _u32(r, 0x1213)
        if total is not None:
            data["ac_energy_total"] = round(total * 0.01, 2)
        if 0x1216 in r:
            data["insulation_impedance_rx"] = round(r[0x1216] * 0.01, 2)
        if 0x1217 in r:
            data["insulation_impedance_ry"] = round(r[0x1217] * 0.01, 2)
        if 0x1218 in r:
            data["inverter_temperature"] = r[0x1218] - 40
        if 0x1400 in r:
            data["country_profile_raw"] = r[0x1400]
        if 0x1423 in r:
            data["output_coefficient"] = round(r[0x1423] * 100 / 1024, 2)
        if 0x1437 in r:
            data["max_designed_power"] = r[0x1437]
        for number in range(1, pv_count + 1):
            base = 0x1302 + (number - 1) * 7
            if base + 2 in r:
                data[f"pv{number}_voltage"] = round(r[base] * 0.1, 2)
                data[f"pv{number}_current"] = round(r[base + 1] * 0.01, 2)
                data[f"pv{number}_power"] = round(r[base + 2] * 0.1, 2)

    else:
        mapping = {
            "inverter_status_raw": (0x0BB8, 1),
            "ac_voltage": (0x0BC4, 0.1),
            "ac_current": (0x0BC5, 0.01),
            "ac_frequency": (0x0BC7, 0.01),
            "inverter_temperature": (0x0BC9, 1),
            "rated_power": (0x0BCC, 1),
            "ac_power": (0x0BCD, 0.1),
            "ac_energy_today": (0x0BCE, 0.01),
        }
        for key, (address, scale) in mapping.items():
            if address not in r:
                continue
            value = r[address] * scale
            if key == "inverter_temperature":
                value = r[address] - 40
            data[key] = round(value, 3) if isinstance(value, float) else value
        total = _u32(r, 0x0BCF)
        if total is not None:
            data["ac_energy_total"] = round(total * 0.01, 2)
        if 0x0BD4 in r:
            data["ambient_temperature"] = r[0x0BD4] - 40
        for key, address in {
            "dsp_firmware_version": 0x0BC0,
            "qcpu1_firmware_version": 0x0E26,
            "qcpu2_firmware_version": 0x0EEE,
        }.items():
            if address in r:
                data[key] = firmware_version(r[address])
        if 0x07D0 in r:
            data["country_profile_raw"] = r[0x07D0]
        if 0x07FA in r:
            data["max_designed_power"] = r[0x07FA]
        bases = (0x0E10, 0x0E17, 0x0E1E, 0x0ED8, 0x0EDF, 0x0EE6)
        for number, base in enumerate(bases[:pv_count], 1):
            if base + 2 in r:
                data[f"pv{number}_voltage"] = round(r[base] * 0.1, 2)
                data[f"pv{number}_current"] = round(r[base + 1] * 0.01, 2)
                data[f"pv{number}_power"] = round(r[base + 2] * 0.1, 2)

    data["detected_pv_count"] = pv_count
    return data


# ---------------------------------------------------------------------------
# Dump document / comparison / filenames
# ---------------------------------------------------------------------------

def _safe_filename_part(value: str) -> str:
    normalized = _SAFE_NAME.sub("-", value.lower()).strip("-._")
    return normalized or "unknown"


def default_output_path(
    model: str | None,
    protocol: str,
    timestamp: datetime,
    *,
    device_index: int | None = None,
) -> Path:
    stamp = timestamp.strftime("%Y%m%dT%H%M%SZ")
    device = f"device-{device_index:02d}_" if device_index is not None else ""
    return Path(
        f"tsun_{device}{_safe_filename_part(model or 'unknown')}_{protocol}_{stamp}.json"
    )


def output_path_for_target(
    requested: Path | None,
    model: str | None,
    protocol: str,
    timestamp: datetime,
    *,
    device_index: int,
    total_targets: int,
) -> Path:
    if requested is None:
        return default_output_path(
            model,
            protocol,
            timestamp,
            device_index=device_index if total_targets > 1 else None,
        )
    if total_targets == 1:
        return requested
    suffix = requested.suffix or ".json"
    stem = requested.stem if requested.suffix else requested.name
    return requested.parent / f"{stem}_device-{device_index:02d}{suffix}"


def _script_sha256() -> str | None:
    try:
        return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    except OSError:
        return None


def _flatten_raw_registers(registers: dict[str, int]) -> list[dict[str, Any]]:
    return [
        {"key": key, "raw_decimal": value, "raw_hex": f"0x{value:04X}"}
        for key, value in sorted(registers.items())
    ]


def capture(
    args: argparse.Namespace,
    host: str,
    sn: int,
    discovery: dict[str, Any],
) -> dict[str, Any]:
    protocol, detection_attempts = detect_protocol(
        args.protocol,
        host,
        args.port,
        sn,
        args.timeout,
        discovery.get("protocol_hint"),
    )
    print(f"Protocol detected: {protocol}")

    dynamic_plan, supplemental_plan = capture_plans(protocol, args.full)
    supplemental_registers, supplemental_blocks, supplemental_trace = read_plan(
        protocol,
        host,
        args.port,
        sn,
        supplemental_plan,
        args.timeout,
    )

    snapshots: list[dict[str, Any]] = []
    snapshot_blocks: list[dict[str, Any]] = []
    protocol_trace = list(supplemental_trace)
    for index in range(args.snapshots):
        registers, blocks, trace = read_plan(
            protocol,
            host,
            args.port,
            sn,
            dynamic_plan,
            args.timeout,
        )
        snapshots.append(
            {
                "index": index + 1,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "registers": registers,
            }
        )
        for block in blocks:
            block["snapshot"] = index + 1
            block["scope"] = "dynamic"
            snapshot_blocks.append(block)
        protocol_trace.extend(trace)
        if index + 1 < args.snapshots and args.interval:
            time.sleep(args.interval)

    latest = snapshots[-1]["registers"] if snapshots else {}
    merged = {**supplemental_registers, **latest}
    supplemental_blocks = [
        {**block, "snapshot": None, "scope": "supplemental"}
        for block in supplemental_blocks
    ]
    all_blocks = [*supplemental_blocks, *snapshot_blocks]
    successful = sum(block["result"] == "success" for block in all_blocks)
    failed = len(all_blocks) - successful
    created_at = datetime.now(timezone.utc)
    family = {
        "1511": "TITAN",
        "02b0": "GEN3 / GEN3 PLUS",
        "1097": "GEN3 / GEN3 PLUS (1097)",
    }[protocol]
    logger_web = capture_logger_web_pages(host, args.http_page_timeout)

    return {
        "format": DUMP_FORMAT,
        "schema_version": SCHEMA_VERSION,
        "metadata": {
            "timestamp_utc": created_at.isoformat(),
            "tool": "TSUN Local Hardware Validation Dump Tool",
            "tool_version": TOOL_VERSION,
            "tool_sha256": _script_sha256(),
            "tool_source": SOURCE_URL,
            "standalone": True,
            "python_required": ">=3.10",
            "read_only": True,
            "capture_mode": "full" if args.full else "standard",
            "detected_protocol": protocol,
            "model_family": family,
            "model_supplied_by_user": args.model,
            "pv_count": _detect_pv_count(protocol, _address_map(merged)),
            "port": args.port,
            "privacy": {
                "host_in_output": False,
                "logger_sn_in_output": False,
                "inverter_serial_in_output": False,
                "ap_envelope_in_output": False,
                "udp_discovery_payload_in_output": False,
                "logger_web_raw_html_in_output": False,
                "logger_web_anonymized_html_in_output": True,
                "inverter_serial_prefix_characters": 3,
            },
        },
        "logger_web": logger_web,
        "discovery": discovery,
        "protocol_detection": {
            "requested": args.protocol,
            "selected": protocol,
            "confidence": "direct successful protocol read",
            "attempts": detection_attempts,
        },
        "decoded_known_measurements": decode_known(protocol, merged),
        "capture_summary": {
            "snapshots": len(snapshots),
            "snapshot_interval_seconds": args.interval,
            "successful_block_reads": successful,
            "failed_block_reads": failed,
            "unique_raw_registers": len(merged),
        },
        "raw_registers": _flatten_raw_registers(merged),
        "snapshots": snapshots,
        "analysis": analyze_snapshots(snapshots),
        "blocks": all_blocks,
        "protocol_trace": protocol_trace,
    }


def _raw_map(document: dict[str, Any]) -> dict[str, int]:
    result: dict[str, int] = {}
    for item in document.get("raw_registers", []):
        if isinstance(item, dict) and "key" in item and "raw_decimal" in item:
            result[str(item["key"])] = int(item["raw_decimal"])
    return result


def compare_documents(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    before_map = _raw_map(before)
    after_map = _raw_map(after)
    common = sorted(before_map.keys() & after_map.keys())
    changed = [
        {
            "key": key,
            "before": before_map[key],
            "before_hex": f"0x{before_map[key]:04X}",
            "after": after_map[key],
            "after_hex": f"0x{after_map[key]:04X}",
        }
        for key in common
        if before_map[key] != after_map[key]
    ]
    return {
        "format": "tsun-local-dump-comparison",
        "schema_version": 1,
        "before_protocol": before.get("metadata", {}).get("detected_protocol"),
        "after_protocol": after.get("metadata", {}).get("detected_protocol"),
        "changed_registers": changed,
        "added_registers": sorted(after_map.keys() - before_map.keys()),
        "removed_registers": sorted(before_map.keys() - after_map.keys()),
        "unchanged_register_count": sum(
            before_map[key] == after_map[key] for key in common
        ),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _positive_port(value: str) -> int:
    port = int(value)
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("port must be between 1 and 65535")
    return port


def _positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("value must be at least 1")
    return number


def _monitor_sn_arg(value: str) -> int:
    try:
        number = int(value)
    except ValueError as err:
        raise argparse.ArgumentTypeError("Monitor SN must be numeric") from err
    if not _valid_monitor_sn(number):
        raise argparse.ArgumentTypeError(
            "Monitor SN must be between 1 and 4294967295"
        )
    return number


def _non_negative_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise argparse.ArgumentTypeError("value must be a finite number >= 0")
    return number


def _positive_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("value must be a finite number > 0")
    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Standalone, privacy-safe, strictly read-only TSUN hardware dump for "
            "1511, 02B0 and 1097. Discovery combines UDP, TCP 8899, HTTP and AP identity."
        )
    )
    parser.add_argument(
        "--host",
        help="logger IP address; when omitted, every discovered logger is captured",
    )
    parser.add_argument(
        "--serial",
        "--monitor-sn",
        dest="serial",
        type=_monitor_sn_arg,
        help=(
            "numeric Monitor SN for single-target use; --monitor-sn is an alias; "
            "normally auto-resolved"
        ),
    )
    parser.add_argument("--port", type=_positive_port, default=DEFAULT_PORT)
    parser.add_argument(
        "--protocol",
        choices=("auto", *SUPPORTED_PROTOCOLS),
        default="auto",
        help="force a protocol or detect automatically",
    )
    parser.add_argument("--model", help="exact physical model for metadata/file name")
    parser.add_argument(
        "--full",
        action="store_true",
        help="read additional known-safe research ranges",
    )
    parser.add_argument("--snapshots", type=_positive_int, default=DEFAULT_SNAPSHOTS)
    parser.add_argument(
        "--interval",
        type=_non_negative_float,
        default=DEFAULT_SNAPSHOT_INTERVAL,
    )
    parser.add_argument("--timeout", type=_positive_float, default=DEFAULT_TIMEOUT)
    parser.add_argument(
        "--discovery-timeout",
        type=_non_negative_float,
        default=DEFAULT_DISCOVERY_TIMEOUT,
    )
    parser.add_argument(
        "--tcp-scan-timeout",
        type=_positive_float,
        default=DEFAULT_TCP_SCAN_TIMEOUT,
        help="TCP 8899 connect timeout used by bounded discovery",
    )
    parser.add_argument(
        "--http-scan-timeout",
        type=_positive_float,
        default=DEFAULT_HTTP_SCAN_TIMEOUT,
        help="HTTP port-80 connect timeout used by bounded discovery",
    )
    parser.add_argument(
        "--http-page-timeout",
        type=_positive_float,
        default=DEFAULT_HTTP_PAGE_TIMEOUT,
        help="timeout for local logger status-page identity reads",
    )
    parser.add_argument(
        "--network",
        action="append",
        default=[],
        metavar="CIDR",
        help=(
            "additional IPv4 /24-or-smaller network to scan, e.g. "
            "10.89.10.0/24; may be repeated"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="output JSON path; multi-device scans add _device-NN automatically",
    )
    parser.add_argument(
        "--compare",
        nargs=2,
        metavar=("BEFORE_JSON", "AFTER_JSON"),
        help="compare two existing dump files without connecting to an inverter",
    )
    return parser


def _print_dump_summary(document: dict[str, Any], output: Path) -> None:
    summary = document["capture_summary"]
    privacy = document["metadata"]["privacy"]
    print("Dump completed.")
    print(f"Protocol : {document['metadata']['detected_protocol']}")
    print(
        f"Blocks   : {summary['successful_block_reads']} successful / "
        f"{summary['failed_block_reads']} failed"
    )
    print(f"Registers: {summary['unique_raw_registers']} unique raw registers")
    print(f"Snapshots: {summary['snapshots']}")
    print("Writes   : 0")
    print(
        "Privacy  : host={}, Monitor SN={}, inverter SN={}".format(
            "excluded" if not privacy["host_in_output"] else "included",
            "excluded" if not privacy["logger_sn_in_output"] else "included",
            "excluded" if not privacy["inverter_serial_in_output"] else "included",
        )
    )
    print(f"Output   : {output}")


def main() -> int:
    if sys.version_info < (3, 10):
        print("ERROR: Python 3.10 or newer is required. Use python3.", file=sys.stderr)
        return 2

    args = build_parser().parse_args()

    if args.compare:
        before_path, after_path = map(Path, args.compare)
        try:
            before = json.loads(before_path.read_text(encoding="utf-8"))
            after = json.loads(after_path.read_text(encoding="utf-8"))
            result = compare_documents(before, after)
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(
                    json.dumps(result, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
        except (OSError, TypeError, ValueError) as err:
            print(f"ERROR: could not compare dump files: {err}", file=sys.stderr)
            return 2
        print(f"Changed raw registers: {len(result['changed_registers'])}")
        for item in result["changed_registers"]:
            print(f"  {item['key']}: {item['before']} -> {item['after']}")
        if args.output:
            print(f"Comparison JSON: {args.output}")
        return 0

    print("TSUN Local Hardware Validation Dump Tool")
    print(f"Standalone v{TOOL_VERSION} · READ-ONLY · Python standard library only")
    print("No inverter configuration write operation is implemented.\n")

    try:
        targets, resolution = resolve_targets(args)
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")
        return 130
    except Exception as err:
        print(f"ERROR: {type(err).__name__}: {err}", file=sys.stderr)
        return 1

    total = len(targets)
    completed: list[Path] = []
    failed = 0
    if total > 1 and args.model:
        print("Note: --model is applied to every captured logger in this scan.")

    for sequence, (host, sn, discovery) in enumerate(targets, 1):
        discovered_index = int(discovery.get("target_index", sequence))
        print(f"\n=== Device {sequence}/{total} (discovery #{discovered_index}) ===")
        print(f"Logger   : {host}")
        if discovery.get("firmware_version"):
            print(f"Firmware : {discovery['firmware_version']}")
        try:
            document = capture(args, host, sn, discovery)
        except (KeyboardInterrupt, EOFError):
            print("\nCancelled.")
            return 130
        except Exception as err:
            failed += 1
            print(
                f"ERROR: device {sequence}/{total}: {type(err).__name__}: {err}",
                file=sys.stderr,
            )
            continue

        timestamp = datetime.fromisoformat(document["metadata"]["timestamp_utc"])
        output = output_path_for_target(
            args.output,
            args.model,
            document["metadata"]["detected_protocol"],
            timestamp,
            device_index=discovered_index,
            total_targets=total,
        )
        try:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(
                json.dumps(document, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        except OSError as err:
            failed += 1
            print(f"ERROR: could not write {output}: {err}", file=sys.stderr)
            continue
        completed.append(output)
        _print_dump_summary(document, output)

    print("\n=== Scan summary ===")
    print(f"Discovered: {resolution['devices_found']}")
    print(f"Resolved  : {resolution['targets_resolved']}")
    print(f"Skipped   : {resolution['targets_skipped']}")
    print(f"Captured  : {len(completed)}")
    print(f"Failed    : {failed}")
    if completed:
        print("Generated files:")
        for output in completed:
            print(f"  {output}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
