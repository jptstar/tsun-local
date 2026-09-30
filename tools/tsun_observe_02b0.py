#!/usr/bin/env python3
# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Long-running, privacy-safe, read-only observer for intermittent 02B0 faults.

This tool is deliberately separate from the normal hardware dump. It repeatedly
compares a one-register health read with the production 23-register telemetry
read across every discovered 02B0 logger. A bounded deep-capture matrix runs only
after a failure, so intermittent faults can be characterized without changing
inverter configuration or continuously high-rate polling.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import socket
import sys
import time
from typing import Any, Iterable

import tsun_dump
import tsun_report_upload as report_upload
import tsun_report_upload_retry as report_upload_retry


OBSERVER_VERSION = "1.0.0"
REPORT_FORMAT = "tsun-local-02b0-observation"
DEFAULT_OBSERVE_MINUTES = 60.0
DEFAULT_INTERVAL_SECONDS = 30.0
MIN_INTERVAL_SECONDS = 5.0
MAX_OBSERVE_MINUTES = 24 * 60.0
DEEP_CAPTURE_COOLDOWN_SECONDS = 120.0
MAX_DEEP_CAPTURES_PER_DEVICE = 5
SENSOR_LIST = 0x02B0

BASELINE_CASES = (
    ("minimal_1", 0x3000, 0x3000, SENSOR_LIST),
    ("production_23", 0x3008, 0x301E, SENSOR_LIST),
)
DEEP_CASES = (
    ("minimal_1", 0x3000, 0x3000, SENSOR_LIST),
    ("start_3008_8", 0x3008, 0x300F, SENSOR_LIST),
    ("cross_boundary_16", 0x3008, 0x3017, SENSOR_LIST),
    ("cross_boundary_17", 0x3008, 0x3018, SENSOR_LIST),
    ("legacy_v153_22", 0x3009, 0x301E, SENSOR_LIST),
    ("production_23", 0x3008, 0x301E, SENSOR_LIST),
    ("production_23_sensor_list_0000", 0x3008, 0x301E, 0x0000),
    ("dynamic_3010_16_sensor_list_0000", 0x3010, 0x301F, 0x0000),
)


def _positive_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("value must be a finite number > 0")
    return number


def _observe_minutes(value: str) -> float:
    number = _positive_float(value)
    if number > MAX_OBSERVE_MINUTES:
        raise argparse.ArgumentTypeError("observation duration is limited to 1440 minutes")
    return number


def _interval_seconds(value: str) -> float:
    number = _positive_float(value)
    if number < MIN_INTERVAL_SECONDS:
        raise argparse.ArgumentTypeError(
            f"interval must be at least {MIN_INTERVAL_SECONDS:g} seconds"
        )
    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only long-duration observer for intermittent TSUN 02B0 data loss. "
            "No inverter configuration write operation is implemented."
        )
    )
    parser.add_argument(
        "--observe",
        type=_observe_minutes,
        default=DEFAULT_OBSERVE_MINUTES,
        metavar="MINUTES",
        help="observation duration in minutes (default: 60)",
    )
    parser.add_argument(
        "--interval",
        type=_interval_seconds,
        default=DEFAULT_INTERVAL_SECONDS,
        metavar="SECONDS",
        help="target interval between round starts (minimum 5 s; default: 30)",
    )
    parser.add_argument("--host", help="optional single logger IP; otherwise discover all")
    parser.add_argument(
        "--serial",
        "--monitor-sn",
        dest="serial",
        type=tsun_dump._monitor_sn_arg,
        help="numeric Monitor SN for single-target use; normally auto-resolved",
    )
    parser.add_argument("--port", type=tsun_dump._positive_port, default=tsun_dump.DEFAULT_PORT)
    parser.add_argument(
        "--network",
        action="append",
        default=[],
        metavar="CIDR",
        help="additional IPv4 /24-or-smaller network to scan; may be repeated",
    )
    parser.add_argument(
        "--timeout", type=_positive_float, default=tsun_dump.DEFAULT_TIMEOUT
    )
    parser.add_argument(
        "--discovery-timeout",
        type=tsun_dump._non_negative_float,
        default=tsun_dump.DEFAULT_DISCOVERY_TIMEOUT,
    )
    parser.add_argument(
        "--tcp-scan-timeout",
        type=_positive_float,
        default=tsun_dump.DEFAULT_TCP_SCAN_TIMEOUT,
    )
    parser.add_argument(
        "--http-scan-timeout",
        type=_positive_float,
        default=tsun_dump.DEFAULT_HTTP_SCAN_TIMEOUT,
    )
    parser.add_argument(
        "--http-page-timeout",
        type=_positive_float,
        default=tsun_dump.DEFAULT_HTTP_PAGE_TIMEOUT,
    )
    parser.add_argument("--output", type=Path, help="observation JSON output path")
    parser.add_argument(
        "--submit",
        action="store_true",
        help="explicitly consent to upload the anonymized observation after capture",
    )
    parser.add_argument(
        "--tester-name",
        default="",
        help="tester name or pseudonym; required with --submit",
    )
    parser.add_argument(
        "--device",
        action="append",
        type=tsun_dump._declared_device_arg,
        default=[],
        metavar="MODEL[:QTY]",
        help="declare inverter model for --submit; may be repeated",
    )
    return parser


