from __future__ import annotations

from pathlib import Path
import sys
import unittest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import tsun_report_model_assignment as legacy_assignment  # noqa: E402
import tsun_report_upload as assignment  # noqa: E402


def tsun_capture(power: int, protocol: str = "02b0") -> dict:
    return {
        "metadata": {
            "model_supplied_by_user": None,
            "detected_protocol": protocol,
            "protocol_validation_status": "validated",
        },
        "capture_summary": {
            "successful_block_reads": 12,
            "unique_raw_registers": 48,
        },
        "decoded_known_measurements": {"rated_power": power},
    }


class ExtraCandidateModelAssignmentTests(unittest.TestCase):
    def test_nxenara_shape_assigns_four_tsun_reports_and_leaves_extra_tuya(self) -> None:
        diagnostics = [
            tsun_capture(450),
            tsun_capture(300),
            tsun_capture(450),
            {
                "metadata": {"model_supplied_by_user": None, "detected_protocol": "tuya-lan"},
                "decoded_known_measurements": {},
            },
            tsun_capture(800),
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

    def test_single_tuya_cannot_inherit_unrelated_mp3000_inventory(self) -> None:
        diagnostics = [
            {
                "metadata": {"model_supplied_by_user": None, "detected_protocol": "tuya-lan"},
                "decoded_known_measurements": {},
            }
        ]
        devices = [{"model": "TSOL-MP3000", "quantity": 1}]
        self.assertEqual(assignment.associate_declared_models(diagnostics, devices), {})
        self.assertIsNone(diagnostics[0]["metadata"]["model_supplied_by_user"])

    def test_unmeasured_02b0_device_cannot_inherit_mp3000_inventory(self) -> None:
        diagnostic = tsun_capture(0)
        diagnostic["logger_web"] = {
            "summary": {
                "logger_raw_profile": "21510:Deye",
                "inverter_serial_prefix": "260",
            }
        }
        self.assertEqual(
            assignment.associate_declared_models(
                [diagnostic], [{"model": "TSOL-MP3000", "quantity": 1}]
            ),
            {},
        )
        self.assertIsNone(diagnostic["metadata"]["model_supplied_by_user"])

    def test_foreign_logger_does_not_match_even_when_power_matches(self) -> None:
        diagnostic = tsun_capture(3000)
        diagnostic["logger_web"] = {"summary": {"logger_raw_profile": "21510:Deye"}}
        self.assertEqual(
            assignment.associate_declared_models(
                [diagnostic], [{"model": "TSOL-MP3000", "quantity": 1}]
            ),
            {},
        )

    def test_real_gen4_mx500_variant_is_matched_by_power(self) -> None:
        diagnostic = tsun_capture(500, "1097")
        self.assertEqual(
            assignment.associate_declared_models(
                [diagnostic], [{"model": "TSOL-MX500", "quantity": 1}]
            ),
            {0: "TSOL-MX500"},
        )

    def test_no_protocol_exchange_cannot_confirm_identity(self) -> None:
        diagnostic = tsun_capture(500)
        diagnostic["metadata"]["protocol_validation_status"] = "undetected"
        self.assertEqual(
            assignment.associate_declared_models(
                [diagnostic], [{"model": "TSOL-MX500", "quantity": 1}]
            ),
            {},
        )

    def test_missing_capture_blocks_cannot_confirm_identity(self) -> None:
        diagnostic = tsun_capture(500)
        diagnostic["capture_summary"]["successful_block_reads"] = 0
        self.assertEqual(
            assignment.associate_declared_models(
                [diagnostic], [{"model": "TSOL-MX500", "quantity": 1}]
            ),
            {},
        )

    def test_fewer_diagnostics_than_declared_units_stays_unassigned(self) -> None:
        diagnostics = [tsun_capture(450)]
        devices = [{"model": "TSOL-MX450", "quantity": 2}]
        self.assertEqual(assignment.associate_declared_models(diagnostics, devices), {})
        self.assertIsNone(diagnostics[0]["metadata"]["model_supplied_by_user"])

    def test_legacy_model_assignment_module_uses_canonical_policy(self) -> None:
        self.assertIs(
            legacy_assignment.associate_declared_models,
            assignment.associate_declared_models,
        )


if __name__ == "__main__":
    unittest.main()
