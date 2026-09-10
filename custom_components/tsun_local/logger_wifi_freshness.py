# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Freshness policy for the logger Wi-Fi signal."""

from __future__ import annotations

from dataclasses import dataclass

LOGGER_WIFI_MISS_THRESHOLD = 2


@dataclass(slots=True)
class LoggerWifiSignalFreshness:
    """Expire RSSI only after repeated HTTP refresh misses."""

    consecutive_misses: int = 0
    miss_threshold: int = LOGGER_WIFI_MISS_THRESHOLD

    def observe(self, signal: int | None) -> bool:
        """Return True when a missing RSSI has become stale."""
        if signal is not None:
            self.consecutive_misses = 0
            return False
        self.consecutive_misses += 1
        return self.consecutive_misses >= self.miss_threshold
