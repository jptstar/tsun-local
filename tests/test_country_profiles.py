# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Regression tests for protocol-aware country/grid-profile labels."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).parents[1]
MODULE_PATH = ROOT / "custom_components/tsun_local/country_profiles.py"
SPEC = importlib.util.spec_from_file_location("tsun_country_profiles", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CountryProfileTests(unittest.TestCase):
    def test_1511_hardware_backed_profiles(self) -> None:
        self.assertEqual(MODULE.country_profile_state("1511", {"country_profile_raw": 6}), "6 (Polska)")
        self.assertEqual(MODULE.country_profile_state("1511", {"country_profile_raw": 8}), "8 (France)")
        self.assertEqual(MODULE.country_profile_state("1511", {"country_profile_raw": 2}), "2 (Deutschland)")

    def test_1511_unknown_code_stays_numeric(self) -> None:
        self.assertEqual(MODULE.country_profile_state("1511", {"country_profile_raw": 99}), "99")

    def test_02b0_uses_product_compliance_source(self) -> None:
        self.assertEqual(MODULE.country_profile_state("02b0", {"product_compliance_type_raw": 16}), "16 (United Kingdom)")
        self.assertIsNone(MODULE.country_profile_state("02b0", {"country_profile_raw": 8}))

    def test_1097_uses_gen4_country_source(self) -> None:
        self.assertEqual(MODULE.country_profile_state("1097", {"country_profile_raw": 2}), "2 (Deutschland)")


if __name__ == "__main__":
    unittest.main()
