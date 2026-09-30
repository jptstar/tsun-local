from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import tsun_tuya_probe as probe  # noqa: E402


class _FakeDevice:
    def __init__(self, backend, version: float) -> None:
        self.backend = backend
        self.version = version
        self.status_calls = 0

    def set_socketPersistent(self, value):
        self.backend.client_options.append(("persistent", value))

    def set_socketRetryLimit(self, value):
        self.backend.client_options.append(("retry_limit", value))

    def set_socketRetryDelay(self, value):
        self.backend.client_options.append(("retry_delay", value))

    def set_socketTimeout(self, value):
        self.backend.client_options.append(("timeout", value))

    def set_retry(self, value):
        self.backend.client_options.append(("decode_retry", value))

    def status(self):
        self.status_calls += 1
        self.backend.status_versions.append(self.version)
        if self.version in (3.5, 3.4):
            # Include credential-looking text in the backend error payload to prove
            # it is not copied into the report.
            return {
                "Error": "wrong key DEVICE-ID-SECRET abcdefghijklmnop",
                "Err": "914",
                "Payload": "abcdefghijklmnop",
            }
        if self.status_calls == 1:
            return {
                "dps": {
                    "1": True,
                    "18": 123.4,
                    "20": "abcdefghijklmnop",
                    "21": "normal",
                }
            }
        return {
            "dps": {
                "1": True,
                "18": 124.1,
                "20": "abcdefghijklmnop",
                "21": "normal",
            }
        }


class _FakeTinyTuya:
    __version__ = "1.20.0"

    def __init__(self) -> None:
        self.created: list[tuple[str, str, str, float]] = []
        self.status_versions: list[float] = []
        self.client_options: list[tuple[str, object]] = []

    def Device(
        self,
        dev_id,
        host,
        local_key,
        *,
        version,
        persist,
        connection_timeout,
        connection_retry_limit,
        connection_retry_delay,
    ):
        self.created.append((dev_id, host, local_key, version))
        self.client_options.extend(
            [
                ("constructor_persist", persist),
                ("constructor_timeout", connection_timeout),
                ("constructor_retry_limit", connection_retry_limit),
                ("constructor_retry_delay", connection_retry_delay),
            ]
        )
        return _FakeDevice(self, version)


class TuyaAuthenticatedProbeTests(unittest.TestCase):
    @staticmethod
    def _document() -> dict:
        return {
            "metadata": {
                "capture_status": "partial_success",
                "protocol_validation_status": "transport_detected",
                "capture_limitation": "encrypted_status_requires_local_key",
                "measurements_available": False,
                "requires_local_key_for_status": True,
                "privacy": {
                    "tuya_device_id_in_output": False,
                    "tuya_local_key_in_output": False,
                },
            },
            "tuya_lan": {
                "candidate_confirmed": True,
                "transport_detected": True,
                "status_read_attempted": False,
                "configuration_write_performed": False,
                "application_payload_sent": False,
            },
            "capture_summary": {
                "snapshots": 0,
                "coherent_snapshots": 0,
                "unique_raw_registers": 0,
            },
        }

    @staticmethod
    def _args(**overrides):
        values = {"timeout": 0.2, "snapshots": 2, "interval": 0.0}
        values.update(overrides)
        return SimpleNamespace(**values)

    def test_falls_back_versions_reads_status_and_never_exports_credentials(self) -> None:
        backend = _FakeTinyTuya()
        device_id = "DEVICE-ID-SECRET"
        local_key = "abcdefghijklmnop"
        document = probe.extend_tuya_capture(
            self._document(),
            self._args(),
            "192.0.2.50",
            value_prompt=lambda _prompt: device_id,
            secret_prompt=lambda _prompt: local_key,
            backend=backend,
        )

        self.assertEqual(backend.status_versions[:3], [3.5, 3.4, 3.3])
        self.assertEqual(document["tuya_lan"]["protocol_version"], "3.3")
        self.assertTrue(document["tuya_lan"]["status_read_success"])
        self.assertTrue(document["tuya_lan"]["application_payload_sent"])
        self.assertFalse(document["tuya_lan"]["configuration_write_performed"])
        self.assertFalse(document["tuya_lan"]["control_command_sent"])
        self.assertEqual(document["metadata"]["capture_status"], "success")
        self.assertEqual(
            document["metadata"]["protocol_validation_status"],
            "authenticated_read",
        )

        encoded = json.dumps(document, sort_keys=True)
        self.assertNotIn(device_id, encoded)
        self.assertNotIn(local_key, encoded)
        string_dp = document["tuya_lan"]["dps_snapshots"][0]["dps"]["20"]
        self.assertEqual(string_dp["type"], "string")
        self.assertIn("sha256", string_dp)
        self.assertNotIn("value", string_dp)

    def test_multiple_snapshots_identify_changing_numeric_dps(self) -> None:
        backend = _FakeTinyTuya()
        document = probe.extend_tuya_capture(
            self._document(),
            self._args(snapshots=2),
            "192.0.2.50",
            value_prompt=lambda _prompt: "DEVICE-ID-SECRET",
            secret_prompt=lambda _prompt: "abcdefghijklmnop",
            backend=backend,
        )
        analysis = document["tuya_lan"]["dps_analysis"]
        self.assertIn("18", analysis["changing"])
        self.assertIn("1", analysis["stable"])
        self.assertEqual(len(document["tuya_lan"]["dps_snapshots"]), 2)

    def test_invalid_local_key_never_contacts_authenticated_backend(self) -> None:
        backend = _FakeTinyTuya()
        document = probe.extend_tuya_capture(
            self._document(),
            self._args(),
            "192.0.2.50",
            value_prompt=lambda _prompt: "DEVICE-ID-SECRET",
            secret_prompt=lambda _prompt: "too-short",
            backend=backend,
        )
        self.assertEqual(backend.created, [])
        self.assertFalse(document["tuya_lan"]["status_read_attempted"])
        self.assertEqual(document["tuya_lan"]["status_read_blocked_by"], "invalid_local_key")

    def test_skipped_credentials_preserve_transport_only_result(self) -> None:
        backend = _FakeTinyTuya()
        document = probe.extend_tuya_capture(
            self._document(),
            self._args(),
            "192.0.2.50",
            value_prompt=lambda _prompt: "",
            secret_prompt=lambda _prompt: self.fail("Local Key must not be requested"),
            backend=backend,
        )
        self.assertEqual(backend.created, [])
        self.assertEqual(document["metadata"]["capture_status"], "partial_success")
        self.assertEqual(document["tuya_lan"]["status_read_blocked_by"], "credentials_skipped")
        self.assertFalse(document["tuya_lan"]["local_key_requested"])

    def test_string_and_complex_dps_are_fingerprinted(self) -> None:
        text = probe._sanitize_dps_value("serial-or-enum")
        obj = probe._sanitize_dps_value({"secret": "value", "n": 2})
        self.assertEqual(text["type"], "string")
        self.assertEqual(text["length"], len("serial-or-enum"))
        self.assertNotIn("serial-or-enum", json.dumps(text))
        self.assertEqual(obj["type"], "dict")
        self.assertIn("sha256", obj)
        self.assertNotIn("secret", json.dumps(obj))


if __name__ == "__main__":
    unittest.main()
