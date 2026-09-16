from __future__ import annotations

from pathlib import Path
import sys
import types
import unittest
from unittest import mock

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import tsun_diagnostic_runtime as runtime  # noqa: E402


class DiagnosticRuntimeTests(unittest.TestCase):
    def test_pipeline_is_unique_ordered_and_read_only(self) -> None:
        runtime.validate_runtime_stages()
        self.assertEqual(
            runtime.pipeline_stage_names(),
            (
                "1097-research-fallback",
                "1097-transport-enrichment",
                "tuya-authenticated-status",
            ),
        )
        description = runtime.pipeline_description()
        self.assertEqual([item["order"] for item in description], [10, 20, 30])
        self.assertTrue(all(item["conditional"] for item in description))
        self.assertTrue(all(item["read_only"] for item in description))

    def test_configure_installs_extensions_in_declared_order(self) -> None:
        fake_dump = types.SimpleNamespace()
        calls: list[str] = []

        with (
            mock.patch.object(
                runtime.tsun_1097_research_probe,
                "install",
                side_effect=lambda module: calls.append("1097-research-fallback"),
            ),
            mock.patch.object(
                runtime.tsun_1097_transport_extension,
                "install",
                side_effect=lambda module: calls.append("1097-transport-enrichment"),
            ),
            mock.patch.object(
                runtime.tsun_tuya_probe,
                "install",
                side_effect=lambda module, **kwargs: calls.append("tuya-authenticated-status"),
            ),
        ):
            signature = runtime.configure_dump_extensions(
                fake_dump,
                value_prompt=lambda _prompt: "",
                secret_prompt=lambda _prompt: "",
            )

        self.assertEqual(tuple(calls), runtime.pipeline_stage_names())
        self.assertEqual(signature, runtime.pipeline_stage_names())
        self.assertEqual(
            getattr(fake_dump, "_tsun_diagnostic_runtime_signature"),
            runtime.pipeline_stage_names(),
        )

    def test_configuration_is_idempotent_and_does_not_double_wrap(self) -> None:
        fake_dump = types.SimpleNamespace()
        with (
            mock.patch.object(runtime.tsun_1097_research_probe, "install") as research,
            mock.patch.object(runtime.tsun_1097_transport_extension, "install") as extension,
            mock.patch.object(runtime.tsun_tuya_probe, "install") as tuya,
        ):
            first = runtime.configure_dump_extensions(fake_dump)
            second = runtime.configure_dump_extensions(fake_dump)

        self.assertEqual(first, second)
        research.assert_called_once_with(fake_dump)
        extension.assert_called_once_with(fake_dump)
        tuya.assert_called_once_with(fake_dump, value_prompt=None, secret_prompt=None)

    def test_conflicting_existing_runtime_is_rejected(self) -> None:
        fake_dump = types.SimpleNamespace(
            _tsun_diagnostic_runtime_signature=("different-stage",)
        )
        with self.assertRaisesRegex(RuntimeError, "different stage order"):
            runtime.configure_dump_extensions(fake_dump)


if __name__ == "__main__":
    unittest.main()
