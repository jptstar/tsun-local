# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Protocol-independent data coordinator for TSUN Local."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .protocols import TsunProtocolClient, TsunReadResult
from .protocols.ap import safe_error_details

_LOGGER = logging.getLogger(__name__)
POLL_LOCK = "poll_lock"
LOGGER_WIFI_REFRESH_INTERVAL = timedelta(minutes=5)


def get_poll_lock(hass: HomeAssistant) -> asyncio.Lock:
    """Return the lock shared by setup validation and every device poll."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    return domain_data.setdefault(POLL_LOCK, asyncio.Lock())


class TsunCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate polling of one locally connected TSUN device."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: TsunProtocolClient,
        interval: int,
        error_interval: int,
        offline_interval: int,
        failure_threshold: int,
        poll_lock: asyncio.Lock,
        logger_firmware_version: str | None = None,
        logger_mac_address: str | None = None,
        inverter_serial_number: str | None = None,
        logger_raw_profile: str | None = None,
        logger_wifi_signal: int | None = None,
        logger_host: str | None = None,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=timedelta(seconds=interval),
        )
        self.client = client
        self._poll_lock = poll_lock
        self._normal_update_interval = timedelta(seconds=interval)
        self._error_update_interval = timedelta(seconds=error_interval)
        self._offline_update_interval = timedelta(seconds=offline_interval)
        self._failure_threshold = failure_threshold
        self._last_success: datetime | None = None
        self._consecutive_failures = 0
        self._online: bool | None = None
        self._last_error: dict[str, str] | None = None
        self._logger_metadata = {
            key: value
            for key, value in {
                "logger_firmware_version": logger_firmware_version,
                "logger_mac_address": logger_mac_address,
                "inverter_serial_number": inverter_serial_number,
                "logger_raw_profile": logger_raw_profile,
                "logger_wifi_signal": logger_wifi_signal,
            }.items()
            if value is not None
        }
        self._hass = hass
        self._logger_host = logger_host
        self._next_logger_wifi_refresh = (
            dt_util.utcnow() + LOGGER_WIFI_REFRESH_INTERVAL
            if logger_host is not None
            else None
        )

    @property
    def diagnostic_summary(self) -> dict[str, Any]:
        """Return communication state without connection identifiers."""
        summary: dict[str, Any] = {
            "online": self._online,
            "last_success": (
                self._last_success.isoformat()
                if self._last_success is not None
                else None
            ),
            "consecutive_failures": self._consecutive_failures,
            "failure_threshold": self._failure_threshold,
            "normal_polling_seconds": int(
                self._normal_update_interval.total_seconds()
            ),
            "error_polling_seconds": int(
                self._error_update_interval.total_seconds()
            ),
            "offline_polling_seconds": int(
                self._offline_update_interval.total_seconds()
            ),
            "last_error": self._last_error,
        }
        if self.data:
            summary["last_duration_ms"] = self.data.get("communication_duration")
            summary["last_blocks_ok"] = self.data.get("communication_blocks")
        return summary

    async def _async_refresh_logger_wifi_signal(self) -> None:
        """Refresh dynamic logger Wi-Fi telemetry at a low frequency."""
        if (
            self._logger_host is None
            or self._next_logger_wifi_refresh is None
        ):
            return
        now = dt_util.utcnow()
        if now < self._next_logger_wifi_refresh:
            return
        self._next_logger_wifi_refresh = now + LOGGER_WIFI_REFRESH_INTERVAL
        try:
            from .logger_web import async_read_logger_wifi_signal

            signal = await async_read_logger_wifi_signal(
                self._hass, self._logger_host
            )
        except Exception:  # Best-effort diagnostic refresh only.
            _LOGGER.debug(
                "Unable to refresh logger Wi-Fi signal", exc_info=True
            )
            return
        if signal is not None:
            self._logger_metadata["logger_wifi_signal"] = signal

    async def _async_update_data(self) -> dict[str, Any]:
        await self._async_refresh_logger_wifi_signal()
        try:
            # Some local loggers accept only one active protocol exchange.
            # Serialize complete polls across all configured TSUN devices.
            async with self._poll_lock:
                result: TsunReadResult = await self.client.async_read_all()
        except Exception as err:
            self._consecutive_failures += 1
            self._last_error = safe_error_details(err)
            trace = self.client.diagnostic_trace
            if trace:
                self._last_error["protocol"] = str(trace[-1].get("protocol", "unknown"))
                self._last_error["stage"] = str(trace[-1].get("stage", "unknown"))
            threshold_reached = (
                self._consecutive_failures >= self._failure_threshold
            )
            if threshold_reached:
                if self._online is not False:
                    _LOGGER.warning(
                        "TSUN device is unavailable after %s consecutive "
                        "communication failures (%s); polling reduced to every "
                        "%s seconds",
                        self._consecutive_failures,
                        type(err).__name__,
                        int(self._offline_update_interval.total_seconds()),
                    )
                self._online = False
                self.update_interval = self._offline_update_interval
            else:
                _LOGGER.debug(
                    "TSUN communication attempt failed (%s/%s, %s); keeping "
                    "the device available and retrying in %s seconds",
                    self._consecutive_failures,
                    self._failure_threshold,
                    type(err).__name__,
                    int(self._error_update_interval.total_seconds()),
                )
                self.update_interval = self._error_update_interval
            previous_data = {
                **self._logger_metadata,
                **dict(self.data or {}),
            }
            previous_data.update(
                {
                    "communication_online": self._online is True,
                    "communication_duration": 0,
                    "communication_blocks": 0,
                    "communication_failures": self._consecutive_failures,
                    "communication_last_success": self._last_success,
                }
            )
            return previous_data

        if self._online is False:
            _LOGGER.info(
                "TSUN device communication restored; normal polling resumed"
            )
        self._online = True
        self._consecutive_failures = 0
        self._last_error = None
        self.update_interval = self._normal_update_interval
        self._last_success = dt_util.utcnow()
        return {
            **self._logger_metadata,
            **result.measurements,
            "communication_online": True,
            "communication_last_success": self._last_success,
            "communication_duration": result.duration_ms,
            "communication_blocks": result.blocks_ok,
            "communication_failures": self._consecutive_failures,
        }
