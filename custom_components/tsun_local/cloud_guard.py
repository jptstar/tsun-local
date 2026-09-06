# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Read-only capability discovery for the future TSUN Local Cloud Guard."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from aiohttp import BasicAuth

from .logger_web import (
    LOGGER_WEB_PASSWORD,
    LOGGER_WEB_USERNAME,
    _async_read_logger_document,
)

_REMOTE_PATH = "/remote.html"
_WIRELESS_PATH = "/wireless.html"
_LOGGER_UPDATE_PATH = "/update.html"
_INVERTER_UPDATE_PATH = "/invupdate.html"

_SERVER_VALUE = re.compile(
    r"\bserver_[ab]\b[^>]{0,500}?value\s*=\s*[\"']([^\"']*)[\"']",
    re.IGNORECASE,
)
_SERVER_ASSIGNMENT = re.compile(
    r"\bserver_[ab]\b\s*[:=]\s*[\"']([^\"']*)[\"']",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class CloudGuardCapabilities:
    """Capabilities discovered without changing logger configuration."""

    remote_server_configurable: bool = False
    dns_configurable: bool = False
    logger_firmware_upload_available: bool = False
    inverter_firmware_upload_available: bool = False
    configured_server_ports: tuple[int, ...] = ()
    ssl_cloud_configured: bool = False
    write_operations_performed: bool = False


def _extract_server_ports(document: str | None) -> tuple[int, ...]:
    """Extract configured remote server ports without returning host names."""
    if not document:
        return ()

    values = [match.group(1) for match in _SERVER_VALUE.finditer(document)]
    values.extend(match.group(1) for match in _SERVER_ASSIGNMENT.finditer(document))

    ports: set[int] = set()
    for value in values:
        fields = [field.strip() for field in value.split(",")]
        if len(fields) < 3:
            continue
        try:
            port = int(fields[2])
        except ValueError:
            continue
        if 1 <= port <= 65535:
            ports.add(port)
    return tuple(sorted(ports))


def parse_cloud_guard_capabilities(
    *,
    remote_document: str | None,
    wireless_document: str | None,
    logger_update_document: str | None,
    inverter_update_document: str | None,
) -> CloudGuardCapabilities:
    """Parse passive logger web pages into a privacy-safe capability summary."""
    ports = _extract_server_ports(remote_document)

    remote_server_configurable = bool(
        remote_document
        and "server_setting_apply" in remote_document
        and ("server_a" in remote_document or "server_b" in remote_document)
    )
    dns_configurable = bool(
        wireless_document
        and "wan_setting_dns" in wireless_document
        and "sta_form_apply" in wireless_document
    )
    logger_firmware_upload_available = bool(
        logger_update_document
        and "SW_UPLOAD" in logger_update_document
        and "files" in logger_update_document
    )
    inverter_firmware_upload_available = bool(
        inverter_update_document
        and "NBQ_UPLOAD" in inverter_update_document
        and "files" in inverter_update_document
    )

    return CloudGuardCapabilities(
        remote_server_configurable=remote_server_configurable,
        dns_configurable=dns_configurable,
        logger_firmware_upload_available=logger_firmware_upload_available,
        inverter_firmware_upload_available=inverter_firmware_upload_available,
        configured_server_ports=ports,
        ssl_cloud_configured=10443 in ports,
        write_operations_performed=False,
    )


async def async_read_cloud_guard_capabilities(
    hass: Any,
    host: str,
) -> CloudGuardCapabilities:
    """Read Cloud Guard capabilities using GET requests only."""
    from homeassistant.helpers.aiohttp_client import async_get_clientsession

    session = async_get_clientsession(hass)
    credentials = (
        None,
        BasicAuth(LOGGER_WEB_USERNAME, LOGGER_WEB_PASSWORD),
    )

    async def _read(path: str) -> str | None:
        for auth in credentials:
            document = await _async_read_logger_document(session, host, path, auth)
            if document is not None:
                return document
        return None

    remote_document = await _read(_REMOTE_PATH)
    wireless_document = await _read(_WIRELESS_PATH)
    logger_update_document = await _read(_LOGGER_UPDATE_PATH)
    inverter_update_document = await _read(_INVERTER_UPDATE_PATH)

    return parse_cloud_guard_capabilities(
        remote_document=remote_document,
        wireless_document=wireless_document,
        logger_update_document=logger_update_document,
        inverter_update_document=inverter_update_document,
    )
