# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Verify sequential multi-device discovery without Home Assistant installed."""

from __future__ import annotations

import importlib.util
from ipaddress import IPv4Network
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch


ROOT = Path(__file__).parents[1]
PACKAGE = "tsun_local_config_flow_tests"


def _module(name: str, **attributes: object) -> ModuleType:
    module = ModuleType(name)
    for key, value in attributes.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


class _ConfigFlow:
    def __init_subclass__(cls, *, domain: str | None = None, **kwargs: object):
        super().__init_subclass__(**kwargs)

    async def async_set_unique_id(self, unique_id: str) -> None:
        self.unique_id = unique_id

    def _abort_if_unique_id_configured(self) -> None:
        pass

    def async_create_entry(
        self, *, title: str, data: dict[str, object], **kwargs: object
    ) -> dict[str, object]:
        return {"title": title, "data": data, **kwargs}


class _OptionsFlowWithReload:
    pass


class _FlowType:
    CONFIG_FLOW = "config_flow"


class _Selector:
    def __init__(self, *args: object, **kwargs: object) -> None:
        pass


def _load_config_flow() -> ModuleType:
    package = _module(PACKAGE)
    package.__path__ = [str(ROOT / "custom_components" / "tsun_local")]

    voluptuous = _module("voluptuous")
    voluptuous.Schema = lambda value: value
    voluptuous.Required = lambda key, **kwargs: key
    voluptuous.All = lambda *values: values
    voluptuous.Coerce = lambda value: value
    voluptuous.Range = lambda **kwargs: kwargs

    homeassistant = _module("homeassistant")
    config_entries = _module(
        "homeassistant.config_entries",
        ConfigEntry=object,
        ConfigFlow=_ConfigFlow,
        FlowType=_FlowType,
        OptionsFlowWithReload=_OptionsFlowWithReload,
        SOURCE_USER="user",
    )
    homeassistant.config_entries = config_entries

    components = _module("homeassistant.components")
    network = _module(
        "homeassistant.components.network",
        MDNS_TARGET_IP="224.0.0.251",
    )
    components.network = network
    homeassistant.components = components

    _module(
        "homeassistant.const",
        CONF_HOST="host",
        CONF_PORT="port",
    )
    _module(
        "homeassistant.core",
        HomeAssistant=object,
        callback=lambda function: function,
    )
    _module("homeassistant.data_entry_flow", FlowResult=dict)
    _module("homeassistant.exceptions", HomeAssistantError=RuntimeError)

    helpers = _module("homeassistant.helpers")
    selector = _module(
        "homeassistant.helpers.selector",
        NumberSelector=_Selector,
        NumberSelectorConfig=_Selector,
        NumberSelectorMode=type("NumberSelectorMode", (), {"BOX": "box"}),
        SelectOptionDict=lambda **kwargs: kwargs,
        SelectSelector=_Selector,
        SelectSelectorConfig=_Selector,
        SelectSelectorMode=type(
            "SelectSelectorMode", (), {"DROPDOWN": "dropdown"}
        ),
    )
    helpers.selector = selector

    _module(
        f"{PACKAGE}.const",
        CONF_DISCOVERY_NETWORK="discovery_network",
        CONF_ERROR_SCAN_INTERVAL="error_scan_interval",
        CONF_FAILURE_THRESHOLD="failure_threshold",
        CONF_INVERTER_SERIAL_NUMBER="inverter_serial_number",
        CONF_LOGGER_FIRMWARE_VERSION="logger_firmware_version",
        CONF_LOGGER_MAC_ADDRESS="logger_mac_address",
        CONF_LOGGER_SN="logger_sn",
        CONF_OFFLINE_SCAN_INTERVAL="offline_scan_interval",
        CONF_PROTOCOL="protocol",
        CONF_SCAN_INTERVAL="scan_interval",
        DEFAULT_ERROR_SCAN_INTERVAL=20,
        DEFAULT_FAILURE_THRESHOLD=3,
        DEFAULT_OFFLINE_SCAN_INTERVAL=300,
        DEFAULT_PORT=8899,
        DEFAULT_SCAN_INTERVAL=20,
        DOMAIN="tsun_local",
        MAX_ERROR_SCAN_INTERVAL=300,
        MAX_FAILURE_THRESHOLD=20,
        MAX_OFFLINE_SCAN_INTERVAL=3600,
        MAX_SCAN_INTERVAL=300,
        MIN_ERROR_SCAN_INTERVAL=10,
        MIN_FAILURE_THRESHOLD=1,
        MIN_OFFLINE_SCAN_INTERVAL=60,
        MIN_SCAN_INTERVAL=10,
    )
    _module(f"{PACKAGE}.coordinator", get_poll_lock=lambda hass: None)
    _module(
        f"{PACKAGE}.logger_web",
        async_read_logger_web_data=lambda *args: None,
    )
    _module(
        f"{PACKAGE}.protocols",
        DEFAULT_PROTOCOL="auto",
        FORCE_PROTOCOL="force_probe",
        SUPPORTED_PROTOCOLS=("1511", "1097", "02b0"),
        protocol_from_firmware=lambda firmware: next(
            (protocol for protocol in ("1511", "1097", "02b0") if protocol in str(firmware).lower()),
            None,
        ),
        create_protocol_client=lambda *args: None,
    )

    discovery_path = (
        ROOT / "custom_components" / "tsun_local" / "discovery.py"
    )
    discovery_spec = importlib.util.spec_from_file_location(
        f"{PACKAGE}.discovery", discovery_path
    )
    assert discovery_spec is not None and discovery_spec.loader is not None
    discovery = importlib.util.module_from_spec(discovery_spec)
    sys.modules[discovery_spec.name] = discovery
    discovery_spec.loader.exec_module(discovery)

    config_flow_path = (
        ROOT / "custom_components" / "tsun_local" / "config_flow.py"
    )
    flow_spec = importlib.util.spec_from_file_location(
        f"{PACKAGE}.config_flow", config_flow_path
    )
    assert flow_spec is not None and flow_spec.loader is not None
    flow_module = importlib.util.module_from_spec(flow_spec)
    sys.modules[flow_spec.name] = flow_module
    flow_spec.loader.exec_module(flow_module)
    return flow_module


