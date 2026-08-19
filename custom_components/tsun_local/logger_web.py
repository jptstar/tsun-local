# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Read the logger serial number from its local status page."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from html import unescape
import re
from typing import Any

from aiohttp import BasicAuth, ClientError, ClientTimeout
from yarl import URL

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession


LOGGER_STATUS_PATHS = ("/index_cn.html", "/index.html", "/status.html", "/")
LOGGER_PROFILE_PATHS = ("/hide_set_edit.html",)
LOGGER_WEB_USERNAME = "admin"
LOGGER_WEB_PASSWORD = "admin"
LOGGER_WEB_TIMEOUT = 4.0
MAX_LOGGER_PAGE_SIZE = 512 * 1024

_SERIAL_NUMBER = r"([1-9]\d{7,9})"
_LABEL_PATTERNS = (
    re.compile(
        rf"device\s*(?:serial\s*(?:number|no\.?|#)|sn)"
        rf"[\s\S]{{0,500}}?{_SERIAL_NUMBER}",
        re.IGNORECASE,
    ),
    re.compile(
        rf"(?:设备|裝置|裝置資訊)[^\d]{{0,80}}(?:序列号|序號|SN)"
        rf"[\s\S]{{0,500}}?{_SERIAL_NUMBER}",
        re.IGNORECASE,
    ),
)
_KEY_PATTERNS = (
    # cover_mid is the numeric Monitor SN / Logger SN. webdata_sn is the
    # inverter serial number and can contain a misleading numeric substring.
    re.compile(
        rf"\bcover[_-]mid\b[\s\S]{{0,160}}?{_SERIAL_NUMBER}",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\b(?:device|logger|monitor)[_-]?(?:serial(?:_number)?|sn)\b"
        rf"[\s\S]{{0,160}}?{_SERIAL_NUMBER}",
        re.IGNORECASE,
    ),
    re.compile(rf"\bAP_{_SERIAL_NUMBER}\b", re.IGNORECASE),
)
_DEVICE_INFORMATION = re.compile(
    r"device\s*information|设备信息|設備資訊",
    re.IGNORECASE,
)
_FIRMWARE_LABEL = re.compile(
    r"firmware\s*version\s+([A-Za-z0-9][A-Za-z0-9._-]{1,79})",
    re.IGNORECASE,
)
_FIRMWARE_KEYS = (
    re.compile(
        r"\b(?:webdata|cover)[_-]ver\s*[:=]\s*[\"']"
        r"([A-Za-z0-9][A-Za-z0-9._-]{1,79})",
        re.IGNORECASE,
    ),
)
_MAC_ADDRESS = r"([0-9A-F]{2}(?:[:-][0-9A-F]{2}){5})"
_MAC_LABEL = re.compile(
    rf"mac\s*address\s+{_MAC_ADDRESS}",
    re.IGNORECASE,
)
_MAC_KEYS = (
    re.compile(
        rf"\b(?:webdata|cover)[_-](?:ap[_-]|sta[_-])?mac"
        rf"\s*[:=]\s*[\"']{_MAC_ADDRESS}",
        re.IGNORECASE,
    ),
)
_INVERTER_SERIAL_KEYS = (
    re.compile(
        r"\bwebdata[_-]sn\s*[:=]\s*[\"']\s*"
        r"([A-Za-z0-9][A-Za-z0-9_-]{3,63})\s*[\"']",
        re.IGNORECASE,
    ),
)
_RAW_PROFILE_KEYS = (
    re.compile(
        r"\binv_tp\b\s*[:=]\s*[\"']\s*([^\"']{1,127}?)\s*[\"']",
        re.IGNORECASE,
    ),
)
_WIFI_SIGNAL_KEYS = (
    re.compile(
        r"\bcover_sta_rssi\b\s*[:=]\s*[\"']?\s*(-?\d{1,3})",
        re.IGNORECASE,
    ),
)


@dataclass(frozen=True, slots=True)
class LoggerWebData:
    """Non-secret metadata exposed by the logger's local status page."""

    logger_sn: int | None = None
    inverter_serial_number: str | None = None
    firmware_version: str | None = None
    mac_address: str | None = None
    raw_profile: str | None = None
    wifi_signal: int | None = None


