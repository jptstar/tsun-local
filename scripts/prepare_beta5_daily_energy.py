# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Prepare TSUN Local 1.6.1-beta.5 daily-energy harmonization."""

from __future__ import annotations

import json
from pathlib import Path
import re
import textwrap

ROOT = Path(__file__).parents[1]


def write_daily_energy_tracker() -> None:
    path = ROOT / "custom_components/tsun_local/daily_energy.py"
    path.write_text(
        textwrap.dedent(
            '''\
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
                    }
                    if self.raw_daily is not None:
                        attributes["raw_daily_energy"] = self.raw_daily
                    if self.total_energy is not None:
                        attributes["tracking_total_energy"] = self.total_energy
                    return attributes
            '''
        ),
        encoding="utf-8",
    )


def patch_sensor() -> None:
    path = ROOT / "custom_components/tsun_local/sensor.py"
    source = path.read_text(encoding="utf-8")

    import_anchor = "from .coordinator import TsunCoordinator\n"
    import_line = "from .daily_energy import DailyEnergyTracker, energy_value\n"
    if import_line not in source:
        if import_anchor not in source:
            raise RuntimeError("sensor.py coordinator import anchor not found")
        source = source.replace(import_anchor, import_anchor + import_line, 1)

    old_init = textwrap.dedent(
        """\
                self._restored_energy_value: float | None = None
                self._daily_reset_override = False
        """
    )
    # dedent removes the eight class-body spaces, so use the literal form.
    old_init = "        self._restored_energy_value: float | None = None\n        self._daily_reset_override = False\n"
    new_init = (
        "        self._restored_energy_value: float | None = None\n"
        "        self._daily_tracker = (\n"
        "            DailyEnergyTracker(dt_util.now().date())\n"
        "            if self._is_daily_energy\n"
        "            else None\n"
        "        )\n"
    )
    if old_init not in source:
        raise RuntimeError("sensor.py beta.4 energy init block not found")
    source = source.replace(old_init, new_init, 1)

    lifecycle_pattern = re.compile(
        r"    @property\n    def _is_energy\(self\) -> bool:\n.*?        super\(\)\._handle_coordinator_update\(\)\n",
        re.DOTALL,
    )
    match = lifecycle_pattern.search(source)
    if match is None:
        raise RuntimeError("sensor.py energy lifecycle block not found")

    lifecycle = textwrap.indent(
        textwrap.dedent(
            '''\
            @property
            def _is_energy(self) -> bool:
                return self.entity_description.device_class == SensorDeviceClass.ENERGY

            @property
            def _is_daily_energy(self) -> bool:
                return self._is_energy and self.entity_description.key.endswith("_energy_today")

            @property
            def _daily_total_key(self) -> str | None:
                if not self._is_daily_energy:
                    return None
                return self.entity_description.key.removesuffix("_today") + "_total"

            def _current_daily_inputs(
                self, *, require_online: bool
            ) -> tuple[float | None, float | None]:
                """Return current raw daily and total values for this channel."""
                if require_online and not bool(
                    self.coordinator.data.get("communication_online", False)
                ):
                    return None, None
                raw_daily = energy_value(
                    self.coordinator.data.get(self.entity_description.key)
                )
                total_key = self._daily_total_key
                total_energy = (
                    energy_value(self.coordinator.data.get(total_key))
                    if total_key is not None
                    else None
                )
                return raw_daily, total_energy

            @override
            async def async_added_to_hass(self) -> None:
                """Restore energy counters and register the local midnight rollover."""
                await super().async_added_to_hass()
                if not self._is_energy:
                    return

                if self._daily_tracker is not None:
                    self.async_on_remove(
                        async_track_time_change(
                            self.hass,
                            self._async_midnight_rollover,
                            hour=0,
                            minute=0,
                            second=0,
                        )
                    )

                    last_state = await self.async_get_last_state()
                    state_value: float | None = None
                    state_date = None
                    restored_raw = None
                    restored_total = None
                    if last_state is not None and last_state.state not in (
                        STATE_UNKNOWN,
                        STATE_UNAVAILABLE,
                    ):
                        state_value = energy_value(last_state.state)
                        state_date = dt_util.as_local(last_state.last_updated).date()
                        restored_raw = energy_value(
                            last_state.attributes.get("raw_daily_energy")
                        )
                        restored_total = energy_value(
                            last_state.attributes.get("tracking_total_energy")
                        )

                    current_online = bool(
                        self.coordinator.data.get("communication_online", False)
                    )
                    current_raw, current_total = self._current_daily_inputs(
                        require_online=True
                    )
                    self._daily_tracker.restore(
                        current_date=dt_util.now().date(),
                        state_value=state_value,
                        state_date=state_date,
                        restored_raw_daily=restored_raw,
                        restored_total_energy=restored_total,
                        current_raw_daily=current_raw,
                        current_total_energy=current_total,
                        current_online=current_online,
                    )
                    self._restored_energy_value = self._daily_tracker.value
                    return

                key = self.entity_description.key
                if key in self.coordinator.data:
                    return
                last_state = await self.async_get_last_state()
                if last_state is None or last_state.state in (
                    STATE_UNKNOWN,
                    STATE_UNAVAILABLE,
                ):
                    return
                self._restored_energy_value = energy_value(last_state.state)

            @callback
            def _async_midnight_rollover(self, _now: datetime) -> None:
                """Reset daily energy at Home Assistant local midnight only."""
                if self._daily_tracker is None:
                    return
                raw_daily, total_energy = self._current_daily_inputs(
                    require_online=False
                )
                self._daily_tracker.reset_for_date(
                    dt_util.now().date(),
                    raw_daily=raw_daily,
                    total_energy=total_energy,
                )
                self._restored_energy_value = 0.0
                self.async_write_ha_state()

            @callback
            @override
            def _handle_coordinator_update(self) -> None:
                """Advance one shared daily-energy policy for every protocol."""
                if self._daily_tracker is not None:
                    raw_daily, total_energy = self._current_daily_inputs(
                        require_online=True
                    )
                    self._daily_tracker.update(
                        current_date=dt_util.now().date(),
                        raw_daily=raw_daily,
                        total_energy=total_energy,
                        online=bool(
                            self.coordinator.data.get("communication_online", False)
                        ),
                    )
                    self._restored_energy_value = self._daily_tracker.value
                super()._handle_coordinator_update()
            '''
        ),
        "    ",
    )
    source = source[: match.start()] + lifecycle + source[match.end() :]

    old_native = (
        "        key = self.entity_description.key\n"
        "        if self._is_daily_energy and self._daily_reset_override:\n"
        "            return 0.0\n"
        "        if key in self.coordinator.data:\n"
        "            return self.coordinator.data[key]\n"
    )
    new_native = (
        "        key = self.entity_description.key\n"
        "        if self._daily_tracker is not None and self._daily_tracker.value is not None:\n"
        "            return self._daily_tracker.value\n"
        "        if key in self.coordinator.data:\n"
        "            return self.coordinator.data[key]\n"
    )
    if old_native not in source:
        raise RuntimeError("sensor.py native daily block not found")
    source = source.replace(old_native, new_native, 1)

    attrs_anchor = (
        "    def extra_state_attributes(self) -> dict[str, Any] | None:\n"
        "        \"\"\"Expose active alarm names or compact raw diagnostics.\"\"\"\n"
    )
    attrs_insert = attrs_anchor + (
        "        if self._daily_tracker is not None:\n"
        "            return self._daily_tracker.state_attributes()\n"
    )
    if attrs_anchor not in source:
        raise RuntimeError("sensor.py extra attributes anchor not found")
    source = source.replace(attrs_anchor, attrs_insert, 1)

    old_available = (
        "        if self._is_energy:\n"
        "            return super().available and (\n"
        "                key in self.coordinator.data\n"
        "                or self._restored_energy_value is not None\n"
        "                or self._daily_reset_override\n"
        "            )\n"
    )
    new_available = (
        "        if self._is_energy:\n"
        "            return super().available and (\n"
        "                key in self.coordinator.data\n"
        "                or self._restored_energy_value is not None\n"
        "                or (\n"
        "                    self._daily_tracker is not None\n"
        "                    and self._daily_tracker.value is not None\n"
        "                )\n"
        "            )\n"
    )
    if old_available not in source:
        raise RuntimeError("sensor.py availability block not found")
    source = source.replace(old_available, new_available, 1)

    if "_daily_reset_override" in source:
        raise RuntimeError("stale _daily_reset_override remains in sensor.py")
    path.write_text(source, encoding="utf-8")