CONFIG_FLOW = _load_config_flow()


class _FlowManager:
    def __init__(self, result: dict[str, str]) -> None:
        self.result = result
        self.calls: list[tuple[str, dict[str, object]]] = []

    async def async_init(
        self, domain: str, *, context: dict[str, object]
    ) -> dict[str, str]:
        self.calls.append((domain, context))
        return self.result


class _ConfigEntries:
    def __init__(self, result: dict[str, str]) -> None:
        self.flow = _FlowManager(result)


class _Hass:
    def __init__(self, result: dict[str, str]) -> None:
        self.config_entries = _ConfigEntries(result)


class DiscoveryContinuationTests(unittest.IsolatedAsyncioTestCase):
    """Protect the automatic transition to the next device search."""

    async def test_discovery_reuses_networks_from_configured_tsun_hosts(
        self,
    ) -> None:
        hass = SimpleNamespace(
            config_entries=SimpleNamespace(
                async_entries=lambda _domain: [
                    SimpleNamespace(data={"host": "198.51.100.42"})
                ]
            )
        )
        with patch.object(
            CONFIG_FLOW.network,
            "async_get_adapters",
            new=AsyncMock(
                return_value=[
                    {
                        "enabled": True,
                        "ipv4": [
                            {
                                "address": "192.0.2.20",
                                "network_prefix": 24,
                            }
                        ],
                    }
                ]
            ),
            create=True,
        ):
            networks = await CONFIG_FLOW._async_get_discovery_networks(hass)

        self.assertEqual(
            [str(network) for network in networks],
            ["192.0.2.0/24", "198.51.100.0/24"],
        )

    def test_polling_options_expose_three_intervals_and_failure_threshold(
        self,
    ) -> None:
        self.assertEqual(
            set(CONFIG_FLOW.OPTIONS_SCHEMA),
            {
                "scan_interval",
                "error_scan_interval",
                "offline_scan_interval",
                "failure_threshold",
            },
        )
        self.assertEqual(CONFIG_FLOW.DEFAULT_SCAN_INTERVAL, 20)
        self.assertEqual(CONFIG_FLOW.DEFAULT_ERROR_SCAN_INTERVAL, 20)
        self.assertEqual(CONFIG_FLOW.DEFAULT_OFFLINE_SCAN_INTERVAL, 300)
        self.assertEqual(CONFIG_FLOW.DEFAULT_FAILURE_THRESHOLD, 3)

    def test_logger_sn_is_hidden_until_automatic_detection_fails(self) -> None:
        automatic_schema = CONFIG_FLOW._connection_schema()
        fallback_schema = CONFIG_FLOW._connection_schema(
            request_logger_sn=True
        )

        automatic_keys = {str(key) for key in automatic_schema}
        fallback_keys = {str(key) for key in fallback_schema}
        self.assertNotIn("logger_sn", automatic_keys)
        self.assertIn("logger_sn", fallback_keys)

    async def test_automatically_detected_logger_sn_is_saved(self) -> None:
        flow = CONFIG_FLOW.TsunConfigFlow()
        flow.hass = object()
        with (
            patch.object(
                CONFIG_FLOW,
                "async_read_logger_web_data",
                new=AsyncMock(
                    return_value=SimpleNamespace(
                        logger_sn=1234567890,
                        inverter_serial_number="TESTINVERTER0001",
                        firmware_version="LSW_TEST_1511_1.0",
                        mac_address="02:00:00:00:00:01",
                    )
                ),
            ),
            patch.object(
                CONFIG_FLOW,
                "_validate_input",
                new=AsyncMock(return_value="1511"),
            ),
        ):
            result = await flow._async_create_device(
                {"host": "192.0.2.10", "port": 8899}
            )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["data"]["logger_sn"], 1234567890)
        self.assertEqual(result["data"]["protocol"], "1511")
        self.assertEqual(
            result["data"]["logger_firmware_version"], "LSW_TEST_1511_1.0"
        )
        self.assertEqual(
            result["data"]["logger_mac_address"], "02:00:00:00:00:01"
        )
        self.assertEqual(
            result["data"]["inverter_serial_number"], "TESTINVERTER0001"
        )
        self.assertEqual(flow.unique_id, "1234567890")

    async def test_manual_logger_sn_is_requested_when_detection_fails(
        self,
    ) -> None:
        flow = CONFIG_FLOW.TsunConfigFlow()
        flow.hass = object()
        with patch.object(
            CONFIG_FLOW,
            "async_read_logger_web_data",
            new=AsyncMock(
                return_value=SimpleNamespace(
                    logger_sn=None,
                    inverter_serial_number=None,
                    firmware_version="LSW_TEST_1511_1.0",
                    mac_address=None,
                )
            ),
        ):
            result = await flow._async_create_device(
                {"host": "192.0.2.10", "port": 8899}
            )

        self.assertEqual(result, "cannot_detect_logger_sn")
        self.assertTrue(flow._logger_sn_required)

    async def test_detected_sn_can_be_corrected_after_invalid_response(
        self,
    ) -> None:
        flow = CONFIG_FLOW.TsunConfigFlow()
        flow.hass = object()
        with (
            patch.object(
                CONFIG_FLOW,
                "async_read_logger_web_data",
                new=AsyncMock(
                    return_value=SimpleNamespace(
                        logger_sn=1234567890,
                        inverter_serial_number=None,
                        firmware_version="LSW_TEST_1511_1.0",
                        mac_address=None,
                    )
                ),
            ),
            patch.object(
                CONFIG_FLOW,
                "_validate_input",
                new=AsyncMock(side_effect=ValueError),
            ),
        ):
            result = await flow._async_create_device(
                {"host": "192.0.2.10", "port": 8899}
            )

        self.assertEqual(result, "invalid_response")
        self.assertTrue(flow._logger_sn_required)
        self.assertEqual(flow._detected_logger_sn, 1234567890)

    async def test_prepares_next_flow_with_pending_host_excluded(self) -> None:
        flow = CONFIG_FLOW.TsunConfigFlow()
        flow.hass = _Hass({"type": "form", "flow_id": "next-flow"})
        flow._discovery_networks = [IPv4Network("192.0.2.0/24")]
        flow._discovery_port = 8899
        flow._excluded_hosts = {"192.0.2.10"}

        result = await flow._async_prepare_next_discovery("192.0.2.11")

        self.assertEqual(result, (_FlowType.CONFIG_FLOW, "next-flow"))
        _, context = flow.hass.config_entries.flow.calls[0]
        self.assertEqual(context["source"], "tsun_continue_discovery")
        self.assertEqual(
            context["tsun_discovery_networks"], ["192.0.2.0/24"]
        )
        self.assertEqual(context["tsun_discovery_port"], 8899)
        self.assertEqual(
            context["tsun_excluded_hosts"],
            ["192.0.2.10", "192.0.2.11"],
        )

    async def test_continuation_starts_only_after_entry_creation(self) -> None:
        flow = CONFIG_FLOW.TsunConfigFlow()
        flow.hass = _Hass({"type": "form", "flow_id": "next-flow"})
        flow._discovery_networks = [IPv4Network("192.0.2.0/24")]
        flow._discovery_port = 8899
        flow._continue_discovery_host = "192.0.2.11"

        result = await flow.async_on_create_entry(
            {"type": "create_entry", "data": {}}
        )

        self.assertEqual(
            result["next_flow"], (_FlowType.CONFIG_FLOW, "next-flow")
        )
        self.assertEqual(len(flow.hass.config_entries.flow.calls), 1)

    async def test_stops_when_continuation_has_no_form(self) -> None:
        flow = CONFIG_FLOW.TsunConfigFlow()
        flow.hass = _Hass({"type": "abort", "flow_id": "stale-flow"})

        self.assertIsNone(
            await flow._async_prepare_next_discovery("192.0.2.11")
        )

    async def test_dedicated_continuation_source_restarts_discovery(
        self,
    ) -> None:
        flow = CONFIG_FLOW.TsunConfigFlow()
        flow.context = {
            "tsun_continue_discovery": True,
            "tsun_discovery_networks": ["198.51.100.0/24"],
            "tsun_discovery_port": 8899,
            "tsun_excluded_hosts": ["198.51.100.20"],
        }
        flow.async_step_user = AsyncMock(
            return_value={"type": "form", "step_id": "discover"}
        )

        result = await flow.async_step_tsun_continue_discovery()

        self.assertEqual(result["step_id"], "discover")
        flow.async_step_user.assert_awaited_once_with()

    async def test_continuation_restarts_discovery_on_same_networks(self) -> None:
        flow = CONFIG_FLOW.TsunConfigFlow()
        flow.context = {
            "tsun_continue_discovery": True,
            "tsun_discovery_networks": ["198.51.100.0/24"],
            "tsun_discovery_port": 18899,
            "tsun_excluded_hosts": ["198.51.100.20"],
        }
        calls = 0

        async def _discover() -> dict[str, str]:
            nonlocal calls
            calls += 1
            return {"type": "form", "step_id": "discover"}

        flow.async_step_discover = _discover
        result = await flow.async_step_user()

        self.assertEqual(result["step_id"], "discover")
        self.assertEqual(calls, 1)
        self.assertEqual(flow._discovery_port, 18899)
        self.assertEqual(
            flow._discovery_networks,
            [IPv4Network("198.51.100.0/24")],
        )
        self.assertEqual(flow._excluded_hosts, {"198.51.100.20"})


if __name__ == "__main__":
    unittest.main()