def _valid_logger_sn(value: str) -> int | None:
    """Return a valid unsigned 32-bit logger serial number."""
    logger_sn = int(value)
    if 0 < logger_sn <= 0xFFFFFFFF:
        return logger_sn
    return None


def parse_logger_sn(document: str) -> int | None:
    """Extract the device/logger SN without confusing it with inverter SN."""
    visible_document = unescape(re.sub(r"<[^>]*>", " ", document))
    for pattern, source in (
        *((pattern, visible_document) for pattern in _LABEL_PATTERNS),
        *((pattern, document) for pattern in _KEY_PATTERNS),
    ):
        for match in pattern.finditer(source):
            if logger_sn := _valid_logger_sn(match.group(1)):
                return logger_sn
    return None


def _first_match(
    patterns: tuple[re.Pattern[str], ...], document: str
) -> str | None:
    """Return the first captured non-empty value."""
    for pattern in patterns:
        if match := pattern.search(document):
            return match.group(1)
    return None


def _parse_wifi_signal(document: str) -> int | None:
    """Extract the logger Wi-Fi signal percentage when exposed locally."""
    value = _first_match(_WIFI_SIGNAL_KEYS, document)
    if value is None:
        return None
    signal = int(value)
    return signal if 0 <= signal <= 100 else None


def parse_logger_web_data(document: str) -> LoggerWebData:
    """Extract logger identity, firmware, and MAC from a local page."""
    visible_document = unescape(re.sub(r"<[^>]*>", " ", document))
    device_section = ""
    if section_match := _DEVICE_INFORMATION.search(visible_document):
        device_section = visible_document[section_match.end() :]

    firmware_version = _first_match(_FIRMWARE_KEYS, document)
    if firmware_version is None and device_section:
        if match := _FIRMWARE_LABEL.search(device_section):
            firmware_version = match.group(1)

    mac_address = _first_match(_MAC_KEYS, document)
    if mac_address is None and device_section:
        if match := _MAC_LABEL.search(device_section):
            mac_address = match.group(1)
    if mac_address is not None:
        mac_address = mac_address.replace("-", ":").upper()

    inverter_serial_number = _first_match(_INVERTER_SERIAL_KEYS, document)
    raw_profile = _first_match(_RAW_PROFILE_KEYS, document)
    if raw_profile is not None:
        raw_profile = raw_profile.strip() or None
    wifi_signal = _parse_wifi_signal(document)

    return LoggerWebData(
        logger_sn=parse_logger_sn(document),
        inverter_serial_number=inverter_serial_number,
        firmware_version=firmware_version,
        mac_address=mac_address,
        raw_profile=raw_profile,
        wifi_signal=wifi_signal,
    )


def _merge_logger_web_data(
    current: LoggerWebData, new: LoggerWebData
) -> LoggerWebData:
    """Merge newly parsed logger data without dropping known values."""
    return LoggerWebData(
        logger_sn=current.logger_sn or new.logger_sn,
        inverter_serial_number=(
            current.inverter_serial_number or new.inverter_serial_number
        ),
        firmware_version=current.firmware_version or new.firmware_version,
        mac_address=current.mac_address or new.mac_address,
        raw_profile=current.raw_profile or new.raw_profile,
        wifi_signal=(
            new.wifi_signal
            if new.wifi_signal is not None
            else current.wifi_signal
        ),
    )


async def _async_read_limited(content: object) -> bytes | None:
    """Read a streamed page completely while enforcing the size limit."""
    chunks: list[bytes] = []
    total = 0
    async for chunk in content.iter_chunked(16 * 1024):  # type: ignore[attr-defined]
        total += len(chunk)
        if total > MAX_LOGGER_PAGE_SIZE:
            return None
        chunks.append(chunk)
    return b"".join(chunks)