def patch_1097() -> None:
    path = ROOT / "custom_components/tsun_local/protocols/protocol_1097.py"
    source = path.read_text(encoding="utf-8")
    old_fields = (
        "        self._last_measurements: dict[str, float | int | str] = {}\n"
        "        self._daily_reset_candidates: dict[str, float | int] = {}\n"
    )
    if old_fields not in source:
        raise RuntimeError("1097 daily stabilizer fields not found")
    source = source.replace(old_fields, "", 1)

    pattern = re.compile(
        r"\n    def _stabilize_daily_energy\(\n.*?        return stabilized\n",
        re.DOTALL,
    )
    source, count = pattern.subn("\n", source, count=1)
    if count != 1:
        raise RuntimeError("1097 daily stabilizer method not found")

    call = "        measurements = self._stabilize_daily_energy(measurements)\n"
    if call not in source:
        raise RuntimeError("1097 daily stabilizer call not found")
    source = source.replace(call, "", 1)
    if "_stabilize_daily_energy" in source or "_daily_reset_candidates" in source:
        raise RuntimeError("old 1097 reset heuristic still present")
    path.write_text(source, encoding="utf-8")


def write_tests() -> None:
    (ROOT / "tests/test_daily_energy_tracker.py").write_text(
        textwrap.dedent(
            '''\
            # Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
            # SPDX-License-Identifier: GPL-3.0-or-later

            """Regression tests for harmonized daily-energy tracking."""

            from __future__ import annotations

            from datetime import date
            import importlib.util
            from pathlib import Path
            import sys
            import unittest

            MODULE_PATH = (
                Path(__file__).parents[1]
                / "custom_components"
                / "tsun_local"
                / "daily_energy.py"
            )
            SPEC = importlib.util.spec_from_file_location("tsun_daily_energy_tests", MODULE_PATH)
            assert SPEC is not None and SPEC.loader is not None
            MODULE = importlib.util.module_from_spec(SPEC)
            sys.modules[SPEC.name] = MODULE
            SPEC.loader.exec_module(MODULE)
            DailyEnergyTracker = MODULE.DailyEnergyTracker


            class DailyEnergyTrackerTests(unittest.TestCase):
                def test_1511_or_02b0_sunrise_reset_does_not_create_new_day(self) -> None:
                    day = date(2026, 9, 8)
                    tracker = DailyEnergyTracker(date(2026, 9, 7), value=1.9)
                    tracker.reset_for_date(day, raw_daily=1.9, total_energy=100.0)
                    self.assertEqual(
                        tracker.update(current_date=day, raw_daily=1.9, total_energy=100.0, online=True),
                        0.0,
                    )
                    self.assertEqual(
                        tracker.update(current_date=day, raw_daily=0.0, total_energy=100.0, online=True),
                        0.0,
                    )
                    self.assertAlmostEqual(
                        tracker.update(current_date=day, raw_daily=0.2, total_energy=100.2, online=True),
                        0.2,
                    )

                def test_1097_18h_reset_is_ignored_while_total_continues(self) -> None:
                    day = date(2026, 9, 8)
                    tracker = DailyEnergyTracker(
                        day, value=3.2, raw_daily=3.2, total_energy=1003.2
                    )
                    self.assertAlmostEqual(
                        tracker.update(current_date=day, raw_daily=0.0, total_energy=1003.2, online=True),
                        3.2,
                    )
                    self.assertAlmostEqual(
                        tracker.update(current_date=day, raw_daily=0.25, total_energy=1003.45, online=True),
                        3.45,
                    )

                def test_same_day_restart_recovers_missed_total_delta(self) -> None:
                    day = date(2026, 9, 8)
                    tracker = DailyEnergyTracker(day)
                    value = tracker.restore(
                        current_date=day,
                        state_value=3.2,
                        state_date=day,
                        restored_raw_daily=3.2,
                        restored_total_energy=1003.2,
                        current_raw_daily=0.25,
                        current_total_energy=1003.45,
                        current_online=True,
                    )
                    self.assertAlmostEqual(value, 3.45)

                def test_restart_after_midnight_uses_midnight_total_reference(self) -> None:
                    day = date(2026, 9, 8)
                    tracker = DailyEnergyTracker(day)
                    value = tracker.restore(
                        current_date=day,
                        state_value=0.0,
                        state_date=day,
                        restored_raw_daily=0.40,
                        restored_total_energy=1003.60,
                        current_raw_daily=0.42,
                        current_total_energy=1003.62,
                        current_online=True,
                    )
                    self.assertAlmostEqual(value, 0.02)

                def test_long_cross_midnight_outage_uses_fresh_daily_best_effort(self) -> None:
                    yesterday = date(2026, 9, 7)
                    today = date(2026, 9, 8)
                    tracker = DailyEnergyTracker(today)
                    value = tracker.restore(
                        current_date=today,
                        state_value=3.0,
                        state_date=yesterday,
                        restored_raw_daily=3.0,
                        restored_total_energy=1000.0,
                        current_raw_daily=1.5,
                        current_total_energy=1001.9,
                        current_online=True,
                    )
                    self.assertEqual(value, 1.5)

                def test_total_reset_falls_back_to_raw_daily_delta(self) -> None:
                    day = date(2026, 9, 8)
                    tracker = DailyEnergyTracker(
                        day, value=2.0, raw_daily=2.0, total_energy=500.0
                    )
                    value = tracker.update(
                        current_date=day,
                        raw_daily=2.1,
                        total_energy=1.0,
                        online=True,
                    )
                    self.assertAlmostEqual(value, 2.1)


            if __name__ == "__main__":
                unittest.main()
            '''
        ),
        encoding="utf-8",
    )

    (ROOT / "tests/test_energy_restore_contract.py").write_text(
        textwrap.dedent(
            '''\
            # Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
            # SPDX-License-Identifier: GPL-3.0-or-later

            """Regression tests for offline energy restoration and daily rollover."""

            from __future__ import annotations

            from pathlib import Path
            import unittest

            ROOT = Path(__file__).parents[1]


            class EnergyRestoreContractTests(unittest.TestCase):
                def test_energy_entities_use_home_assistant_restore_state(self) -> None:
                    source = (ROOT / "custom_components/tsun_local/sensor.py").read_text(
                        encoding="utf-8"
                    )
                    self.assertIn("RestoreEntity", source)
                    self.assertIn("async_get_last_state", source)
                    self.assertIn("STATE_UNKNOWN", source)
                    self.assertIn("STATE_UNAVAILABLE", source)
                    self.assertIn("DailyEnergyTracker", source)

                def test_daily_energy_has_local_midnight_rollover(self) -> None:
                    source = (ROOT / "custom_components/tsun_local/sensor.py").read_text(
                        encoding="utf-8"
                    )
                    self.assertIn("async_track_time_change", source)
                    self.assertIn("hour=0", source)
                    self.assertIn("minute=0", source)
                    self.assertIn("second=0", source)
                    self.assertIn("reset_for_date", source)
                    self.assertIn("dt_util.now().date()", source)
                    self.assertIn("tracking_total_energy", source)
                    self.assertNotIn("_daily_reset_override", source)
                    self.assertNotIn("_daily_reset_successes", source)

                def test_missing_energy_without_history_is_unavailable_not_unknown(self) -> None:
                    source = (ROOT / "custom_components/tsun_local/sensor.py").read_text(
                        encoding="utf-8"
                    )
                    self.assertIn("self._daily_tracker is not None", source)
                    self.assertIn("self._daily_tracker.value is not None", source)
                    self.assertIn("or self._restored_energy_value is not None", source)
                    self.assertNotIn("return True", source)

                def test_1511_adds_all_validated_pv_entities_even_before_live_detection(self) -> None:
                    source = (ROOT / "custom_components/tsun_local/sensor.py").read_text(
                        encoding="utf-8"
                    )
                    self.assertIn('protocol_name == "1511"', source)
                    self.assertIn('description.key.startswith("pv")', source)


            if __name__ == "__main__":
                unittest.main()
            '''
        ),
        encoding="utf-8",
    )

    path = ROOT / "tests/test_protocol_1097_resilience.py"
    source = path.read_text(encoding="utf-8")
    source = source.replace(
        '    """Verify persistent sessions, retry and daily-counter stability."""',
        '    """Verify persistent sessions and bounded retry behavior."""',
        1,
    )
    pattern = re.compile(
        r'\n    def test_transient_daily_zero_is_not_published\(self\) -> None:\n.*?        self.assertEqual\(second_lower\["ac_energy_today"\], 0\.1\)\n',
        re.DOTALL,
    )
    replacement = (
        '\n    def test_protocol_no_longer_guesses_daily_reset_timing(self) -> None:\n'
        '        client = Tsun1097Client("192.0.2.10", 8899, 123456)\n'
        '        self.assertFalse(hasattr(client, "_stabilize_daily_energy"))\n'
    )
    source, count = pattern.subn(replacement, source, count=1)
    if count != 1:
        raise RuntimeError("old 1097 daily stabilization tests not found")
    path.write_text(source, encoding="utf-8")


