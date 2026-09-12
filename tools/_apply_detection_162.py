#!/usr/bin/env python3
"""One-time helper to finalize the 1.6.2 protocol detection branch."""

from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"{label} not found")
    return text.replace(old, new, 1)


def replace_section(text: str, start: str, end: str, replacement: str, label: str) -> str:
    try:
        left = text.index(start)
        right = text.index(end, left)
    except ValueError as err:
        raise SystemExit(f"{label} markers not found") from err
    return text[:left] + replacement + text[right:]


def patch_config_flow() -> None:
    path = Path("custom_components/tsun_local/config_flow.py")
    text = path.read_text(encoding="utf-8")

    text = replace_once(
        text,
        '''from .protocols import (
    DEFAULT_PROTOCOL,
    FORCE_PROTOCOL,
    SUPPORTED_PROTOCOLS,
    create_protocol_client,
    protocol_from_firmware,
)''',
        '''from .protocols import (
    DEFAULT_PROTOCOL,
    DETECTION_MIN_SCORE,
    FORCE_PROTOCOL,
    SUPPORTED_PROTOCOLS,
    create_protocol_client,
    score_protocol_candidate,
)''',
        "protocol import block",
    )

    text = replace_once(
        text,
        '''async def _validate_input(hass: HomeAssistant, data: dict[str, Any]) -> str:
    client = create_protocol_client(
        data.get(CONF_PROTOCOL, DEFAULT_PROTOCOL),
        data[CONF_HOST],
        data[CONF_PORT],
        data[CONF_LOGGER_SN],
    )
    async with get_poll_lock(hass, data[CONF_LOGGER_SN]):
        await client.async_read_all()
    return client.protocol_name
''',
        '''async def _validate_input(hass: HomeAssistant, data: dict[str, Any]) -> str:
    requested_protocol = str(
        data.get(CONF_PROTOCOL, DEFAULT_PROTOCOL)
    ).lower()
    client = create_protocol_client(
        requested_protocol,
        data[CONF_HOST],
        data[CONF_PORT],
        data[CONF_LOGGER_SN],
    )
    async with get_poll_lock(hass, data[CONF_LOGGER_SN]):
        result = await client.async_read_all()

    # An explicit family remains authoritative, but it must validate reliably.
    # Manual mode never falls back silently to another protocol.
    if requested_protocol in SUPPORTED_PROTOCOLS:
        assessment = score_protocol_candidate(requested_protocol, result)
        if not assessment.hard_valid or assessment.score < DETECTION_MIN_SCORE:
            raise ValueError(
                f"Protocol {requested_protocol} did not validate reliably"
            )
    return client.protocol_name


def _normalize_protocol_selection(value: str) -> str:
    """Translate UI protocol choices to runtime protocol modes."""
    normalized = value.lower()
    if normalized == _FORCE_PROTOCOL_DETECTION:
        return FORCE_PROTOCOL
    if normalized in SUPPORTED_PROTOCOLS:
        return normalized
    return DEFAULT_PROTOCOL
''',
        "validation block",
    )

    text = replace_once(
        text,
        '''RECONFIGURE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=65535)
        ),
    }
)
''',
        '''def _reconfigure_schema(current_protocol: str) -> vol.Schema:
    """Allow connection details and protocol detection mode to be retested."""
    default_protocol = (
        current_protocol
        if current_protocol in SUPPORTED_PROTOCOLS
        else DEFAULT_PROTOCOL
    )
    return vol.Schema(
        {
            vol.Required(CONF_HOST): str,
            vol.Required(CONF_PORT): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=65535)
            ),
            vol.Required(
                CONF_PROTOCOL, default=default_protocol
            ): SelectSelector(
                SelectSelectorConfig(
                    translation_key="protocol",
                    options=[
                        DEFAULT_PROTOCOL,
                        _FORCE_PROTOCOL_DETECTION,
                        *SUPPORTED_PROTOCOLS,
                    ],
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
        }
    )
''',
        "reconfigure schema",
    )

    text = replace_once(
        text,
        '''        if detection_mode == _FORCE_PROTOCOL_DETECTION:
            entry_input[CONF_PROTOCOL] = FORCE_PROTOCOL
        elif detection_mode in SUPPORTED_PROTOCOLS:
            entry_input[CONF_PROTOCOL] = detection_mode
        else:
            firmware_protocol = protocol_from_firmware(
                self._logger_firmware_version
            )
            if firmware_protocol is None:
                return "unknown_firmware"
            entry_input[CONF_PROTOCOL] = firmware_protocol
''',
        '''        # Auto keeps firmware as a priority hint inside TsunAutoClient.
        # Force ignores that hint; explicit families remain strict.
        entry_input[CONF_PROTOCOL] = _normalize_protocol_selection(detection_mode)
''',
        "initial protocol selection",
    )

    text = replace_once(
        text,
        '''        if user_input is not None:
            updated_data = {**entry.data, **user_input}
            try:
                await _validate_input(self.hass, updated_data)
            except (TimeoutError, asyncio.TimeoutError):
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "invalid_response"
            else:
                await self.async_set_unique_id(str(entry.data[CONF_LOGGER_SN]))
                self._abort_if_unique_id_mismatch()
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates=user_input,
                    reload_even_if_entry_is_unchanged=False,
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                RECONFIGURE_SCHEMA, entry.data
            ),
            errors=errors,
        )''',
        '''        if user_input is not None:
            requested_protocol = _normalize_protocol_selection(
                str(
                    user_input.get(
                        CONF_PROTOCOL,
                        entry.data.get(CONF_PROTOCOL, DEFAULT_PROTOCOL),
                    )
                )
            )
            updated_data = {
                **entry.data,
                **user_input,
                CONF_PROTOCOL: requested_protocol,
            }
            try:
                detected_protocol = await _validate_input(self.hass, updated_data)
            except (TimeoutError, asyncio.TimeoutError, ConnectionError, OSError):
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "invalid_response"
            else:
                await self.async_set_unique_id(str(entry.data[CONF_LOGGER_SN]))
                self._abort_if_unique_id_mismatch()
                # Transactional reconfigure: only persist after validation.
                data_updates = {
                    **user_input,
                    CONF_PROTOCOL: detected_protocol,
                }
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates=data_updates,
                    reload_even_if_entry_is_unchanged=False,
                )

        current_protocol = str(
            entry.data.get(CONF_PROTOCOL, DEFAULT_PROTOCOL)
        ).lower()
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                _reconfigure_schema(current_protocol), entry.data
            ),
            errors=errors,
        )''',
        "reconfigure logic",
    )
    path.write_text(text, encoding="utf-8")


