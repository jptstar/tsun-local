# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later
"""Regression coverage for opt-in, privacy-safe single-IP GEN3 network checks."""

from __future__ import annotations

import importlib.util
import json
import queue
from types import SimpleNamespace
from pathlib import Path
import sys
import tempfile
from unittest import TestCase, main, mock

TOOL_PATH = Path(__file__).parents[1] / "tools" / "tsun_dump.py"
SPEC = importlib.util.spec_from_file_location("tsun_network_probe_test", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
TOOL = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = TOOL
SPEC.loader.exec_module(TOOL)


class NetworkProbeTests(TestCase):
    def test_private_lan_address_only_and_no_dns_resolution(self) -> None:
        for host in (
            "8.8.8.8", "127.0.0.1", "169.254.1.1", "224.0.0.1",
            "192.0.2.2", "localhost", "some-cloud.example", "::1",
        ):
            with self.subTest(host=host), mock.patch.object(
                TOOL.socket, "create_connection"
            ) as connect:
                with self.assertRaises(ValueError):
                    TOOL.capture_local_network_probe(host)
                connect.assert_not_called()
        for host in ("10.3.4.5", "172.20.4.5", "192.168.1.15"):
            self.assertEqual(TOOL._private_lan_ipv4(host), host)

    def test_open_refused_timeout_without_application_payload(self) -> None:
        attempted: list[tuple[str, int]] = []
        connected = mock.MagicMock()

        def connect(target: tuple[str, int], *, timeout: float):
            attempted.append(target)
            self.assertLessEqual(timeout, 1.0)
            if target[1] == 80:
                return connected
            if target[1] == 5005:
                raise ConnectionRefusedError("connection refused")
            raise TimeoutError("no TCP handshake")

        with mock.patch.object(TOOL.socket, "create_connection", side_effect=connect):
            report = TOOL.capture_local_network_probe(
                "192.168.3.15", ports=(80, 5005, 8899)
            )
        self.assertEqual(
            [(p["port"], p["status"]) for p in report["tcp_connect_tests"]],
            [(80, "open"), (5005, "refused"), (8899, "timeout")],
        )
        self.assertEqual(len(attempted), 3)
        connected.__enter__.assert_called_once()
        self.assertFalse(report["metadata"]["application_payload_sent"])
        self.assertFalse(report["assessment"]["inverter_identity_confirmed"])
        self.assertEqual(report["assessment"]["open_ports"], [80])
        self.assertNotIn("192.168.3.15", json.dumps(report))

    def test_no_open_ports_is_not_interpreted_as_offline(self) -> None:
        with mock.patch.object(
            TOOL.socket, "create_connection", side_effect=TimeoutError
        ):
            report = TOOL.capture_local_network_probe(
                "192.168.1.50", ports=(5005, 10000)
            )
        self.assertEqual(report["assessment"]["open_ports"], [])
        self.assertIn("does not imply", report["assessment"]["note"])

    def test_unsafe_ports_and_timeouts_rejected_before_scanning(self) -> None:
        with mock.patch.object(TOOL.socket, "create_connection") as connect:
            with self.assertRaises(ValueError):
                TOOL.capture_local_network_probe("192.168.2.10", ports=(22,))
            with self.assertRaises(ValueError):
                TOOL.capture_local_network_probe("192.168.2.10", timeout=5.0)
            connect.assert_not_called()

    def test_report_keeps_ip_and_serial_out_and_uses_distinct_format(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "output.json"
            with mock.patch.object(
                TOOL.socket, "create_connection", side_effect=TimeoutError
            ):
                written, report = TOOL.write_local_network_probe_report(
                    "192.168.1.88", path
                )
            self.assertEqual(path, written)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), report)
            self.assertEqual(report["format"], "tsun-local-network-probe")
            self.assertNotIn("192.168.1.88", path.read_text(encoding="utf-8"))
            self.assertFalse(report["metadata"]["cloud_traffic_intercepted"])

    def test_cli_does_not_require_monitor_serial_or_normal_discovery(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            dest = Path(folder) / "network.json"
            with mock.patch.object(
                TOOL.socket, "create_connection", side_effect=TimeoutError
            ), mock.patch.object(
                TOOL, "resolve_targets", side_effect=AssertionError("unexpected discovery")
            ), mock.patch.object(
                sys, "argv", ["tsun_dump.py", "--no-update", "--network-probe",
                               "192.168.5.20", "--output", str(dest)]
            ):
                self.assertEqual(TOOL.main(), 0)
            self.assertTrue(dest.exists())


    def test_network_probe_report_enters_opt_in_upload_selection(self) -> None:
        import tsun_diagnostic_gui as gui

        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "tsun_network_probe_demo.json"
            path.write_text('{"format":"tsun-local-network-probe"}', encoding="utf-8")
            events = queue.Queue()
            fake = SimpleNamespace(
                events=events,
                t={"network_probe_done": "ready", "network_probe_failed": "failed"},
            )
            with mock.patch.object(
                gui.tsun_dump, "write_local_network_probe_report",
                return_value=(path, {"assessment": {
                    "open_ports": [5005], "note": "Transport only."
                }}),
            ):
                gui.DiagnosticApp._run_network_probe(fake, Path(folder), "192.168.1.88")

            pending = list(events.queue)
            self.assertEqual([entry[0] for entry in pending], [
                "log", "log", "log", "network_probe_report", "status"
            ])
            self.assertEqual(pending[3][1], path.resolve())

            receiver = SimpleNamespace(
                events=events,
                latest_reports=[],
                uploaded_reports=set(),
                status=mock.Mock(),
                progress=mock.Mock(),
                confirm_check=mock.Mock(),
                status_label=mock.Mock(),
                root=mock.Mock(),
                _append_log=mock.Mock(),
                _sync_run_button=mock.Mock(),
                t={},
            )
            gui.DiagnosticApp._poll_events(receiver)
            self.assertEqual(receiver.latest_reports, [path.resolve()])
            self.assertEqual(receiver.uploaded_reports, set())

    def test_network_probe_can_use_existing_upload_contract_with_consent(self) -> None:
        import tsun_report_upload as upload

        with mock.patch.object(
            TOOL.socket, "create_connection", side_effect=TimeoutError
        ):
            report = TOOL.capture_local_network_probe("192.168.1.88")
        self.assertEqual(upload.validate_diagnostic(report), report)
        devices = [{"model": "TSOL-MP3000", "quantity": 1}]
        # Never infer TSUN identity from a network-only report.
        self.assertEqual(upload.associate_declared_models([report], devices), {})

        with mock.patch.object(upload.request, "urlopen") as send:
            with self.assertRaises(upload.ReportUploadError):
                upload.upload_diagnostic(
                    report, consent=False, tester_name="Tester",
                    declared_devices=devices,
                )
            send.assert_not_called()

            response = mock.MagicMock()
            response.__enter__.return_value.read.return_value = json.dumps({
                "ok": True, "report_id": "TSL-20261010-12345678",
                "view_url": "https://example.invalid/view/network",
            }).encode("utf-8")
            send.return_value = response
            receipt = upload.upload_diagnostic(
                report, consent=True, tester_name="Tester",
                declared_devices=devices,
            )
            self.assertEqual(receipt["report_id"], "TSL-20261010-12345678")
            self.assertEqual(send.call_count, 1)
            req = send.call_args.args[0]
            sent = json.loads(req.data)
            self.assertEqual(sent["diagnostic"]["format"], "tsun-local-network-probe")
            self.assertTrue(sent["consent"])
            self.assertNotIn("192.168.1.88", json.dumps(sent))

    def test_prepare_email_creates_draft_without_attachment_or_sending(self) -> None:
        import tsun_diagnostic_desktop as desktop

        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "tsun_network_probe_demo.json"
            path.write_text("{}", encoding="utf-8")
            fake = SimpleNamespace(
                latest_reports=[path], lang="fr", root=mock.Mock()
            )
            with mock.patch.object(desktop.webbrowser, "open", return_value=True) as opened:
                with mock.patch.object(desktop.messagebox, "showinfo") as show:
                    desktop.CleanDiagnosticApp._prepare_report_email(fake)
            self.assertEqual(opened.call_count, 1)
            link = opened.call_args.args[0]
            self.assertTrue(link.startswith("mailto:dev@jptstar.com?"))
            self.assertIn("tsun_network_probe_demo.json", link)
            self.assertIn("joindre manuellement", show.call_args.args[1])


    def test_windows_entrypoint_has_manual_probe_button(self) -> None:
        gui = (Path(__file__).parents[1] / "tools" / "tsun_diagnostic_gui.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("def _start_network_probe(", gui)
        self.assertIn("write_local_network_probe_report(", gui)
        self.assertIn('self.t["network_probe_run"]', gui)
        self.assertNotIn("self.latest_reports.append(path)", gui)


if __name__ == "__main__":
    main()
