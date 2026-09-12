# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
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
