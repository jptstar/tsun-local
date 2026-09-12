# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Shared daily-energy tracking for all TSUN Local protocol families."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import math
from typing import Any


def energy_value(value: object) -> float | None:
    """Return one finite numeric energy value, otherwise None."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        result = float(value)
    else:
        try:
            result = float(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return None
    return result if math.isfinite(result) else None


# Supported TSUN Local micro-inverters cannot physically produce 100 kWh in
# one local day. This conservative ceiling is used only to repair clearly
# impossible 1.6.1 states that were already contaminated by the Wh/kWh
# restore regression. Plausible values are never guessed or rewritten.
LEGACY_DAILY_SANITY_LIMIT_KWH = 100.0


def repair_legacy_daily_state(
    state_value: float,
    *,
    current_total_energy: float | None,
    restored_total_energy: float | None,
) -> float:
    """Repair only unambiguous 1.6.1 x1000 daily-energy contamination."""
    if state_value < 0:
        return 0.0
    candidate = state_value / 1000.0

    # A daily value above this ceiling is impossible for supported hardware.
    if (
        state_value >= LEGACY_DAILY_SANITY_LIMIT_KWH
        and candidate < LEGACY_DAILY_SANITY_LIMIT_KWH
    ):
        return candidate

    # Daily energy can never exceed the lifetime total. If only the /1000
    # candidate satisfies that invariant, the legacy scale error is certain.
    for total in (current_total_energy, restored_total_energy):
        if total is None or total < 0:
            continue
        if state_value > total + 1e-6 and candidate <= total + 1e-6:
            return candidate

    return state_value


@dataclass(slots=True)
class DailyEnergyTracker:
    """Keep a Home Assistant day continuous across logger counter resets.

    The hardware daily counter is an input, not the clock. Home Assistant
    local midnight is the only day boundary. Between boundaries the
    monotonic total-energy counter is preferred for deltas; the raw daily
    counter is only a fallback when a total value cannot be used.
    """

    local_date: date
    value: float | None = None
    raw_daily: float | None = None
    total_energy: float | None = None
    reset_pending: bool = False

    def reset_for_date(
        self,
        new_date: date,
        *,
        raw_daily: float | None,
        total_energy: float | None,
    ) -> float:
        """Start a new HA-local day while retaining hardware references."""
        self.local_date = new_date
        self.value = 0.0
        self.raw_daily = raw_daily
        self.total_energy = total_energy
        self.reset_pending = True
        return 0.0

    def restore(
        self,
        *,
        current_date: date,
        state_value: float | None,
        state_date: date | None,
        restored_raw_daily: float | None,
        restored_total_energy: float | None,
        current_raw_daily: float | None,
        current_total_energy: float | None,
        current_online: bool,
    ) -> float | None:
        """Restore state and recover a same-day HA restart when possible."""
        self.local_date = current_date

        if state_value is None:
            if current_online and current_raw_daily is not None:
                self.value = current_raw_daily
                self.raw_daily = current_raw_daily
                self.total_energy = current_total_energy
                self.reset_pending = False
            else:
                self.value = None
                self.raw_daily = restored_raw_daily
                self.total_energy = restored_total_energy
                self.reset_pending = False
            return self.value

        if state_date == current_date:
            self.value = max(0.0, state_value)
            self.raw_daily = restored_raw_daily
            self.total_energy = restored_total_energy
            self.reset_pending = False

            # Migration from beta.4 and older: no tracker metadata exists.
            # Keep the restored value if the raw counter has fallen; accept
            # a newer raw value when it is already greater or equal.
            if (
                restored_raw_daily is None
                and restored_total_energy is None
                and current_online
                and current_raw_daily is not None
            ):
                if current_raw_daily >= self.value:
                    self.value = current_raw_daily
                self.raw_daily = current_raw_daily
                self.total_energy = current_total_energy
                return self.value

            if current_online and current_raw_daily is not None:
                self.update(
                    current_date=current_date,
                    raw_daily=current_raw_daily,
                    total_energy=current_total_energy,
                    online=True,
                )
            return self.value

        # HA was absent across a day boundary. Without an observation at
        # midnight, an energy increase cannot always be allocated exactly
        # between yesterday and today. Use the first fresh hardware daily
        # value as a best-effort fallback rather than fabricating a split.
        if current_online and current_raw_daily is not None:
            self.value = current_raw_daily
            self.raw_daily = current_raw_daily
            self.total_energy = current_total_energy
            self.reset_pending = False
        else:
            self.value = 0.0
            self.raw_daily = None
            self.total_energy = None
            self.reset_pending = True
        return self.value

    def update(
        self,
        *,
        current_date: date,
        raw_daily: float | None,
        total_energy: float | None,
        online: bool,
    ) -> float | None:
        """Advance the displayed daily value without accepting false resets."""
        if current_date != self.local_date:
            return self.reset_for_date(
                current_date,
                raw_daily=raw_daily,
                total_energy=total_energy,
            )

        if not online or raw_daily is None:
            return self.value

        if self.value is None:
            self.value = raw_daily
        elif (
            self.reset_pending
            and self.raw_daily is None
            and self.total_energy is None
        ):
            self.value = raw_daily
        else:
            delta: float | None = None
            if total_energy is not None and self.total_energy is not None:
                if total_energy >= self.total_energy:
                    delta = total_energy - self.total_energy
            if delta is None and self.raw_daily is not None:
                # A lower raw daily value is a hardware/logger reset, not
                # a new HA day. A negative delta therefore becomes zero.
                delta = max(0.0, raw_daily - self.raw_daily)
            if delta is not None:
                self.value += delta

        self.value = round(max(0.0, self.value), 6)
        self.raw_daily = raw_daily
        self.total_energy = total_energy
        self.reset_pending = False
        return self.value

    def state_attributes(self) -> dict[str, Any]:
        """Return compact restore metadata stored with the HA state."""
        attributes: dict[str, Any] = {
            "tracking_date": self.local_date.isoformat(),
            "tracking_source": "total_delta_with_daily_fallback",
            "tracking_version": 2,
        }
        if self.raw_daily is not None:
            attributes["raw_daily_energy"] = self.raw_daily
        if self.total_energy is not None:
            attributes["tracking_total_energy"] = self.total_energy
        return attributes
