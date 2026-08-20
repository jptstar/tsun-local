#!/usr/bin/env python3
# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Create privacy-safe, strictly read-only TSUN hardware validation dumps.

The tool intentionally implements no inverter write operation. It reuses the
same read-only protocol clients as TSUN Local and records raw register values
alongside the already-known decoded measurements.
"""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime
import getpass
import importlib.util
import json
from pathlib import Path
import re
import socket
import subprocess
import sys
import time
from typing import Any, Iterable


TOOL_VERSION = "1.0.0"
DUMP_FORMAT = "tsun-local-hardware-dump"
SCHEMA_VERSION = 1
DEFAULT_PORT = 8899
DEFAULT_DISCOVERY_PORT = 48899
DEFAULT_DISCOVERY_TIMEOUT = 4.0
DEFAULT_SNAPSHOTS = 3
DEFAULT_SNAPSHOT_INTERVAL = 3.0
MAX_MODBUS_REGISTERS_PER_READ = 16
DISCOVERY_MESSAGES = (
    b"WIFIKIT-214028-READ",
    b"HF-A11ASSISTHREAD",
    b"devicelinkfind",
)
_SERIAL_TOKEN = re.compile(r"(?<!\d)(\d{8,10})(?!\d)")
_SAFE_NAME = re.compile(r"[^a-z0-9._-]+")

PROTOCOLS_PATH = (
    Path(__file__).parents[1] / "custom_components" / "tsun_local" / "protocols"
)
SPEC = importlib.util.spec_from_file_location(
    "tsun_local_dump_capture",
    PROTOCOLS_PATH / "__init__.py",
    submodule_search_locations=[str(PROTOCOLS_PATH)],
)
assert SPEC is not None and SPEC.loader is not None
PROTOCOLS = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PROTOCOLS
SPEC.loader.exec_module(PROTOCOLS)

from tsun_local_dump_capture import (  # noqa: E402
    DEFAULT_PROTOCOL,
    SUPPORTED_PROTOCOLS,
    create_protocol_client,
)
from tsun_local_dump_capture.ap import safe_error_details  # noqa: E402
from tsun_local_dump_capture.protocol_02b0 import Tsun02b0Client  # noqa: E402
from tsun_local_dump_capture.protocol_1097 import Tsun1097Client  # noqa: E402
from tsun_local_dump_capture.protocol_1511 import Tsun1511Client  # noqa: E402


@dataclass(slots=True)
class DiscoveryDevice:
    """One logger discovered on the local network."""

    host: str
    serial_candidates: set[int] = field(default_factory=set)
    replies: int = 0


def _valid_monitor_sn(value: int) -> bool:
    """Return whether a value fits the four-byte logger field."""
    return 0 < value <= 0xFFFFFFFF


def _serial_candidates_from_object(value: Any, key_hint: str = "") -> set[int]:
    """Collect plausible logger numbers from a decoded discovery object."""
    found: set[int] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            found.update(_serial_candidates_from_object(child, str(key).lower()))
        return found
    if isinstance(value, list):
        for child in value:
            found.update(_serial_candidates_from_object(child, key_hint))
        return found

    if any(token in key_hint for token in ("serial", "logger", "monitor", "sn")):
        try:
            candidate = int(str(value).strip())
        except (TypeError, ValueError):
            return found
        if _valid_monitor_sn(candidate):
            found.add(candidate)
    return found


def serial_candidates_from_payload(payload: bytes) -> set[int]:
    """Extract plausible Monitor SN values from a local discovery reply."""
    text = payload.decode("utf-8", errors="replace").strip("\x00\r\n ")
    found: set[int] = set()
    try:
        parsed = json.loads(text)
    except (TypeError, ValueError):
        parsed = None
    if parsed is not None:
        found.update(_serial_candidates_from_object(parsed))

    # Several logger generations answer with simple CSV/text rather than JSON.
    # Restrict the fallback to 8-10 digit values that still fit the four-byte
    # AP envelope field. Ambiguous results are never selected automatically.
    if parsed is None:
        for match in _SERIAL_TOKEN.finditer(text):
            candidate = int(match.group(1))
            if _valid_monitor_sn(candidate):
                found.add(candidate)
    return found


def discover_devices(
    *,
    port: int = DEFAULT_DISCOVERY_PORT,
    timeout: float = DEFAULT_DISCOVERY_TIMEOUT,
) -> list[DiscoveryDevice]:
    """Discover local loggers with read-only UDP probes."""
    devices: dict[str, DiscoveryDevice] = {}
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    try:
        sock.bind(("", port))
        for message in DISCOVERY_MESSAGES:
            sock.sendto(message, ("255.255.255.255", port))

        deadline = time.monotonic() + timeout
        while (remaining := deadline - time.monotonic()) > 0:
            sock.settimeout(remaining)
            try:
                payload, (source, _source_port) = sock.recvfrom(4096)
            except socket.timeout:
                break
            if payload in DISCOVERY_MESSAGES:
                continue
            device = devices.setdefault(source, DiscoveryDevice(host=source))
            device.replies += 1
            device.serial_candidates.update(serial_candidates_from_payload(payload))
    except OSError:
        # Discovery is convenience only. The caller falls back to manual data.
        return []
    finally:
        sock.close()
    return sorted(devices.values(), key=lambda item: item.host)


def _positive_port(value: str) -> int:
    port = int(value)
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("port must be between 1 and 65535")
    return port


def _positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("value must be at least 1")
    return number


def _non_negative_float(value: str) -> float:
    number = float(value)
    if number < 0:
        raise argparse.ArgumentTypeError("value must not be negative")
    return number


def _monitor_sn_arg(value: str) -> int:
    number = int(value)
    if not _valid_monitor_sn(number):
        raise argparse.ArgumentTypeError("Monitor SN must fit an unsigned 32-bit value")
    return number


def _prompt_monitor_sn() -> int:
    """Prompt without echoing the Monitor SN into the terminal."""
    while True:
        value = getpass.getpass("Numeric Monitor SN: ").strip()
        try:
            number = int(value)
        except ValueError:
            print("Monitor SN must be numeric.")
            continue
        if _valid_monitor_sn(number):
            return number
        print("Monitor SN must be between 1 and 4294967295.")


def resolve_target(args: argparse.Namespace) -> tuple[str, int, dict[str, Any]]:
    """Resolve host and Monitor SN by discovery, then manual fallback."""
    host = args.host
    monitor_sn = args.serial
    report: dict[str, Any] = {
        "attempted": False,
        "devices_found": 0,
        "host_discovered": False,
        "monitor_sn_discovered": False,
    }

    selected: DiscoveryDevice | None = None
    if host is None or monitor_sn is None:
        print("Searching the local network for TSUN loggers (read-only UDP)...")
        report["attempted"] = True
        devices = discover_devices(timeout=args.discovery_timeout)
        report["devices_found"] = len(devices)

        if host is not None:
            selected = next((item for item in devices if item.host == host), None)
        elif len(devices) == 1:
            selected = devices[0]
        elif len(devices) > 1:
            print(f"{len(devices)} candidate loggers found:")
            for index, item in enumerate(devices, 1):
                sn_state = "SN found" if len(item.serial_candidates) == 1 else "SN unresolved"
                print(f"  {index}. {item.host} ({sn_state})")
            while selected is None:
                answer = input("Select logger number: ").strip()
                try:
                    index = int(answer)
                except ValueError:
                    continue
                if 1 <= index <= len(devices):
                    selected = devices[index - 1]

        if selected is not None:
            if host is None:
                host = selected.host
                report["host_discovered"] = True
            if monitor_sn is None and len(selected.serial_candidates) == 1:
                monitor_sn = next(iter(selected.serial_candidates))
                report["monitor_sn_discovered"] = True

    if host is None:
        host = input("Logger IP address: ").strip()
    if not host:
        raise ValueError("A logger IP address is required")
    if monitor_sn is None:
        print("Monitor SN could not be resolved automatically.")
        monitor_sn = _prompt_monitor_sn()

    return host, monitor_sn, report


def split_modbus_range(start: int, end: int) -> list[tuple[int, int, int]]:
    """Split one safe Modbus range into conservative FC03 reads."""
    blocks: list[tuple[int, int, int]] = []
    cursor = start
    while cursor <= end:
        chunk_end = min(end, cursor + MAX_MODBUS_REGISTERS_PER_READ - 1)
        blocks.append((0x03, cursor, chunk_end))
        cursor = chunk_end + 1
    return blocks


def capture_plans(protocol: str, full: bool) -> tuple[list[tuple], list[tuple]]:
    """Return dynamic snapshot blocks and static/supplemental blocks."""
    if protocol == "02b0":
        dynamic = split_modbus_range(0x3000, 0x302F)
        if full:
            supplemental = split_modbus_range(0x2000, 0x204F)
        else:
            supplemental = [
                (0x03, 0x2007, 0x2007),
                *split_modbus_range(0x2014, 0x202C),
            ]
        return dynamic, supplemental

    if protocol == "1097":
        dynamic = [
            *split_modbus_range(0x1100, 0x110F),
            *split_modbus_range(0x1200, 0x121F),
            *split_modbus_range(0x1300, 0x132F),
        ]
        if full:
            supplemental = [
                *split_modbus_range(0x1008, 0x100F),
                *split_modbus_range(0x1400, 0x143F),
            ]
        else:
            supplemental = [
                *split_modbus_range(0x1008, 0x100F),
                (0x03, 0x1400, 0x1400),
                (0x03, 0x1423, 0x1423),
                (0x03, 0x1437, 0x1437),
            ]
        return dynamic, supplemental

    if protocol == "1511":
        # Native TITAN reads only. These are the same read-only blocks used by
        # TSUN Local and by the published MP3000 field-validation captures.
        dynamic = [
            (0xA1, 0x01, 0x0BB8, 0x0BD7),
            (0xA2, 0x02, 0x0CE4, 0x0CE7),
            (0xA3, 0x03, 0x0E10, 0x0E2D),
            (0xA4, 0x04, 0x0ED8, 0x0EF5),
        ]
        supplemental = [(0xA1, 0x21, 0x07D0, 0x082F)]
        return dynamic, supplemental

    raise ValueError(f"Unsupported protocol: {protocol}")


def _specific_client(protocol: str, host: str, port: int, monitor_sn: int):
    if protocol == "02b0":
        return Tsun02b0Client(host, port, monitor_sn)
    if protocol == "1097":
        return Tsun1097Client(host, port, monitor_sn)
    if protocol == "1511":
        return Tsun1511Client(host, port, monitor_sn)
    raise ValueError(f"Unsupported protocol: {protocol}")


def register_key(protocol: str, block: tuple, address: int) -> str:
    """Return a stable raw-register key, preserving 1511 native context."""
    if protocol == "1511":
        address_tag, function, _start, _end = block
        return f"{address_tag:02X}/{function:02X}:0x{address:04X}"
    return f"0x{address:04X}"


def _block_descriptor(protocol: str, block: tuple) -> dict[str, Any]:
    if protocol == "1511":
        address_tag, function, start, end = block
        return {
            "address_tag": f"0x{address_tag:02X}",
            "function": f"0x{function:02X}",
            "start": f"0x{start:04X}",
            "end": f"0x{end:04X}",
        }
    function, start, end = block
    return {
        "function": f"0x{function:02X}",
        "start": f"0x{start:04X}",
        "end": f"0x{end:04X}",
    }


async def read_plan(client, protocol: str, plan: Iterable[tuple]) -> tuple[dict[str, int], list[dict[str, Any]]]:
    """Read a plan while retaining successful blocks if another block fails."""
    registers: dict[str, int] = {}
    blocks: list[dict[str, Any]] = []
    for block in plan:
        record = _block_descriptor(protocol, block)
        try:
            values = await client._read_block(block)  # Same internal read path as the integration.
        except Exception as err:
            record["result"] = "failure"
            record["error"] = safe_error_details(err)
        else:
            record["result"] = "success"
            record["register_count"] = len(values)
            record["registers"] = [
                {
                    "key": register_key(protocol, block, address),
                    "address": address,
                    "address_hex": f"0x{address:04X}",
                    "raw_decimal": value,
                    "raw_hex": f"0x{value:04X}",
                }
                for address, value in sorted(values.items())
            ]
            for address, value in values.items():
                registers[register_key(protocol, block, address)] = value
        blocks.append(record)
    return registers, blocks


def analyze_snapshots(snapshots: list[dict[str, Any]]) -> dict[str, list[str]]:
    """Classify raw register behavior across complete snapshot observations."""
    if not snapshots:
        return {
            "changing_registers": [],
            "stable_registers": [],
            "zero_registers": [],
            "ffff_registers": [],
            "incomplete_registers": [],
        }

    maps = [snapshot.get("registers", {}) for snapshot in snapshots]
    all_keys = sorted(set().union(*(mapping.keys() for mapping in maps)))
    changing: list[str] = []
    stable: list[str] = []
    zero: list[str] = []
    ffff: list[str] = []
    incomplete: list[str] = []

    for key in all_keys:
        if not all(key in mapping for mapping in maps):
            incomplete.append(key)
            continue
        values = [mapping[key] for mapping in maps]
        if len(set(values)) > 1:
            changing.append(key)
        elif values[0] == 0:
            zero.append(key)
        elif values[0] == 0xFFFF:
            ffff.append(key)
        else:
            stable.append(key)

    return {
        "changing_registers": changing,
        "stable_registers": stable,
        "zero_registers": zero,
        "ffff_registers": ffff,
        "incomplete_registers": incomplete,
    }


def _repository_version() -> str | None:
    manifest = Path(__file__).parents[1] / "custom_components" / "tsun_local" / "manifest.json"
    try:
        return str(json.loads(manifest.read_text(encoding="utf-8"))["version"])
    except (OSError, KeyError, TypeError, ValueError):
        return None


def _git_commit() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=Path(__file__).parents[1],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=2,
        ).strip()
    except (OSError, subprocess.SubprocessError):
        return None


def _safe_filename_part(value: str) -> str:
    normalized = _SAFE_NAME.sub("-", value.lower()).strip("-._")
    return normalized or "unknown"


def default_output_path(model: str | None, protocol: str, timestamp: datetime) -> Path:
    stamp = timestamp.strftime("%Y%m%dT%H%M%SZ")
    model_part = _safe_filename_part(model or "unknown")
    return Path(f"tsun_{model_part}_{protocol}_{stamp}.json")


def _flatten_raw_registers(registers: dict[str, int]) -> list[dict[str, Any]]:
    return [
        {
            "key": key,
            "raw_decimal": value,
            "raw_hex": f"0x{value:04X}",
        }
        for key, value in sorted(registers.items())
    ]


async def capture(args: argparse.Namespace, host: str, monitor_sn: int, discovery: dict[str, Any]) -> dict[str, Any]:
    """Detect the protocol and create a complete hardware-validation document."""
    detection_client = create_protocol_client(args.protocol, host, args.port, monitor_sn)
    detection_result = await detection_client.async_read_all()
    protocol = detection_client.protocol_name
    if protocol not in SUPPORTED_PROTOCOLS:
        raise RuntimeError("Protocol detection did not select a supported adapter")

    dynamic_plan, supplemental_plan = capture_plans(protocol, args.full)
    raw_client = _specific_client(protocol, host, args.port, monitor_sn)

    supplemental_registers, supplemental_blocks = await read_plan(
        raw_client, protocol, supplemental_plan
    )

    snapshots: list[dict[str, Any]] = []
    snapshot_blocks: list[dict[str, Any]] = []
    for index in range(args.snapshots):
        registers, blocks = await read_plan(raw_client, protocol, dynamic_plan)
        snapshots.append(
            {
                "index": index + 1,
                "timestamp_utc": datetime.now(UTC).isoformat(),
                "registers": registers,
            }
        )
        for block in blocks:
            block["snapshot"] = index + 1
            snapshot_blocks.append(block)
        if index + 1 < args.snapshots and args.interval:
            await asyncio.sleep(args.interval)

    latest_dynamic = snapshots[-1]["registers"] if snapshots else {}
    merged_registers = {**supplemental_registers, **latest_dynamic}
    all_blocks = [
        *({**block, "snapshot": None, "scope": "supplemental"} for block in supplemental_blocks),
        *({**block, "scope": "dynamic"} for block in snapshot_blocks),
    ]
    successful_blocks = sum(block["result"] == "success" for block in all_blocks)
    failed_blocks = len(all_blocks) - successful_blocks
    created_at = datetime.now(UTC)

    document: dict[str, Any] = {
        "format": DUMP_FORMAT,
        "schema_version": SCHEMA_VERSION,
        "metadata": {
            "timestamp_utc": created_at.isoformat(),
            "tool": "TSUN Local Hardware Validation Dump Tool",
            "tool_version": TOOL_VERSION,
            "tsun_local_version": _repository_version(),
            "git_commit": _git_commit(),
            "read_only": True,
            "capture_mode": "full" if args.full else "standard",
            "detected_protocol": protocol,
            "model_family": detection_client.model,
            "model_supplied_by_user": args.model,
            "pv_count": detection_client.pv_count,
            "port": args.port,
            "privacy": {
                "host_in_output": False,
                "logger_sn_in_output": False,
                "inverter_serial_in_output": False,
                "ap_envelope_in_output": False,
                "udp_discovery_payload_in_output": False,
            },
        },
        "discovery": discovery,
        "protocol_detection": {
            "requested": args.protocol,
            "selected": protocol,
            "confidence": "direct successful protocol read",
            "initial_poll_duration_ms": detection_result.duration_ms,
            "initial_poll_blocks_ok": detection_result.blocks_ok,
        },
        "decoded_known_measurements": detection_result.measurements,
        "capture_summary": {
            "snapshots": len(snapshots),
            "snapshot_interval_seconds": args.interval,
            "successful_block_reads": successful_blocks,
            "failed_block_reads": failed_blocks,
            "unique_raw_registers": len(merged_registers),
        },
        "raw_registers": _flatten_raw_registers(merged_registers),
        "snapshots": snapshots,
        "analysis": analyze_snapshots(snapshots),
        "blocks": all_blocks,
        "protocol_trace": list(raw_client.diagnostic_trace),
    }
    return document


def _raw_map(document: dict[str, Any]) -> dict[str, int]:
    result: dict[str, int] = {}
    for item in document.get("raw_registers", []):
        if isinstance(item, dict) and "key" in item and "raw_decimal" in item:
            result[str(item["key"])] = int(item["raw_decimal"])
    return result


def compare_documents(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    """Compare two dump documents without assigning semantics to raw changes."""
    before_map = _raw_map(before)
    after_map = _raw_map(after)
    common = sorted(before_map.keys() & after_map.keys())
    changed = [
        {
            "key": key,
            "before": before_map[key],
            "before_hex": f"0x{before_map[key]:04X}",
            "after": after_map[key],
            "after_hex": f"0x{after_map[key]:04X}",
        }
        for key in common
        if before_map[key] != after_map[key]
    ]
    return {
        "format": "tsun-local-dump-comparison",
        "schema_version": 1,
        "before_protocol": before.get("metadata", {}).get("detected_protocol"),
        "after_protocol": after.get("metadata", {}).get("detected_protocol"),
        "changed_registers": changed,
        "unchanged_register_count": sum(before_map[key] == after_map[key] for key in common),
        "only_in_before": sorted(before_map.keys() - after_map.keys()),
        "only_in_after": sorted(after_map.keys() - before_map.keys()),
    }


def run_compare(paths: list[Path], output: Path | None) -> int:
    try:
        before = json.loads(paths[0].read_text(encoding="utf-8"))
        after = json.loads(paths[1].read_text(encoding="utf-8"))
    except (OSError, ValueError) as err:
        print(f"Unable to read dumps: {type(err).__name__}")
        return 2

    comparison = compare_documents(before, after)
    changed = comparison["changed_registers"]
    print(f"Changed raw registers: {len(changed)}")
    for item in changed:
        print(f"  {item['key']}: {item['before']} -> {item['after']}")
    if output is not None:
        output.write_text(json.dumps(comparison, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"Comparison saved to: {output.resolve()}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Create a strictly read-only, privacy-safe TSUN hardware validation dump. "
            "Without --host/--serial the tool first tries local UDP discovery."
        )
    )
    parser.add_argument("--host", help="logger IP address; discovered or prompted if omitted")
    parser.add_argument("--serial", type=_monitor_sn_arg, help="numeric Monitor SN; discovered or prompted if omitted")
    parser.add_argument("--port", type=_positive_port, default=DEFAULT_PORT)
    parser.add_argument(
        "--protocol",
        choices=(DEFAULT_PROTOCOL, *SUPPORTED_PROTOCOLS),
        default=DEFAULT_PROTOCOL,
        help="protocol to use; default: auto",
    )
    parser.add_argument("--model", help="optional exact inverter model supplied by the user")
    parser.add_argument(
        "--full",
        action="store_true",
        help="include additional known-safe research ranges; never brute-forces the address space",
    )
    parser.add_argument("--snapshots", type=_positive_int, default=DEFAULT_SNAPSHOTS)
    parser.add_argument("--interval", type=_non_negative_float, default=DEFAULT_SNAPSHOT_INTERVAL)
    parser.add_argument("--discovery-timeout", type=_non_negative_float, default=DEFAULT_DISCOVERY_TIMEOUT)
    parser.add_argument("--output", type=Path, help="output JSON path")
    parser.add_argument(
        "--compare",
        nargs=2,
        type=Path,
        metavar=("BEFORE", "AFTER"),
        help="compare two existing dump JSON files instead of reading hardware",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.compare:
        return run_compare(args.compare, args.output)

    print("TSUN Local Hardware Validation Dump Tool")
    print("READ-ONLY: this tool contains no inverter configuration write path.\n")

    try:
        host, monitor_sn, discovery = resolve_target(args)
        document = asyncio.run(capture(args, host, monitor_sn, discovery))
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.")
        return 130
    except Exception as err:
        print(f"Dump failed: {type(err).__name__}: {err}")
        return 1

    timestamp = datetime.fromisoformat(document["metadata"]["timestamp_utc"])
    output = args.output or default_output_path(
        args.model or document["metadata"].get("model_family"),
        document["metadata"]["detected_protocol"],
        timestamp,
    )
    output.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary = document["capture_summary"]
    print(f"\nProtocol: {document['metadata']['detected_protocol']}")
    print(f"Snapshots: {summary['snapshots']}")
    print(f"Successful block reads: {summary['successful_block_reads']}")
    print(f"Failed block reads: {summary['failed_block_reads']}")
    print(f"Unique raw registers: {summary['unique_raw_registers']}")
    print("Writes: 0")
    print("Privacy: IP address and Monitor SN are not stored in the JSON")
    print(f"Output: {output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