def update_version_and_notes() -> None:
    manifest_path = ROOT / "custom_components/tsun_local/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("version") != "1.6.1-beta.4":
        raise RuntimeError(f"unexpected beta source version: {manifest.get('version')}")
    manifest["version"] = "1.6.1-beta.5"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    changelog_path = ROOT / "CHANGELOG.md"
    changelog = changelog_path.read_text(encoding="utf-8")
    marker = "## [1.6.1-beta.4] - 2026-09-07\n"
    if marker not in changelog:
        raise RuntimeError("CHANGELOG beta.4 marker not found")
    entry = textwrap.dedent(
        '''\
        ## [1.6.1-beta.5] - 2026-09-08

        ### Fixed

        - Make Home Assistant local midnight the only daily-energy day boundary for 1511, 02B0 and 1097.
        - Ignore logger/micro-inverter daily-counter resets at other times, including the PLAY2 / 1097 reset observed around 18:00.
        - Prefer monotonic `*_energy_total` deltas to keep `*_energy_today` continuous; use the raw daily counter only as a fallback.
        - Persist daily tracking references in Home Assistant state attributes so same-day HA restarts can recover production missed during the restart.
        - Preserve the 1511 / 02B0 behavior where yesterday's daily value can remain in hardware overnight and reset only when the inverter wakes.
        - Remove the 1097-specific "second lower sample means a real reset" heuristic.

        ### Recovery behavior

        - A restart a few minutes after midnight can recover from the total-energy reference written by the midnight rollover.
        - A same-day restart can recover missed energy from the monotonic total counter when beta.5 tracking metadata already exists.
        - A long HA outage spanning midnight cannot always be split mathematically between the two days; beta.5 uses the first fresh hardware daily value as a best-effort fallback instead of inventing a split.

        ### Validation

        - Add regression tests for 1511/02B0 sunrise reset, PLAY2/1097 18:00 reset, same-day HA restart, restart just after midnight and total-counter fallback.
        - Keep protocol register maps, read-only access, communication resilience, adaptive polling and logger Wi-Fi corrections unchanged.

        '''
    )
    changelog_path.write_text(changelog.replace(marker, entry + marker, 1), encoding="utf-8")

    notes_dir = ROOT / "docs/releases"
    notes_dir.mkdir(parents=True, exist_ok=True)
    (notes_dir / "1.6.1-beta.5.md").write_text(
        textwrap.dedent(
            '''\
            # TSUN Local 1.6.1-beta.5

            This beta harmonizes daily-energy handling across **1511**, **02B0** and **1097** after field tests showed that TSUN hardware does not always reset its own daily counter at Home Assistant midnight.

            ## What beta.5 changes

            - **Home Assistant local midnight is the only calendar-day boundary shown by TSUN Local.**
            - `*_energy_total` is the preferred monotonic reference used to advance `*_energy_today`.
            - A hardware daily-counter drop at another time is treated as a logger/inverter reset, not as a new Home Assistant day.
            - Tracking references are stored with the Home Assistant state so a same-day HA restart can recover missed energy from the total counter.

            ## Cases covered

            **MP3000 / 1511 and MX500 / 02B0:** if hardware keeps yesterday's daily value overnight and only resets when the inverter wakes, HA remains at 0 after midnight and starts the new day cleanly.

            **Sunology PLAY2 / 1097:** if the raw daily counter drops around 18:00, the displayed Home Assistant day stays continuous from total-energy deltas and does not start a false new day.

            ## Restart behavior

            - Same-day restart: recover missed energy from the monotonic total counter when beta.5 tracking metadata is available.
            - Restart just after midnight: use the persisted 00:00 total reference.
            - Long outage spanning midnight: exact allocation across midnight can be impossible; use the first fresh hardware daily value as best effort rather than inventing a split.

            ## Safety

            TSUN Local remains local and strictly read-only. This beta changes only Home Assistant-side interpretation and persistence of already-read energy counters.
            '''
        ),
        encoding="utf-8",
    )


def main() -> None:
    write_daily_energy_tracker()
    patch_sensor()
    patch_1097()
    write_tests()
    update_version_and_notes()
    print("TSUN Local 1.6.1-beta.5 source prepared")


if __name__ == "__main__":
    main()
