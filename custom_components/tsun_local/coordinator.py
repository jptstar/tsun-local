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
POLL_LOCKS = "poll_locks"
INVERTER_SERIAL_PREFIX_LENGTH = 3


def get_poll_lock(hass: HomeAssistant, logger_key: str | int) -> asyncio.Lock:
    """Return the protocol lock dedicated to one local TSUN logger."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    locks: dict[str, asyncio.Lock] = domain_data.setdefault(POLL_LOCKS, {})
    return locks.setdefault(str(logger_key), asyncio.Lock())


def inverter_serial_prefix(serial_number: str | None) -> str | None:
    """Return a short privacy-safe inverter identifier such as ``Y47``."""
    if not serial_number:
        return None
    compact = "".join(
        character for character in serial_number.strip() if character.isalnum()
    )
    if len(compact) < INVERTER_SERIAL_PREFIX_LENGTH:
        return None
    return compact[:INVERTER_SERIAL_PREFIX_LENGTH].upper()


def _add_common_alarm_metadata(
    measurements: dict[str, Any], protocol_name: str
) -> dict[str, Any]:
    """Add protocol identity and a common active-alarm count when needed."""
    data = dict(measurements)
    data["_alarm_protocol"] = protocol_name.lower()
    if "alarm_active" in data and "alarm_active_count" not in data:
        data["alarm_active_count"] = sum(
            value.bit_count()
            for key, value in data.items()
            if (
                isinstance(value, int)
                and key.startswith("alarm_code_")
                and key.endswith("_raw")
            )
        )
    return data


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
        adaptive_polling: bool = False,
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
        self._adaptive_polling = adaptive_polling
        self._last_success: datetime | None = None
        self._consecutive_failures = 0
        self._consecutive_successes = 0
        self._online: bool | None = None
        self._last_error: dict[str, str] | None = None
        self._adaptive_level = 0
        self._adaptive_state = "normal" if adaptive_polling else "disabled"
        self._adaptive_reason = "normal" if adaptive_polling else "disabled"
        self._effective_interval_seconds = interval
        self._poll_attempts = 0
        self._poll_successes_total = 0
        self._poll_failures_total = 0
        self._adaptive_backoff_events = 0
        self._inverter_serial_prefix = inverter_serial_prefix(inverter_serial_number)
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

    @property
    def inverter_serial_prefix(self) -> str | None:
        """Return the short inverter serial prefix used in logs/diagnostics."""
        return self._inverter_serial_prefix

    @property
    def adaptive_polling_enabled(self) -> bool:
        """Return whether adaptive polling is enabled for this device."""
        return self._adaptive_polling

    def _device_log_name(self) -> str:
        """Return a log label without exposing the complete inverter serial."""
        if self._inverter_serial_prefix is None:
            return "TSUN device"
        return f"TSUN device [{self._inverter_serial_prefix}]"

    def _adaptive_intervals(self) -> tuple[int, ...]:
        """Build monotonic adaptive polling steps from the user limits."""
        normal = int(self._normal_update_interval.total_seconds())
        error = int(self._error_update_interval.total_seconds())
        offline = max(normal, int(self._offline_update_interval.total_seconds()))
        candidates = (
            normal,
            max(normal, error),
            round(normal * 1.5),
            normal * 3,
            normal * 6,
            offline,
        )
        steps: list[int] = []
        previous = normal
        for candidate in candidates:
            value = min(offline, max(previous, int(candidate)))
            steps.append(value)
            previous = value
        return tuple(steps)

    def _set_effective_polling(
        self,
        *,
        interval_seconds: int,
        state: str,
        reason: str,
    ) -> None:
        """Apply an interval and log adaptive state transitions compactly."""
        old_interval = self._effective_interval_seconds
        old_state = self._adaptive_state
        old_reason = self._adaptive_reason
        self._effective_interval_seconds = interval_seconds
        self._adaptive_state = state
        self._adaptive_reason = reason
        self.update_interval = timedelta(seconds=interval_seconds)
        if not self._adaptive_polling:
            return
        if (
            old_interval != interval_seconds
            or old_state != state
            or old_reason != reason
        ):
            _LOGGER.info(
                "%s adaptive polling: %s -> %s, %ss -> %ss (%s)",
                self._device_log_name(),
                old_state,
                state,
                old_interval,
                interval_seconds,
                reason,
            )

    def _communication_metrics(self) -> dict[str, Any]:
        """Return chartable communication and adaptive-polling diagnostics."""
        return {
            "communication_failures": self._consecutive_failures,
            "communication_successes_consecutive": self._consecutive_successes,
            "adaptive_polling_state": self._adaptive_state,
            "adaptive_polling_reason": self._adaptive_reason,
            "adaptive_polling_interval": self._effective_interval_seconds,
            "adaptive_backoff_events": self._adaptive_backoff_events,
        }

    @property
    def diagnostic_summary(self) -> dict[str, Any]:
        """Return communication state without connection identifiers."""
        summary: dict[str, Any] = {
            "online": self._online,
            "inverter_serial_prefix": self._inverter_serial_prefix,
            "last_success": (
                self._last_success.isoformat()
                if self._last_success is not None
                else None
            ),
            "consecutive_failures": self._consecutive_failures,
            "consecutive_successes": self._consecutive_successes,
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
            "adaptive_polling_enabled": self._adaptive_polling,
            "adaptive_polling_state": self._adaptive_state,
            "adaptive_polling_reason": self._adaptive_reason,
            "effective_polling_seconds": self._effective_interval_seconds,
            "poll_attempts": self._poll_attempts,
            "poll_successes_total": self._poll_successes_total,
            "poll_failures_total": self._poll_failures_total,
            "adaptive_backoff_events": self._adaptive_backoff_events,
            "last_error": self._last_error,
        }
        if self.data:
            summary["last_duration_ms"] = self.data.get(
                "communication_duration"
            )
            summary["last_blocks_ok"] = self.data.get(
                "communication_blocks"
            )
        return summary

    def async_update_logger_metadata(
        self, updates: dict[str, Any]
    ) -> bool:
        """Update logger metadata without resetting inverter polling."""
        changed = False
        for key, value in updates.items():
            if value is None or self._logger_metadata.get(key) == value:
                continue
            self._logger_metadata[key] = value
            if key == "inverter_serial_number":
                self._inverter_serial_prefix = inverter_serial_prefix(str(value))
            changed = True
        if not changed:
            return False

        self.data = {
            **dict(self.data or {}),
            **self._logger_metadata,
        }
        self.async_update_listeners()
        return True

    def _handle_failed_poll(self, err: Exception) -> None:
        """Update availability and polling cadence after one failed poll."""
        self._consecutive_failures += 1
        self._consecutive_successes = 0
        self._poll_failures_total += 1
        self._last_error = safe_error_details(err)
        trace = self.client.diagnostic_trace
        if trace:
            self._last_error["protocol"] = str(
                trace[-1].get("protocol", "unknown")
            )
            self._last_error["stage"] = str(
                trace[-1].get("stage", "unknown")
            )
        threshold_reached = self._consecutive_failures >= self._failure_threshold

        if self._adaptive_polling:
            steps = self._adaptive_intervals()
            previous_interval = self._effective_interval_seconds
            self._adaptive_level = min(self._adaptive_level + 1, len(steps) - 1)
            interval_seconds = steps[self._adaptive_level]
            if interval_seconds > previous_interval:
                self._adaptive_backoff_events += 1
            wifi_signal = self._logger_metadata.get("logger_wifi_signal")
            reason = (
                "wifi_signal_zero"
                if wifi_signal == 0
                else "communication_failure"
            )
            state = "offline" if threshold_reached else "degraded"
            self._set_effective_polling(
                interval_seconds=interval_seconds,
                state=state,
                reason=reason,
            )
        elif threshold_reached:
            self._effective_interval_seconds = int(
                self._offline_update_interval.total_seconds()
            )
            self.update_interval = self._offline_update_interval
        else:
            self._effective_interval_seconds = int(
                self._error_update_interval.total_seconds()
            )
            self.update_interval = self._error_update_interval

        if threshold_reached:
            if self._online is not False:
                _LOGGER.warning(
                    "%s is unavailable after %s consecutive communication "
                    "failures (%s); next poll in %s seconds",
                    self._device_log_name(),
                    self._consecutive_failures,
                    type(err).__name__,
                    self._effective_interval_seconds,
                )
            self._online = False
        else:
            _LOGGER.debug(
                "%s communication attempt failed (%s/%s, %s); retrying in "
                "%s seconds",
                self._device_log_name(),
                self._consecutive_failures,
                self._failure_threshold,
                type(err).__name__,
                self._effective_interval_seconds,
            )

    def _handle_successful_poll(self) -> None:
        """Restore availability and progressively recover adaptive cadence."""
        was_offline = self._online is False
        self._online = True
        self._consecutive_failures = 0
        self._consecutive_successes += 1
        self._poll_successes_total += 1
        self._last_error = None

        if self._adaptive_polling:
            steps = self._adaptive_intervals()
            if self._adaptive_level > 0:
                self._adaptive_level -= 1
                state = "recovery" if self._adaptive_level > 0 else "normal"
                reason = "recovery" if self._adaptive_level > 0 else "normal"
                self._set_effective_polling(
                    interval_seconds=steps[self._adaptive_level],
                    state=state,
                    reason=reason,
                )
            else:
                self._set_effective_polling(
                    interval_seconds=steps[0],
                    state="normal",
                    reason="normal",
                )
        else:
            self._effective_interval_seconds = int(
                self._normal_update_interval.total_seconds()
            )
            self.update_interval = self._normal_update_interval

        if was_offline:
            _LOGGER.info(
                "%s communication restored; polling recovery started",
                self._device_log_name(),
            )

    async def _async_update_data(self) -> dict[str, Any]:
        self._poll_attempts += 1
        try:
            # A logger can reject concurrent local exchanges. The lock is now
            # dedicated to this logger so an unrelated TSUN cannot block it.
            async with self._poll_lock:
                result: TsunReadResult = await self.client.async_read_all()
        except Exception as err:
            self._handle_failed_poll(err)
            previous_data = {
                **dict(self.data or {}),
                **self._logger_metadata,
            }
            previous_data.update(
                {
                    "communication_online": self._online is True,
                    "communication_duration": 0,
                    "communication_blocks": 0,
                    "communication_last_success": self._last_success,
                    **self._communication_metrics(),
                }
            )
            return previous_data

        self._handle_successful_poll()
        self._last_success = dt_util.utcnow()
        measurements = _add_common_alarm_metadata(
            result.measurements,
            str(getattr(self.client, "protocol_name", "1511")),
        )
        return {
            **self._logger_metadata,
            **measurements,
            "communication_online": True,
            "communication_last_success": self._last_success,
            "communication_duration": result.duration_ms,
            "communication_blocks": result.blocks_ok,
            **self._communication_metrics(),
        }