def _safe_error(exc: Exception) -> dict[str, str]:
    return tsun_dump.safe_error_details(exc)


def _tcp_probe(host: str, port: int, timeout: float) -> dict[str, Any]:
    started = time.monotonic()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            pass
    except OSError as exc:
        return {
            "reachable": False,
            "connect_latency_ms": round((time.monotonic() - started) * 1000, 1),
            "error": _safe_error(exc),
        }
    return {
        "reachable": True,
        "connect_latency_ms": round((time.monotonic() - started) * 1000, 1),
    }


def _payload_metrics(hex_payload: str | None) -> dict[str, Any]:
    if not hex_payload:
        return {}
    try:
        payload = bytes.fromhex(hex_payload)
    except ValueError:
        return {"payload_parseable": False}
    result: dict[str, Any] = {
        "payload_parseable": True,
        "payload_bytes": len(payload),
    }
    if len(payload) < 2:
        return result
    result["unit"] = payload[0]
    result["function"] = f"0x{payload[1]:02X}"
    if len(payload) >= 3 and payload[1] in (0x03, 0x04):
        announced = payload[2]
        expected = 3 + announced + 2
        result.update(
            {
                "announced_data_bytes": announced,
                "expected_response_bytes": expected,
                "length_matches": len(payload) == expected,
            }
        )
    if len(payload) >= 5:
        result["crc_valid"] = (
            tsun_dump.crc16_modbus(payload[:-2]) == payload[-2:]
        )
    return result


def compact_observation(observation: dict[str, Any]) -> dict[str, Any]:
    """Keep transport evidence while dropping bulky raw payload hex strings."""
    compact: dict[str, Any] = {
        "result": observation.get("result", "failure"),
    }
    for key in (
        "latency_ms",
        "first_payload_bytes",
        "register_count",
        "short_marker",
        "followup",
        "followup_payload_bytes",
        "followup_wait_ms",
        "error",
        "followup_error",
    ):
        if key in observation:
            compact[key] = observation[key]

    first_metrics = _payload_metrics(observation.get("first_payload"))
    if first_metrics:
        compact["first_modbus"] = first_metrics
    followup_metrics = _payload_metrics(observation.get("followup_payload"))
    if followup_metrics:
        compact["followup_modbus"] = followup_metrics
    return compact


def _read_case(
    host: str,
    port: int,
    sn: int,
    start: int,
    end: int,
    sensor_list: int,
    timeout: float,
) -> dict[str, Any]:
    started = time.monotonic()
    try:
        observation = tsun_dump._observe_02b0_read(
            host,
            port,
            sn,
            start,
            end,
            sensor_list=sensor_list,
            timeout=min(timeout, tsun_dump.CHARACTERIZATION_TIMEOUT_CAP),
        )
    except Exception as exc:
        observation = {
            "result": "failure",
            "error": _safe_error(exc),
            "latency_ms": round((time.monotonic() - started) * 1000, 1),
        }
    return compact_observation(observation)


def _succeeded(observation: dict[str, Any]) -> bool:
    return observation.get("result") in ("success", "success_after_short_marker")


def _deep_capture(host: str, port: int, sn: int, timeout: float) -> dict[str, Any]:
    tests: list[dict[str, Any]] = []
    for test_id, start, end, sensor_list in DEEP_CASES:
        tests.append(
            {
                "id": test_id,
                "function": "0x03",
                "start": f"0x{start:04X}",
                "end": f"0x{end:04X}",
                "register_count": end - start + 1,
                "sensor_list": f"0x{sensor_list:04X}",
                "observation": _read_case(
                    host, port, sn, start, end, sensor_list, timeout
                ),
            }
        )
        time.sleep(tsun_dump.CHARACTERIZATION_DELAY)
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "read_only": True,
        "fresh_connection_per_test": True,
        "tests": tests,
    }


def _public_target(index: int, discovery: dict[str, Any], protocol: str | None) -> dict[str, Any]:
    return {
        "device_index": index,
        "protocol": protocol,
        "firmware_hint": discovery.get("firmware_version"),
        "protocol_hint": discovery.get("protocol_hint"),
        "discovery_sources": list(discovery.get("sources") or []),
        "private_network_identity_stored": False,
    }


