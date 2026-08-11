# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Verify sequential multi-device discovery without Home Assistant installed."""

from __future__ import annotations

import importlib.util
from ipaddress import IPv4Network
from pathlib import Path
import sys
from types import ModuleType
import unittest


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
        f"{PACKAGE}.protocols",
        DEFAULT_PROTOCOL="auto",
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

    async def test_prepares_next_flow_with_pending_host_excluded(self) -> None:
        flow = CONFIG_FLOW.TsunConfigFlow()
        flow.hass = _Hass({"flow_id": "next-flow"})
        flow._discovery_networks = [IPv4Network("192.0.2.0/24")]
        flow._discovery_port = 8899
        flow._excluded_hosts = {"192.0.2.10"}

        result = await flow._async_prepare_next_discovery("192.0.2.11")

        self.assertEqual(result, (_FlowType.CONFIG_FLOW, "next-flow"))
        _, context = flow.hass.config_entries.flow.calls[0]
        self.assertEqual(context["source"], "user")
        self.assertEqual(
            context["tsun_discovery_networks"], ["192.0.2.0/24"]
        )
        self.assertEqual(context["tsun_discovery_port"], 8899)
        self.assertEqual(
            context["tsun_excluded_hosts"],
            ["192.0.2.10", "192.0.2.11"],
        )

    async def test_stops_when_continuation_has_no_form(self) -> None:
        flow = CONFIG_FLOW.TsunConfigFlow()
        flow.hass = _Hass({"type": "abort"})

        self.assertIsNone(
            await flow._async_prepare_next_discovery("192.0.2.11")
        )

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
