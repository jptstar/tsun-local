# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Verify communication-failure tolerance without Home Assistant installed."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import importlib.util
from pathlib import Path
import sys
from types import ModuleType
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
        self.data: dict[str, object] = {}
        self.update_interval = update_interval


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


class CoordinatorFailureTests(unittest.IsolatedAsyncioTestCase):
    """Protect the three-attempt availability threshold."""

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

    async def test_success_immediately_resets_failure_state(self) -> None:
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


if __name__ == "__main__":
    unittest.main()
