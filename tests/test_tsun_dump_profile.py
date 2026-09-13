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
        with mock.patch.object(TOOL, "load_upload_profile", return_value={"tester_name": "", "declared_devices": []}), mock.patch.object(TOOL, "save_upload_profile") as save, mock.patch(
            "builtins.input",
            side_effect=["Marcus", "2", "", "9", "9"],
        ):
            name, devices = TOOL._prompt_upload_profile()
        self.assertEqual(name, "Marcus")
        self.assertEqual(devices, [{"model": "TSOL-MS800", "quantity": 2}])
        save.assert_called_once_with("Marcus", devices)

    def test_unknown_model_can_be_entered(self) -> None:
        with mock.patch.object(TOOL, "load_upload_profile", return_value={"tester_name": "", "declared_devices": []}), mock.patch.object(TOOL, "save_upload_profile"), mock.patch(
            "builtins.input",
            side_effect=["Marcus", "1", "", "0", "TSOL-UNKNOWN-TEST"],
        ):
            name, devices = TOOL._prompt_upload_profile()
        self.assertEqual(name, "Marcus")
        self.assertEqual(devices, [{"model": "TSOL-UNKNOWN-TEST", "quantity": 1}])

    def test_saved_profile_supplies_defaults(self) -> None:
        saved = {
            "tester_name": "Marcus",
            "declared_devices": [{"model": "TSOL-MS800", "quantity": 2}],
        }
        with mock.patch.object(TOOL, "load_upload_profile", return_value=saved), mock.patch.object(TOOL, "save_upload_profile"), mock.patch(
            "builtins.input",
            side_effect=["", "", "", "", ""],
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
