# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Verify communication-failure tolerance without Home Assistant installed."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest


ROOT = Path(__file__).parents[1]
PACKAGE = "tsun_local_coordinator_tests"


def _module(name: str, **attributes: object) -> ModuleType:
    module = ModuleType(name)
    for key, value in attributes.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


class _DataUpdateCoordinator:
    @classmethod
    def __class_getitem__(cls, item: object) -> type[_DataUpdateCoordinator]:
        return cls

    def __init__(
        self,
        hass: object,
        logger: object,
        *,
        name: str,
        config_entry: object,
        update_interval: object,
    ) -> None:
        self.hass = hass
        self.data: dict[str, object] = {}
        self.update_interval = update_interval
        self.listener_updates = 0

    def async_update_listeners(self) -> None:
        self.listener_updates += 1


class _ReadResult:
    def __init__(
        self,
        measurements: dict[str, object],
        duration_ms: int = 25,
        blocks_ok: int = 3,
    ) -> None:
        self.measurements = measurements
        self.duration_ms = duration_ms
        self.blocks_ok = blocks_ok


def _load_coordinator() -> ModuleType:
    package = _module(PACKAGE)
    package.__path__ = [str(ROOT / "custom_components" / "tsun_local")]

    homeassistant = _module("homeassistant")
    _module("homeassistant.config_entries", ConfigEntry=object)
    _module("homeassistant.core", HomeAssistant=object)
    helpers = _module("homeassistant.helpers")
    update_coordinator = _module(
        "homeassistant.helpers.update_coordinator",
        DataUpdateCoordinator=_DataUpdateCoordinator,
    )
    helpers.update_coordinator = update_coordinator
    homeassistant.helpers = helpers

    util = _module("homeassistant.util")
    dt = _module(
        "homeassistant.util.dt",
        utcnow=lambda: datetime(2026, 8, 11, tzinfo=timezone.utc),
    )
    util.dt = dt
    homeassistant.util = util

    _module(
        f"{PACKAGE}.const",
        CONF_ADAPTIVE_POLLING="adaptive_polling",
        CONF_LOGGER_SN="logger_sn",
        DEFAULT_ADAPTIVE_POLLING=False,
        DOMAIN="tsun_local",
    )
    _module(
        f"{PACKAGE}.protocols",
        TsunProtocolClient=object,
        TsunReadResult=_ReadResult,
    )
    protocol_package = _module(f"{PACKAGE}.protocols.ap")
    protocol_package.safe_error_details = lambda error: {
        "type": type(error).__name__
    }

    path = ROOT / "custom_components" / "tsun_local" / "coordinator.py"
    spec = importlib.util.spec_from_file_location(
        f"{PACKAGE}.coordinator", path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


COORDINATOR = _load_coordinator()


class _Client:
    def __init__(self, responses: list[object]) -> None:
        self.responses = responses
        self.diagnostic_trace: list[dict[str, object]] = []

    async def async_read_all(self) -> _ReadResult:
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class _Hass:
    def __init__(self) -> None:
        self.data: dict[str, object] = {}


def _entry(
    logger_sn: int = 123456,
    *,
    adaptive_polling: bool = False,
) -> SimpleNamespace:
    return SimpleNamespace(
        data={"logger_sn": logger_sn},
        options={"adaptive_polling": adaptive_polling},
    )


class CoordinatorFailureTests(unittest.IsolatedAsyncioTestCase):
    """Protect fixed and adaptive communication-failure handling."""

    def test_builds_privacy_safe_inverter_serial_prefix(self) -> None:
        self.assertEqual(
            COORDINATOR.inverter_serial_prefix("Y47E8439081E01E5"), "Y47"
        )
        self.assertEqual(
            COORDINATOR.inverter_serial_prefix(" y47-abc "), "Y47"
        )
        self.assertIsNone(COORDINATOR.inverter_serial_prefix(None))
        self.assertIsNone(COORDINATOR.inverter_serial_prefix("Y4"))

    def test_poll_locks_are_isolated_per_logger(self) -> None:
        hass = _Hass()
        first = COORDINATOR.get_poll_lock(hass, 111)
        same = COORDINATOR.get_poll_lock(hass, 111)
        second = COORDINATOR.get_poll_lock(hass, 222)
        self.assertIs(first, same)
        self.assertIsNot(first, second)

    async def test_logger_metadata_is_exposed_and_survives_failures(self) -> None:
        client = _Client([_ReadResult({"ac_power": 400}), OSError("one")])
        coordinator = COORDINATOR.TsunCoordinator(
            object(),
            object(),
            client,
            20,
            25,
            300,
            3,
            asyncio.Lock(),
            "LSW_TEST_1.0",
            "02:00:00:00:00:01",
            "TESTINVERTER0001",
            "5393:Tengsheng_titan",
            57,
        )

        first = await coordinator._async_update_data()
        coordinator.data = first
        second = await coordinator._async_update_data()

        for data in (first, second):
            self.assertEqual(
                data["logger_firmware_version"], "LSW_TEST_1.0"
            )
            self.assertEqual(
                data["logger_mac_address"], "02:00:00:00:00:01"
            )
            self.assertEqual(
                data["inverter_serial_number"], "TESTINVERTER0001"
            )
            self.assertEqual(
                data["logger_raw_profile"], "5393:Tengsheng_titan"
            )
            self.assertEqual(data["logger_wifi_signal"], 57)
        self.assertEqual(coordinator.inverter_serial_prefix, "TES")
        self.assertEqual(
            coordinator.diagnostic_summary["inverter_serial_prefix"], "TES"
        )
        self.assertEqual(
            coordinator.diagnostic_summary["online_basis"],
            "protocol_poll_failure_threshold",
        )
        self.assertFalse(coordinator.diagnostic_summary["wifi_controls_online"])

    async def test_refreshed_serial_updates_log_prefix(self) -> None:
        client = _Client([_ReadResult({"ac_power": 400})])
        coordinator = COORDINATOR.TsunCoordinator(
            object(), object(), client, 20, 25, 300, 3, asyncio.Lock()
        )
        self.assertIsNone(coordinator.inverter_serial_prefix)
        changed = coordinator.async_update_logger_metadata(
            {"inverter_serial_number": "Y47E8439081E01E5"}
        )
        self.assertTrue(changed)
        self.assertEqual(coordinator.inverter_serial_prefix, "Y47")

    async def test_warning_uses_prefix_without_full_serial(self) -> None:
        full_serial = "Y47E8439081E01E5"
        client = _Client([OSError("one"), OSError("two"), OSError("three")])
        coordinator = COORDINATOR.TsunCoordinator(
            object(),
            object(),
            client,
            20,
            25,
            300,
            3,
            asyncio.Lock(),
            inverter_serial_number=full_serial,
        )
        coordinator._online = True

        with self.assertLogs(COORDINATOR._LOGGER.name, level="WARNING") as captured:
            for _ in range(3):
                coordinator.data = await coordinator._async_update_data()

        message = "\n".join(captured.output)
        self.assertIn("TSUN device [Y47] is unavailable", message)
        self.assertNotIn(full_serial, message)

    async def test_refreshed_logger_metadata_survives_failed_poll(self) -> None:
        client = _Client([OSError("one")])
        coordinator = COORDINATOR.TsunCoordinator(
            object(),
            object(),
            client,
            20,
            25,
            300,
            3,
            asyncio.Lock(),
            logger_wifi_signal=40,
        )
        coordinator._online = True
        coordinator.data = {
            "logger_wifi_signal": 40,
            "communication_online": True,
        }

        changed = coordinator.async_update_logger_metadata(
            {
                "logger_wifi_signal": 63,
                "logger_raw_profile": "688:Tengsheng_G3",
            }
        )
        self.assertTrue(changed)
        self.assertEqual(coordinator.data["logger_wifi_signal"], 63)
        self.assertEqual(
            coordinator.data["logger_raw_profile"], "688:Tengsheng_G3"
        )
        self.assertEqual(coordinator.listener_updates, 1)

        failed = await coordinator._async_update_data()
        self.assertEqual(failed["logger_wifi_signal"], 63)
        self.assertEqual(
            failed["logger_raw_profile"], "688:Tengsheng_G3"
        )

    async def test_marks_device_offline_on_third_consecutive_failure(self) -> None:
        client = _Client([OSError("one"), OSError("two"), OSError("three")])
        coordinator = COORDINATOR.TsunCoordinator(
            object(), object(), client, 20, 25, 300, 3, asyncio.Lock()
        )
        coordinator._online = True
        coordinator._last_success = datetime(
            2026, 8, 11, tzinfo=timezone.utc
        )
        coordinator.data = {
            "ac_power": 400,
            "communication_online": True,
        }

        first = await coordinator._async_update_data()
        coordinator.data = first
        self.assertTrue(first["communication_online"])
        self.assertEqual(first["communication_failures"], 1)
        self.assertEqual(first["ac_power"], 400)
        self.assertEqual(coordinator.update_interval.total_seconds(), 25)

        second = await coordinator._async_update_data()
        coordinator.data = second
        self.assertTrue(second["communication_online"])
        self.assertEqual(second["communication_failures"], 2)
        self.assertEqual(coordinator.update_interval.total_seconds(), 25)

        third = await coordinator._async_update_data()
        coordinator.data = third
        self.assertFalse(third["communication_online"])
        self.assertEqual(third["communication_failures"], 3)
        self.assertEqual(coordinator.update_interval.total_seconds(), 300)
        self.assertEqual(
            coordinator.diagnostic_summary["failure_threshold"], 3
        )
        self.assertEqual(
            coordinator.diagnostic_summary["normal_polling_seconds"], 20
        )
        self.assertEqual(
            coordinator.diagnostic_summary["error_polling_seconds"], 25
        )
        self.assertEqual(
            coordinator.diagnostic_summary["offline_polling_seconds"], 300
        )

    async def test_success_immediately_resets_fixed_failure_state(self) -> None:
        client = _Client(
            [
                OSError("one"),
                OSError("two"),
                OSError("three"),
                _ReadResult({"ac_power": 425}),
            ]
        )
        coordinator = COORDINATOR.TsunCoordinator(
            object(), object(), client, 20, 25, 300, 3, asyncio.Lock()
        )
        coordinator._online = True

        for _ in range(3):
            coordinator.data = await coordinator._async_update_data()

        restored = await coordinator._async_update_data()
        self.assertTrue(restored["communication_online"])
        self.assertEqual(restored["communication_failures"], 0)
        self.assertEqual(restored["ac_power"], 425)
        self.assertEqual(coordinator.update_interval.total_seconds(), 20)

    async def test_custom_failure_threshold_controls_offline_transition(
        self,
    ) -> None:
        client = _Client([OSError("one"), OSError("two")])
        coordinator = COORDINATOR.TsunCoordinator(
            object(), object(), client, 20, 20, 300, 2, asyncio.Lock()
        )
        coordinator._online = True

        first = await coordinator._async_update_data()
        coordinator.data = first
        self.assertTrue(first["communication_online"])
        self.assertEqual(coordinator.update_interval.total_seconds(), 20)

        second = await coordinator._async_update_data()
        self.assertFalse(second["communication_online"])
        self.assertEqual(coordinator.update_interval.total_seconds(), 300)

    async def test_adaptive_polling_backs_off_and_matches_online_state(self) -> None:
        client = _Client([OSError(str(index)) for index in range(1, 6)])
        coordinator = COORDINATOR.TsunCoordinator(
            object(),
            object(),
            client,
            20,
            20,
            300,
            3,
            asyncio.Lock(),
            adaptive_polling=True,
        )
        coordinator._online = True

        expected_intervals = [20, 30, 300, 300, 300]
        expected_states = [
            "degraded",
            "degraded",
            "offline",
            "offline",
            "offline",
        ]
        expected_online = [True, True, False, False, False]
        for interval, state, online in zip(
            expected_intervals,
            expected_states,
            expected_online,
        ):
            coordinator.data = await coordinator._async_update_data()
            self.assertEqual(
                coordinator.update_interval.total_seconds(), interval
            )
            self.assertEqual(
                coordinator.data["adaptive_polling_state"], state
            )
            self.assertEqual(
                coordinator.data["communication_online"], online
            )

        self.assertEqual(
            coordinator.diagnostic_summary["adaptive_backoff_events"], 2
        )
        self.assertEqual(
            coordinator.diagnostic_summary["poll_failures_total"], 5
        )

    async def test_adaptive_polling_recovers_progressively(self) -> None:
        failures = [OSError(str(index)) for index in range(1, 6)]
        successes = [_ReadResult({"ac_power": 425}) for _ in range(5)]
        coordinator = COORDINATOR.TsunCoordinator(
            object(),
            object(),
            _Client([*failures, *successes]),
            20,
            20,
            300,
            3,
            asyncio.Lock(),
            adaptive_polling=True,
        )
        coordinator._online = True

        for _ in failures:
            coordinator.data = await coordinator._async_update_data()
        self.assertEqual(coordinator.update_interval.total_seconds(), 300)
        self.assertFalse(coordinator.data["communication_online"])

        expected_intervals = [120, 60, 30, 20, 20]
        expected_states = [
            "recovery",
            "recovery",
            "recovery",
            "recovery",
            "normal",
        ]
        for interval, state in zip(expected_intervals, expected_states):
            coordinator.data = await coordinator._async_update_data()
            self.assertTrue(coordinator.data["communication_online"])
            self.assertEqual(coordinator.data["communication_failures"], 0)
            self.assertEqual(
                coordinator.update_interval.total_seconds(), interval
            )
            self.assertEqual(
                coordinator.data["adaptive_polling_state"], state
            )

        self.assertEqual(
            coordinator.diagnostic_summary["poll_successes_total"], 5
        )

    async def test_low_wifi_does_not_slow_successful_adaptive_polling(self) -> None:
        coordinator = COORDINATOR.TsunCoordinator(
            object(),
            object(),
            _Client([_ReadResult({"ac_power": 425})]),
            20,
            20,
            300,
            3,
            asyncio.Lock(),
            logger_wifi_signal=8,
            adaptive_polling=True,
        )
        result = await coordinator._async_update_data()
        self.assertTrue(result["communication_online"])
        self.assertEqual(result["adaptive_polling_state"], "normal")
        self.assertEqual(result["adaptive_polling_interval"], 20)

    async def test_zero_wifi_is_diagnostic_reason_not_extra_backoff(self) -> None:
        coordinator = COORDINATOR.TsunCoordinator(
            object(),
            object(),
            _Client([OSError("one")]),
            20,
            20,
            300,
            3,
            asyncio.Lock(),
            logger_wifi_signal=0,
            adaptive_polling=True,
        )
        coordinator._online = True
        result = await coordinator._async_update_data()
        self.assertTrue(result["communication_online"])
        self.assertEqual(result["adaptive_polling_reason"], "wifi_signal_zero")
        self.assertEqual(result["adaptive_polling_interval"], 20)

    async def test_entry_options_enable_adaptive_mode_and_per_logger_lock(self) -> None:
        hass = _Hass()
        entry = _entry(999, adaptive_polling=True)
        coordinator = COORDINATOR.TsunCoordinator(
            hass,
            entry,
            _Client([_ReadResult({"ac_power": 425})]),
            20,
            20,
            300,
            3,
            asyncio.Lock(),
        )
        self.assertTrue(coordinator.adaptive_polling_enabled)
        self.assertIs(
            coordinator.poll_lock,
            COORDINATOR.get_poll_lock(hass, 999),
        )


if __name__ == "__main__":
    unittest.main()
