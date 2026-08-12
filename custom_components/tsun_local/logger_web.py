# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Read the logger serial number from its local status page."""

from __future__ import annotations

from dataclasses import dataclass
from html import unescape
import re

from aiohttp import BasicAuth, ClientError, ClientTimeout
from yarl import URL

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession


LOGGER_STATUS_PATHS = ("/index_cn.html", "/status.html")
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
    re.compile(
        rf"\bwebdata[_-]sn\s*[:=]\s*[\"']?{_SERIAL_NUMBER}",
        re.IGNORECASE,
    ),
    re.compile(
        rf"(?:device|logger|monitor)[_-]?(?:serial(?:_number)?|sn)"
        rf"\s*[:=]\s*[\"']?{_SERIAL_NUMBER}",
        re.IGNORECASE,
    ),
    re.compile(rf"\bAP_{_SERIAL_NUMBER}\b", re.IGNORECASE),
    re.compile(
        rf"\bcover[_-]mid\s*[:=]\s*[\"']?{_SERIAL_NUMBER}",
        re.IGNORECASE,
    ),
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


@dataclass(frozen=True, slots=True)
class LoggerWebData:
    """Non-secret metadata exposed by the logger's local status page."""

    logger_sn: int | None = None
    firmware_version: str | None = None
    mac_address: str | None = None


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

    return LoggerWebData(
        logger_sn=parse_logger_sn(document),
        firmware_version=firmware_version,
        mac_address=mac_address,
    )


async def async_read_logger_web_data(
    hass: HomeAssistant,
    host: str,
) -> LoggerWebData:
    """Best-effort read of metadata from the local HTTP status pages."""
    session = async_get_clientsession(hass)
    metadata = LoggerWebData()
    for path in LOGGER_STATUS_PATHS:
        url = URL.build(scheme="http", host=host, path=path)
        try:
            async with session.get(
                url,
                auth=BasicAuth(LOGGER_WEB_USERNAME, LOGGER_WEB_PASSWORD),
                timeout=ClientTimeout(total=LOGGER_WEB_TIMEOUT),
                allow_redirects=False,
            ) as response:
                if response.status != 200:
                    if response.status in {401, 403}:
                        break
                    continue
                if response.content_length is not None and (
                    response.content_length > MAX_LOGGER_PAGE_SIZE
                ):
                    continue
                content = await response.content.read(MAX_LOGGER_PAGE_SIZE + 1)
        except (ClientError, TimeoutError, UnicodeError, ValueError):
            break

        if len(content) > MAX_LOGGER_PAGE_SIZE:
            continue
        page_data = parse_logger_web_data(
            content.decode("utf-8", errors="replace")
        )
        metadata = LoggerWebData(
            logger_sn=metadata.logger_sn or page_data.logger_sn,
            firmware_version=(
                metadata.firmware_version or page_data.firmware_version
            ),
            mac_address=metadata.mac_address or page_data.mac_address,
        )
        if all(
            (
                metadata.logger_sn,
                metadata.firmware_version,
                metadata.mac_address,
            )
        ):
            break
    return metadata


async def async_detect_logger_sn(
    hass: HomeAssistant,
    host: str,
) -> int | None:
    """Best-effort detection from the logger's local HTTP status page."""
    return (await async_read_logger_web_data(hass, host)).logger_sn
