# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Coverage tests for the 1.6.2 protocol-family and diagnostic alignment work."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

PROTOCOLS_PATH = (
    Path(__file__).parents[1]
    / "custom_components"
    / "tsun_local"
    / "protocols"
)
SPEC = importlib.util.spec_from_file_location(
    "tsun_local_protocol_coverage_tests",
    PROTOCOLS_PATH / "__init__.py",
    submodule_search_locations=[str(PROTOCOLS_PATH)],
)
assert SPEC is not None and SPEC.loader is not None
PKG = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PKG
SPEC.loader.exec_module(PKG)

from tsun_local_protocol_coverage_tests.protocol_02b0 import (  # noqa: E402
    DIAGNOSTIC_BLOCKS as BLOCKS_02B0,
)
from tsun_local_protocol_coverage_tests.protocol_1097 import (  # noqa: E402
    BLOCKS as BLOCKS_1097,
    MODEL as MODEL_1097,
    SENSOR_LIST as SENSOR_LIST_1097,
    SLOW_BLOCKS as SLOW_BLOCKS_1097,
)


class ProtocolCoverage162Tests(unittest.TestCase):
    """Protect the intended family coverage without enabling writes."""

    def test_02b0_reads_full_remaining_signature_ranges(self) -> None:
        self.assertIn((0x03, 0x2011, 0x2013), BLOCKS_02B0)
        self.assertIn((0x03, 0x202D, 0x205F), BLOCKS_02B0)
        self.assertIn((0x03, 0x302B, 0x302F), BLOCKS_02B0)
        self.assertTrue(all(function == 0x03 for function, _, _ in BLOCKS_02B0))

    def test_1097_family_remains_complete_and_read_only(self) -> None:
        self.assertEqual(MODEL_1097, "GEN4")
        self.assertEqual(SENSOR_LIST_1097, 0x1097)
        self.assertEqual(
            BLOCKS_1097,
            (
                (0x03, 0x1100, 0x110F),
                (0x03, 0x1200, 0x122F),
                (0x03, 0x1300, 0x133F),
            ),
        )
        self.assertEqual(
            SLOW_BLOCKS_1097,
            (
                (0x03, 0x1000, 0x100F),
                (0x03, 0x1400, 0x144F),
            ),
        )
        self.assertTrue(
            all(
                function == 0x03
                for function, _, _ in (*BLOCKS_1097, *SLOW_BLOCKS_1097)
            )
        )


if __name__ == "__main__":
    unittest.main()