async def async_probe_logger_sn(host: str, port: int) -> int | None:
    """Best-effort discovery from the identity in a local AP response."""
    # Imports stay local so the HTML parser remains independently testable.
    from .protocols.ap import (
        TsunProtocolError,
        build_ap_frame,
        extract_ap_logger_sn,
        read_ap_frame,
    )
    from .protocols.protocol_02b0 import build_modbus_request
    from .protocols.protocol_1511 import build_1511_request

    probe_payloads = (
        build_1511_request(0xA1, 0x01, 0x0BB8, 0x0BD0),
        build_modbus_request(0x03, 0x3009, 0x301E),
    )
    for payload in probe_payloads:
        writer: asyncio.StreamWriter | None = None
        try:
            async with asyncio.timeout(LOGGER_WEB_TIMEOUT):
                reader, writer = await asyncio.open_connection(host, port)
                writer.write(build_ap_frame(0, payload))
                await writer.drain()
                response = await read_ap_frame(reader)
            return extract_ap_logger_sn(response)
        except (
            OSError,
            TimeoutError,
            asyncio.IncompleteReadError,
            TsunProtocolError,
            ValueError,
        ):
            continue
        finally:
            if writer is not None:
                writer.close()
                try:
                    await writer.wait_closed()
                except OSError:
                    pass
    return None


async def _async_read_logger_document(
    session: Any, host: str, path: str, auth: BasicAuth | None
) -> str | None:
    """Read one bounded logger web page."""
    url = URL.build(scheme="http", host=host, path=path)
    try:
        async with session.get(
            url,
            auth=auth,
            timeout=ClientTimeout(total=LOGGER_WEB_TIMEOUT),
            allow_redirects=False,
        ) as response:
            if response.status != 200:
                return None
            if response.content_length is not None and (
                response.content_length > MAX_LOGGER_PAGE_SIZE
            ):
                return None
            content = await _async_read_limited(response.content)
    except (ClientError, TimeoutError, UnicodeError, ValueError):
        return None
    if content is None:
        return None
    return content.decode("utf-8", errors="replace")


async def async_read_logger_web_data(
    hass: HomeAssistant,
    host: str,
    port: int | None = None,
) -> LoggerWebData:
    """Best-effort read of identity and metadata from the local logger."""
    session = async_get_clientsession(hass)
    metadata = LoggerWebData()
    credentials = (
        None,
        BasicAuth(LOGGER_WEB_USERNAME, LOGGER_WEB_PASSWORD),
    )

    for path in LOGGER_STATUS_PATHS:
        for auth in credentials:
            document = await _async_read_logger_document(
                session, host, path, auth
            )
            if document is None:
                continue
            metadata = _merge_logger_web_data(
                metadata, parse_logger_web_data(document)
            )
            if all(
                (
                    metadata.logger_sn,
                    metadata.inverter_serial_number,
                    metadata.firmware_version,
                    metadata.mac_address,
                    metadata.wifi_signal is not None,
                )
            ):
                break
        if all(
            (
                metadata.logger_sn,
                metadata.inverter_serial_number,
                metadata.firmware_version,
                metadata.mac_address,
                metadata.wifi_signal is not None,
            )
        ):
            break

    if metadata.raw_profile is None:
        for path in LOGGER_PROFILE_PATHS:
            for auth in credentials:
                document = await _async_read_logger_document(
                    session, host, path, auth
                )
                if document is None:
                    continue
                metadata = _merge_logger_web_data(
                    metadata, parse_logger_web_data(document)
                )
                if metadata.raw_profile is not None:
                    break
            if metadata.raw_profile is not None:
                break

    if metadata.logger_sn is None and port is not None:
        metadata = LoggerWebData(
            logger_sn=await async_probe_logger_sn(host, port),
            inverter_serial_number=metadata.inverter_serial_number,
            firmware_version=metadata.firmware_version,
            mac_address=metadata.mac_address,
            raw_profile=metadata.raw_profile,
            wifi_signal=metadata.wifi_signal,
        )
    return metadata


async def async_read_logger_wifi_signal(
    hass: HomeAssistant, host: str
) -> int | None:
    """Read the current logger Wi-Fi signal without polling the inverter."""
    session = async_get_clientsession(hass)
    credentials = (
        None,
        BasicAuth(LOGGER_WEB_USERNAME, LOGGER_WEB_PASSWORD),
    )
    for path in LOGGER_STATUS_PATHS:
        for auth in credentials:
            document = await _async_read_logger_document(
                session, host, path, auth
            )
            if document is None:
                continue
            signal = _parse_wifi_signal(document)
            if signal is not None:
                return signal
    return None


async def async_detect_logger_sn(
    hass: HomeAssistant,
    host: str,
) -> int | None:
    """Best-effort detection from the logger's local HTTP status page."""
    return (await async_read_logger_web_data(hass, host)).logger_sn