def patch_protocol_tests() -> None:
    path = Path("tests/test_protocols.py")
    source = path.read_text(encoding="utf-8")

    source = replace_section(
        source,
        "    async def test_selects_working_protocol_and_reuses_it(self) -> None:",
        "    def test_extracts_protocol_from_known_firmware_names(self) -> None:",
        '''    async def test_selects_working_protocol_and_reuses_it(self) -> None:
        attempts: list[str] = []

        class FakeClient:
            model = "Test"
            pv_count = 1
            measurement_keys = frozenset({"ac_power"})

            def __init__(self, protocol_name: str, succeeds: bool) -> None:
                self.protocol_name = protocol_name
                self.succeeds = succeeds
                self.reads = 0

            @property
            def diagnostic_trace(self):
                return ({"protocol": self.protocol_name, "stage": "complete"},)

            async def async_read_all(self):
                self.reads += 1
                if not self.succeeds:
                    raise RuntimeError("wrong protocol")
                return PROTOCOLS.TsunReadResult(
                    measurements={
                        "ac_power": 0,
                        "rated_power": 800,
                        "max_designed_power": 800,
                    },
                    duration_ms=1,
                    blocks_ok=2,
                )

        working_client = FakeClient("02b0", True)

        def create_client(protocol_name: str, *_args):
            attempts.append(protocol_name)
            if protocol_name in {"1511", "1097"}:
                return FakeClient(protocol_name, False)
            return working_client

        with (
            patch.object(
                PROTOCOLS,
                "async_detect_protocol_from_firmware",
                new=AsyncMock(return_value=None),
            ),
            patch.object(PROTOCOLS, "_create_specific_client", new=create_client),
        ):
            client = PROTOCOLS.TsunAutoClient("192.0.2.10", 8899, 123456)
            await client.async_read_all()
            await client.async_read_all()

        self.assertEqual(attempts, ["1511", "1097", "02b0"])
        self.assertEqual(client.protocol_name, "02b0")
        self.assertEqual(working_client.reads, 2)

''',
        "auto selection test",
    )

    source = replace_section(
        source,
        "    async def test_forced_probe_ignores_firmware_hint(self) -> None:",
        "    async def test_firmware_hint_prevents_blind_protocol_probing(self) -> None:",
        '''    async def test_forced_probe_ignores_firmware_hint(self) -> None:
        attempts: list[str] = []

        class FakeClient:
            model = "Test"
            pv_count = 1
            measurement_keys = frozenset()
            diagnostic_trace = ()

            def __init__(self, protocol_name: str) -> None:
                self.protocol_name = protocol_name

            async def async_read_all(self):
                if self.protocol_name != "1097":
                    raise RuntimeError("wrong protocol")
                return PROTOCOLS.TsunReadResult(
                    measurements={"rated_power": 800, "max_designed_power": 800},
                    duration_ms=1,
                    blocks_ok=3,
                )

        def create_client(protocol_name: str, *_args):
            attempts.append(protocol_name)
            return FakeClient(protocol_name)

        with (
            patch.object(
                PROTOCOLS,
                "async_detect_protocol_from_firmware",
                new=AsyncMock(return_value="02b0"),
            ),
            patch.object(PROTOCOLS, "_create_specific_client", new=create_client),
        ):
            client = PROTOCOLS.create_protocol_client(
                PROTOCOLS.FORCE_PROTOCOL, "192.0.2.10", 8899, 123456
            )
            await client.async_read_all()

        self.assertEqual(attempts, ["1511", "1097", "02b0"])
        self.assertEqual(client.protocol_name, "1097")

''',
        "force probe test",
    )

    source = replace_section(
        source,
        "    async def test_firmware_hint_prevents_blind_protocol_probing(self) -> None:",
        "\nclass DiscoveryTests",
        '''    async def test_firmware_hint_is_priority_not_a_lock(self) -> None:
        attempts: list[str] = []

        class FakeClient:
            model = "Test"
            pv_count = 1
            measurement_keys = frozenset()
            diagnostic_trace = ()

            def __init__(self, protocol_name: str) -> None:
                self.protocol_name = protocol_name

            async def async_read_all(self):
                if self.protocol_name != "02b0":
                    raise RuntimeError("wrong protocol")
                return PROTOCOLS.TsunReadResult(
                    measurements={"rated_power": 800, "max_designed_power": 800},
                    duration_ms=1,
                    blocks_ok=2,
                )

        def create_client(protocol_name: str, *_args):
            attempts.append(protocol_name)
            return FakeClient(protocol_name)

        with (
            patch.object(
                PROTOCOLS,
                "async_detect_protocol_from_firmware",
                new=AsyncMock(return_value="02b0"),
            ),
            patch.object(PROTOCOLS, "_create_specific_client", new=create_client),
        ):
            client = PROTOCOLS.TsunAutoClient("192.0.2.10", 8899, 123456)
            await client.async_read_all()

        self.assertEqual(attempts, ["02b0", "1511", "1097"])
        self.assertEqual(client.protocol_name, "02b0")


''',
        "firmware priority test",
    )
    path.write_text(source, encoding="utf-8")


