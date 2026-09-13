# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from unittest import mock
import unittest

ROOT = Path(__file__).parents[1]
TOOL_PATH = ROOT / "tools" / "tsun_dump.py"
SPEC = importlib.util.spec_from_file_location("tsun_dump_profile_test", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
TOOL = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = TOOL
SPEC.loader.exec_module(TOOL)


class TsunDumpProfileTests(unittest.TestCase):
    def test_prompt_asks_one_model_per_inverter_and_merges_duplicates(self) -> None:
        with mock.patch(
            "builtins.input",
            side_effect=["Marcus", "2", "", "TSOL-MS800", "TSOL-MS800"],
        ):
            name, devices = TOOL._prompt_upload_profile()
        self.assertEqual(name, "Marcus")
        self.assertEqual(devices, [{"model": "TSOL-MS800", "quantity": 2}])

    def test_parser_collects_submit_profile(self) -> None:
        args = TOOL.build_parser().parse_args(
            ["--submit", "--tester-name", "Marcus", "--device", "TSOL-MS800:2"]
        )
        self.assertEqual(args.tester_name, "Marcus")
        self.assertEqual(args.device, [{"model": "TSOL-MS800", "quantity": 2}])


if __name__ == "__main__":
    unittest.main()