def _detect_observation_targets(
    args: argparse.Namespace,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    resolved, resolution = tsun_dump.resolve_targets(args)
    private_targets: list[dict[str, Any]] = []
    public_targets: list[dict[str, Any]] = []
    for ordinal, (host, sn, discovery) in enumerate(resolved, 1):
        index = int(discovery.get("target_index", ordinal))
        if discovery.get("transport_kind") == "tuya_oem_candidate":
            public_targets.append(_public_target(index, discovery, "tuya-lan"))
            continue
        try:
            protocol, _attempts = tsun_dump.detect_protocol(
                "auto",
                host,
                args.port,
                sn,
                args.timeout,
                discovery.get("protocol_hint"),
            )
        except Exception as exc:
            public = _public_target(index, discovery, None)
            public["initial_detection_error"] = _safe_error(exc)
            public_targets.append(public)
            continue
        public_targets.append(_public_target(index, discovery, protocol))
        if protocol == "02b0":
            private_targets.append(
                {
                    "device_index": index,
                    "host_private": host,
                    "sn_private": sn,
                }
            )
    return private_targets, public_targets, resolution


def _round_failure(device_result: dict[str, Any]) -> bool:
    return not (
        _succeeded(device_result.get("minimal", {}))
        and _succeeded(device_result.get("production", {}))
    )


def summarize_rounds(
    public_targets: list[dict[str, Any]], rounds: list[dict[str, Any]]
) -> dict[str, Any]:
    per_device: list[dict[str, Any]] = []
    for target in public_targets:
        index = int(target["device_index"])
        observations = [
            device
            for round_item in rounds
            for device in round_item.get("devices", [])
            if device.get("device_index") == index
        ]
        if target.get("protocol") != "02b0":
            per_device.append(
                {
                    "device_index": index,
                    "protocol": target.get("protocol"),
                    "observed_rounds": 0,
                    "reason": "observer currently targets 02B0 only",
                }
            )
            continue
        failures = sum(_round_failure(item) for item in observations)
        per_device.append(
            {
                "device_index": index,
                "protocol": "02b0",
                "observed_rounds": len(observations),
                "failed_rounds": failures,
                "successful_rounds": len(observations) - failures,
                "deep_captures": sum("deep_capture" in item for item in observations),
            }
        )

    simultaneous: list[dict[str, Any]] = []
    for round_item in rounds:
        failed = [
            int(item["device_index"])
            for item in round_item.get("devices", [])
            if _round_failure(item)
        ]
        if len(failed) >= 2:
            simultaneous.append(
                {
                    "round": round_item.get("round"),
                    "timestamp_utc": round_item.get("timestamp_utc"),
                    "failed_device_indexes": failed,
                }
            )
    return {
        "devices": per_device,
        "simultaneous_failure_rounds": simultaneous,
    }


def observe(args: argparse.Namespace) -> dict[str, Any]:
    private_targets, public_targets, resolution = _detect_observation_targets(args)
    if not private_targets:
        raise RuntimeError("No 02B0 logger was resolved for observation")

    duration_seconds = args.observe * 60.0
    started_utc = datetime.now(timezone.utc)
    started_mono = time.monotonic()
    deadline = started_mono + duration_seconds
    rounds: list[dict[str, Any]] = []
    last_deep: dict[int, float] = {}
    deep_count: dict[int, int] = {}
    interrupted = False
    round_number = 0

    print(
        f"Observing {len(private_targets)} 02B0 device(s) for {args.observe:g} min "
        f"with a {args.interval:g} s target interval."
    )
    print("No IP address or Monitor SN will be written to the report.")

    try:
        while True:
            now = time.monotonic()
            if round_number > 0 and now >= deadline:
                break
            round_number += 1
            round_started = time.monotonic()
            round_item: dict[str, Any] = {
                "round": round_number,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "devices": [],
            }
            for target in private_targets:
                index = int(target["device_index"])
                host = str(target["host_private"])
                sn = int(target["sn_private"])
                device_item: dict[str, Any] = {
                    "device_index": index,
                    "tcp": _tcp_probe(host, args.port, min(args.timeout, 3.0)),
                }
                baseline: dict[str, dict[str, Any]] = {}
                for test_id, start, end, sensor_list in BASELINE_CASES:
                    baseline[test_id] = _read_case(
                        host, args.port, sn, start, end, sensor_list, args.timeout
                    )
                device_item["minimal"] = baseline["minimal_1"]
                device_item["production"] = baseline["production_23"]

                if _round_failure(device_item):
                    last = last_deep.get(index, float("-inf"))
                    count = deep_count.get(index, 0)
                    if (
                        time.monotonic() - last >= DEEP_CAPTURE_COOLDOWN_SECONDS
                        and count < MAX_DEEP_CAPTURES_PER_DEVICE
                    ):
                        print(
                            f"  Device #{index}: failure detected, running bounded deep capture..."
                        )
                        device_item["deep_capture"] = _deep_capture(
                            host, args.port, sn, args.timeout
                        )
                        last_deep[index] = time.monotonic()
                        deep_count[index] = count + 1
                round_item["devices"].append(device_item)

            rounds.append(round_item)
            failed_indexes = [
                item["device_index"]
                for item in round_item["devices"]
                if _round_failure(item)
            ]
            if failed_indexes:
                print(
                    f"Round {round_number}: failure on device(s) "
                    + ", ".join(f"#{index}" for index in failed_indexes)
                )
            elif round_number == 1 or round_number % 10 == 0:
                print(f"Round {round_number}: all observed 02B0 devices answered")

            if time.monotonic() >= deadline:
                break
            next_start = round_started + args.interval
            remaining = next_start - time.monotonic()
            if remaining > 0:
                time.sleep(min(remaining, max(0.0, deadline - time.monotonic())))
    except KeyboardInterrupt:
        interrupted = True
        print("\nObservation interrupted; saving the evidence collected so far.")

    ended_utc = datetime.now(timezone.utc)
    report = {
        "format": REPORT_FORMAT,
        "schema_version": 1,
        "metadata": {
            "observer_version": OBSERVER_VERSION,
            "tsun_dump_version": tsun_dump.TOOL_VERSION,
            "started_utc": started_utc.isoformat(),
            "ended_utc": ended_utc.isoformat(),
            "requested_duration_minutes": args.observe,
            "interval_seconds": args.interval,
            "interrupted": interrupted,
            "read_only": True,
            "privacy": {
                "host_in_output": False,
                "logger_sn_in_output": False,
                "full_inverter_serial_in_output": False,
            },
        },
        "test_plan": {
            "baseline": [
                {
                    "id": test_id,
                    "function": "0x03",
                    "start": f"0x{start:04X}",
                    "end": f"0x{end:04X}",
                    "register_count": end - start + 1,
                    "sensor_list": f"0x{sensor_list:04X}",
                }
                for test_id, start, end, sensor_list in BASELINE_CASES
            ],
            "deep_capture_on_failure": [
                {
                    "id": test_id,
                    "function": "0x03",
                    "start": f"0x{start:04X}",
                    "end": f"0x{end:04X}",
                    "register_count": end - start + 1,
                    "sensor_list": f"0x{sensor_list:04X}",
                }
                for test_id, start, end, sensor_list in DEEP_CASES
            ],
            "deep_capture_cooldown_seconds": DEEP_CAPTURE_COOLDOWN_SECONDS,
            "max_deep_captures_per_device": MAX_DEEP_CAPTURES_PER_DEVICE,
            "fresh_connection_per_read": True,
        },
        "discovery_summary": resolution,
        "devices": public_targets,
        "rounds": rounds,
        "summary": summarize_rounds(public_targets, rounds),
    }
    return report


def _default_output() -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return Path(f"tsun_02b0_observation_{stamp}.json")


def _upload(path: Path, args: argparse.Namespace) -> None:
    if not args.tester_name.strip() or not args.device:
        raise report_upload.ReportUploadError(
            "--submit requires --tester-name and at least one --device MODEL[:QTY]"
        )

    def progress(attempt: int, attempts: int, delay: float) -> None:
        print(
            f"Upload attempt {attempt}/{attempts} failed transiently; "
            f"retrying in {delay:g} s..."
        )

    receipt = report_upload_retry.upload_file_with_retry(
        path,
        consent=True,
        tester_name=args.tester_name,
        declared_devices=args.device,
        user_agent=f"TSUN-Local-02B0-Observer/{OBSERVER_VERSION}",
        on_retry=progress,
    )
    print(f"Upload accepted · report ID {receipt.get('report_id', '?')}")
    if receipt.get("view_url"):
        print(f"Secure report link: {receipt['view_url']}")


def main() -> int:
    if sys.version_info < (3, 10):
        print("ERROR: Python 3.10 or newer is required.", file=sys.stderr)
        return 2
    args = build_parser().parse_args()
    try:
        report = observe(args)
    except (EOFError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    output = args.output or _default_output()
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        print(f"ERROR: could not save observation: {exc}", file=sys.stderr)
        return 1

    print(f"Observation report saved: {output}")
    summary = report["summary"]
    simultaneous = summary.get("simultaneous_failure_rounds", [])
    print(f"Simultaneous multi-device failure rounds: {len(simultaneous)}")

    if args.submit:
        try:
            _upload(output, args)
        except report_upload.ReportUploadError as exc:
            print(f"Secure upload failed: {exc}", file=sys.stderr)
            print(f"The observation remains saved locally as {output}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