def write_detection_tests() -> None:
    Path("tests/test_protocol_detection_162.py").write_text(
        '''# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Regression tests for conservative 1.6.2 protocol detection."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import AsyncMock, patch

PROTOCOLS_PATH = Path(__file__).parents[1] / "custom_components" / "tsun_local" / "protocols"
SPEC = importlib.util.spec_from_file_location(
    "tsun_local_protocol_detection_tests",
    PROTOCOLS_PATH / "__init__.py",
    submodule_search_locations=[str(PROTOCOLS_PATH)],
)
assert SPEC is not None and SPEC.loader is not None
PROTOCOLS = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PROTOCOLS
SPEC.loader.exec_module(PROTOCOLS)


def confident_result(protocol_name: str):
    blocks = {"1511": 3, "1097": 3, "02b0": 2}[protocol_name]
    return PROTOCOLS.TsunReadResult(
        measurements={
            "rated_power": 800,
            "max_designed_power": 800,
            "ac_voltage": 0,
            "ac_frequency": 0,
            "ac_power": 0,
            "ac_energy_total": 0,
        },
        duration_ms=1,
        blocks_ok=blocks,
    )


class DetectionScoringTests(unittest.TestCase):
    def test_night_zero_production_is_neutral(self) -> None:
        assessment = PROTOCOLS.score_protocol_candidate("02b0", confident_result("02b0"))
        self.assertTrue(assessment.hard_valid)
        self.assertGreaterEqual(assessment.score, PROTOCOLS.DETECTION_MIN_SCORE)

    def test_implausible_grid_value_is_hard_rejected(self) -> None:
        result = confident_result("1097")
        result.measurements["ac_voltage"] = 999
        assessment = PROTOCOLS.score_protocol_candidate("1097", result)
        self.assertFalse(assessment.hard_valid)
        self.assertEqual(assessment.score, 0)

    def test_incomplete_core_blocks_are_hard_rejected(self) -> None:
        result = PROTOCOLS.TsunReadResult(
            measurements={"rated_power": 800, "max_designed_power": 800},
            duration_ms=1,
            blocks_ok=1,
        )
        self.assertFalse(PROTOCOLS.score_protocol_candidate("1511", result).hard_valid)


class DetectionFallbackTests(unittest.IsolatedAsyncioTestCase):
    async def test_wrong_firmware_hint_falls_back_to_valid_family(self) -> None:
        attempts: list[str] = []

        class FakeClient:
            model = "Test"
            pv_count = 1
            measurement_keys = frozenset()
            diagnostic_trace = ()

            def __init__(self, protocol_name: str) -> None:
                self.protocol_name = protocol_name

            async def async_read_all(self):
                if self.protocol_name != "1097":
                    raise RuntimeError("wrong family")
                return confident_result("1097")

        def create_client(protocol_name: str, *_args):
            attempts.append(protocol_name)
            return FakeClient(protocol_name)

        with (
            patch.object(PROTOCOLS, "async_detect_protocol_from_firmware", new=AsyncMock(return_value="02b0")),
            patch.object(PROTOCOLS, "_create_specific_client", new=create_client),
        ):
            client = PROTOCOLS.TsunAutoClient("192.0.2.10", 8899, 123456)
            await client.async_read_all()

        self.assertEqual(attempts, ["02b0", "1511", "1097"])
        self.assertEqual(client.protocol_name, "1097")

    async def test_close_scores_are_rejected_as_ambiguous(self) -> None:
        class FakeClient:
            model = "Test"
            pv_count = 1
            measurement_keys = frozenset()
            diagnostic_trace = ()

            def __init__(self, protocol_name: str) -> None:
                self.protocol_name = protocol_name

            async def async_read_all(self):
                if self.protocol_name == "1511":
                    raise RuntimeError("wrong family")
                return confident_result(self.protocol_name)

        def create_client(protocol_name: str, *_args):
            return FakeClient(protocol_name)

        with (
            patch.object(PROTOCOLS, "async_detect_protocol_from_firmware", new=AsyncMock(return_value=None)),
            patch.object(PROTOCOLS, "_create_specific_client", new=create_client),
        ):
            client = PROTOCOLS.TsunAutoClient("192.0.2.10", 8899, 123456)
            with self.assertRaisesRegex(RuntimeError, "Ambiguous"):
                await client.async_read_all()


if __name__ == "__main__":
    unittest.main()
''',
        encoding="utf-8",
    )


if __name__ == "__main__":
    patch_config_flow()
    patch_protocol_tests()
    write_detection_tests()
