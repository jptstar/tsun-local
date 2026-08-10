# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Protocol-independent data coordinator for TSUN Local."""

from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .protocols import TsunProtocolClient, TsunReadResult

_LOGGER = logging.getLogger(__name__)


class TsunCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate polling of one locally connected TSUN device."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: TsunProtocolClient,
        interval: int,
        offline_interval: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=timedelta(seconds=interval),
        )
        self.client = client
        self._normal_update_interval = timedelta(seconds=interval)
        self._offline_update_interval = timedelta(seconds=offline_interval)
        self._last_success: datetime | None = None
        self._consecutive_failures = 0
        self._online: bool | None = None

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            result: TsunReadResult = await self.client.async_read_all()
        except Exception as err:
            self._consecutive_failures += 1
            if self._online is not False:
                _LOGGER.warning(
                    "TSUN device is unavailable (%s); polling reduced to every %s seconds",
                    err,
                    int(self._offline_update_interval.total_seconds()),
                )
            self._online = False
            self.update_interval = self._offline_update_interval
            previous_data = dict(self.data or {})
            previous_data.update(
                {
                    "communication_online": False,
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
        self.update_interval = self._normal_update_interval
        self._last_success = dt_util.utcnow()
        return {
            **result.measurements,
            "communication_online": True,
            "communication_last_success": self._last_success,
            "communication_duration": result.duration_ms,
            "communication_blocks": result.blocks_ok,
            "communication_failures": self._consecutive_failures,
        }
