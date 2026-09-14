from __future__ import annotations

from pathlib import Path
import sys
import unittest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import tsun_report_model_assignment as assignment  # noqa: E402


class ExtraCandidateModelAssignmentTests(unittest.TestCase):
    def test_nxenara_shape_assigns_four_tsun_reports_and_leaves_extra_tuya(self) -> None:
        diagnostics = [
            {
                "metadata": {"model_supplied_by_user": None, "detected_protocol": "02b0"},
                "decoded_known_measurements": {"rated_power": 450},
            },
            {
                "metadata": {"model_supplied_by_user": None, "detected_protocol": "02b0"},
                "decoded_known_measurements": {"rated_power": 300},
            },
            {
                "metadata": {"model_supplied_by_user": None, "detected_protocol": "02b0"},
                "decoded_known_measurements": {"rated_power": 450},
            },
            {
                "metadata": {"model_supplied_by_user": None, "detected_protocol": "tuya-lan"},
                "decoded_known_measurements": {},
            },
            {
                "metadata": {"model_supplied_by_user": None, "detected_protocol": "02b0"},
                "decoded_known_measurements": {"rated_power": 800},
            },
        ]
        devices = [
            {"model": "TSOL-MX450", "quantity": 2},
            {"model": "TSOL-MS800", "quantity": 1},
            {"model": "TSOL-MS300", "quantity": 1},
        ]

        assigned = assignment.associate_declared_models(diagnostics, devices)

        self.assertEqual(
            assigned,
            {
                0: "TSOL-MX450",
                1: "TSOL-MS300",
                2: "TSOL-MX450",
                4: "TSOL-MS800",
            },
        )
        self.assertIsNone(diagnostics[3]["metadata"]["model_supplied_by_user"])
        self.assertEqual(
            diagnostics[4]["metadata"]["model_assignment"]["method"],
            "rated_power_match",
        )

    def test_single_unmeasured_tuya_can_still_take_single_declared_model(self) -> None:
        diagnostics = [
            {
                "metadata": {"model_supplied_by_user": None, "detected_protocol": "tuya-lan"},
                "decoded_known_measurements": {},
            }
        ]
        devices = [{"model": "TSOL-MX800", "quantity": 1}]
        assigned = assignment.associate_declared_models(diagnostics, devices)
        self.assertEqual(assigned, {0: "TSOL-MX800"})
        self.assertEqual(
            diagnostics[0]["metadata"]["model_assignment"]["method"],
            "remaining_declared_inventory",
        )

    def test_fewer_diagnostics_than_declared_units_stays_unassigned(self) -> None:
        diagnostics = [
            {
                "metadata": {"model_supplied_by_user": None},
                "decoded_known_measurements": {"rated_power": 450},
            }
        ]
        devices = [{"model": "TSOL-MX450", "quantity": 2}]
        self.assertEqual(assignment.associate_declared_models(diagnostics, devices), {})
        self.assertIsNone(diagnostics[0]["metadata"]["model_supplied_by_user"])


if __name__ == "__main__":
    unittest.main()
