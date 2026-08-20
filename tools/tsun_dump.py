#!/usr/bin/env python3
# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Standalone, privacy-safe, strictly read-only TSUN hardware dump tool.

The tool uses only the Python standard library. It implements read paths only
for the local TSUN protocol families currently researched by TSUN Local:
1511, 02B0 and 1097.

Without --host, every TSUN logger discovered on the local network is captured
and written to a separate JSON file. --host intentionally switches to a single
logger. No Modbus write function and no inverter configuration command exists
in this file.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import UTC, datetime
import getpass
import hashlib
import json
from pathlib import Path
import re
import socket
import sys
import time
from typing import Any, Iterable

TOOL_VERSION = "2.1.0"
DUMP_FORMAT = "tsun-local-hardware-dump"
SCHEMA_VERSION = 2
SOURCE_URL = "https://raw.githubusercontent.com/jptstar/tsun-local/main/tools/tsun_dump.py"
DEFAULT_PORT = 8899
DEFAULT_DISCOVERY_PORT = 48899
DEFAULT_DISCOVERY_TIMEOUT = 4.0
DEFAULT_TIMEOUT = 6.0
DEFAULT_SNAPSHOTS = 3
DEFAULT_SNAPSHOT_INTERVAL = 3.0
MAX_MODBUS_REGISTERS_PER_READ = 16
SUPPORTED_PROTOCOLS = ("1511", "02b0", "1097")
DISCOVERY_MESSAGES = (
    b"WIFIKIT-214028-READ",
    b"HF-A11ASSISTHREAD",
    b"devicelinkfind",
)
_SERIAL_TOKEN = re.compile(r"(?<!\d)(\d{8,10})(?!\d)")
_SAFE_NAME = re.compile(r"[^a-z0-9._-]+")


class TsunProtocolError(Exception):
    """Raised when a TSUN protocol frame is invalid."""


@dataclass(slots=True)
class DiscoveryDevice:
    """One logger discovered on the local network."""

    host: str
    serial_candidates: set[int] = field(default_factory=set)
    replies: int = 0


def safe_error_details(error: Exception) -> dict[str, str]:
    """Return error details without addresses, serials or payload identifiers."""
    result = {"type": type(error).__name__}
    if isinstance(error, TsunProtocolError):
        result["detail"] = str(error)
    return result


# ---------------------------------------------------------------------------
# AP envelope + protocol framing (READ ONLY)
# ---------------------------------------------------------------------------

def checksum_ap(data: bytes) -> int:
    return sum(data) & 0xFF


def build_ap_frame(logger_sn: int, payload: bytes, sensor_list: int = 0) -> bytes:
    """Wrap one read payload in the local TSUN AP envelope."""
    data = b"\x02" + sensor_list.to_bytes(2, "little") + bytes(12) + payload
    scope = (
        len(data).to_bytes(2, "little")
        + b"\x10\x45\x00\x00"
        + logger_sn.to_bytes(4, "little")
        + data
    )
    return b"\xA5" + scope + bytes((checksum_ap(scope), 0x15))


def _recv_exact(sock: socket.socket, count: int) -> bytes:
    data = bytearray()
    while len(data) < count:
        chunk = sock.recv(count - len(data))
        if not chunk:
            raise TsunProtocolError("Unexpected end of TCP stream")
        data.extend(chunk)
    return bytes(data)


def read_ap_frame(sock: socket.socket) -> bytes:
    header = _recv_exact(sock, 3)
    if header[0] != 0xA5:
        raise TsunProtocolError("Invalid AP start marker")
    remaining = int.from_bytes(header[1:3], "little") + 10
    return header + _recv_exact(sock, remaining)


def parse_ap_frame(frame: bytes) -> bytes:
    if len(frame) < 27 or frame[0] != 0xA5 or frame[-1] != 0x15:
        raise TsunProtocolError("Invalid AP frame markers or length")
    expected = int.from_bytes(frame[1:3], "little") + 13
    if len(frame) != expected:
        raise TsunProtocolError("Invalid AP frame length")
    if checksum_ap(frame[1:-2]) != frame[-2]:
        raise TsunProtocolError("Invalid AP checksum")
    if frame[11] != 0x02:
        raise TsunProtocolError("Unexpected AP frame type")
    if frame[12] != 0x01:
        raise TsunProtocolError(f"AP returned status 0x{frame[12]:02X}")
    return frame[25:-2]


def crc16_modbus(data: bytes) -> bytes:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc.to_bytes(2, "little")


def build_modbus_request(start: int, end: int) -> bytes:
    """Build an FC03 register read. No write function is implemented."""
    count = end - start + 1
    body = b"\x01\x03" + start.to_bytes(2, "big") + count.to_bytes(2, "big")
    return body + crc16_modbus(body)


def parse_modbus_response(frame: bytes, start: int, end: int) -> dict[int, int]:
    if len(frame) < 5 or frame[0] != 0x01:
        raise TsunProtocolError("Invalid Modbus frame")
    if crc16_modbus(frame[:-2]) != frame[-2:]:
        raise TsunProtocolError("Invalid Modbus CRC")
    if frame[1] == 0x83:
        raise TsunProtocolError(f"Modbus exception 0x{frame[2]:02X}")
    if frame[1] != 0x03:
        raise TsunProtocolError("Unexpected Modbus function")
    count = end - start + 1
    data_length = frame[2]
    if data_length != count * 2 or len(frame) != 3 + data_length + 2:
        raise TsunProtocolError("Unexpected Modbus data length")
    values = frame[3 : 3 + data_length]
    return {
        start + index: int.from_bytes(values[index * 2 : index * 2 + 2], "big")
        for index in range(count)
    }


def crc16_1511(data: bytes) -> bytes:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc.to_bytes(2, "big")


def build_1511_request(address_tag: int, function: int, start: int, end: int) -> bytes:
    count = end - start + 1
    body = bytes((address_tag, function, 0x00)) + start.to_bytes(2, "big")
    body += b"\x00\x02" + count.to_bytes(2, "big")
    return body + crc16_1511(body)


def parse_1511_response(
    frame: bytes, address_tag: int, function: int, start: int, end: int
) -> dict[int, int]:
    if len(frame) < 11 or frame[0] != 0x7E:
        raise TsunProtocolError("Invalid 1511 frame")
    if crc16_1511(frame[1:-2]) != frame[-2:]:
        raise TsunProtocolError("Invalid 1511 CRC")
    if frame[1] != address_tag or frame[2] != (function | 0x80):
        raise TsunProtocolError("Unexpected 1511 address or response function")
    if frame[3] != 0x01:
        raise TsunProtocolError(f"1511 returned status 0x{frame[3]:02X}")
    if int.from_bytes(frame[4:6], "big") != start:
        raise TsunProtocolError("Unexpected 1511 start address")
    data_length = int.from_bytes(frame[6:8], "big")
    count = end - start + 1
    if data_length != count * 2 or len(frame) != 8 + data_length + 2:
        raise TsunProtocolError("Unexpected 1511 data length")
    values = frame[8 : 8 + data_length]
    return {
        start + index: int.from_bytes(values[index * 2 : index * 2 + 2], "little")
        for index in range(count)
    }


def exchange_ap(
    host: str,
    port: int,
    logger_sn: int,
    payload: bytes,
    *,
    sensor_list: int = 0,
    timeout: float = DEFAULT_TIMEOUT,
) -> bytes:
    request = build_ap_frame(logger_sn, payload, sensor_list=sensor_list)
    with socket.create_connection((host, port), timeout=timeout) as sock:
        sock.settimeout(timeout)
        sock.sendall(request)
        return parse_ap_frame(read_ap_frame(sock))


def read_modbus_block(
    host: str,
    port: int,
    logger_sn: int,
    start: int,
    end: int,
    *,
    sensor_list: int,
    timeout: float,
) -> tuple[dict[int, int], bytes, bytes]:
    payload = build_modbus_request(start, end)
    response = exchange_ap(
        host, port, logger_sn, payload, sensor_list=sensor_list, timeout=timeout
    )
    return parse_modbus_response(response, start, end), payload, response


def read_1511_block(
    host: str,
    port: int,
    logger_sn: int,
    address_tag: int,
    function: int,
    start: int,
    end: int,
    *,
    timeout: float,
) -> tuple[dict[int, int], bytes, bytes]:
    payload = build_1511_request(address_tag, function, start, end)
    response = exchange_ap(host, port, logger_sn, payload, timeout=timeout)
    return (
        parse_1511_response(response, address_tag, function, start, end),
        payload,
        response,
    )


# ---------------------------------------------------------------------------
# Network discovery / target resolution
# ---------------------------------------------------------------------------

def _valid_monitor_sn(value: int) -> bool:
    return 0 < value <= 0xFFFFFFFF


def _serial_candidates_from_object(value: Any, key_hint: str = "") -> set[int]:
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
    """Extract plausible Monitor SN values from a discovery response."""
    text = payload.decode("utf-8", errors="replace").strip("\x00\r\n ")
    found: set[int] = set()
    try:
        parsed = json.loads(text)
    except (TypeError, ValueError):
        parsed = None
    if parsed is not None:
        found.update(_serial_candidates_from_object(parsed))
    else:
        for match in _SERIAL_TOKEN.finditer(text):
            candidate = int(match.group(1))
            if _valid_monitor_sn(candidate):
                found.add(candidate)
    return found


def discover_devices(
    *, port: int = DEFAULT_DISCOVERY_PORT, timeout: float = DEFAULT_DISCOVERY_TIMEOUT
) -> list[DiscoveryDevice]:
    """Return every logger answering the read-only UDP discovery probes."""
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
        return []
    finally:
        sock.close()
    return sorted(devices.values(), key=lambda item: tuple(int(p) for p in item.host.split(".")))


def _prompt_monitor_sn(prompt: str = "Monitor SN: ", *, allow_skip: bool = False) -> int | None:
    while True:
        answer = getpass.getpass(prompt).strip()
        if allow_skip and not answer:
            return None
        try:
            number = int(answer)
        except ValueError:
            print("Monitor SN must be numeric." + (" Press Enter to skip." if allow_skip else ""))
            continue
        if _valid_monitor_sn(number):
            return number
        print("Monitor SN must fit the four-byte logger field.")


def resolve_targets(
    args: argparse.Namespace,
) -> tuple[list[tuple[str, int, dict[str, Any]]], dict[str, int]]:
    """Resolve all discovered targets; --host deliberately restricts to one."""
    summary = {"devices_found": 0, "targets_resolved": 0, "targets_skipped": 0}

    # Explicit IP means deliberate single-device mode.
    if args.host is not None:
        host = args.host.strip()
        if not host:
            raise ValueError("A logger IP address is required")
        monitor_sn = args.serial
        report: dict[str, Any] = {
            "attempted": monitor_sn is None,
            "devices_found": 0,
            "host_discovered": False,
            "monitor_sn_discovered": False,
            "target_index": 1,
            "multi_device_scan": False,
        }
        if monitor_sn is None:
            print("Searching the local network for the supplied logger (read-only UDP)...")
            devices = discover_devices(timeout=args.discovery_timeout)
            report["devices_found"] = len(devices)
            summary["devices_found"] = len(devices)
            selected = next((item for item in devices if item.host == host), None)
            if selected is not None and len(selected.serial_candidates) == 1:
                monitor_sn = next(iter(selected.serial_candidates))
                report["monitor_sn_discovered"] = True
        if monitor_sn is None:
            print("Monitor SN could not be resolved automatically.")
            monitor_sn = _prompt_monitor_sn()
        assert monitor_sn is not None
        summary["targets_resolved"] = 1
        return [(host, monitor_sn, report)], summary

    print("Searching the local network for all TSUN loggers (read-only UDP)...")
    devices = discover_devices(timeout=args.discovery_timeout)
    summary["devices_found"] = len(devices)

    # No discovery response: manual fallback for one device.
    if not devices:
        host = input("Logger IP address: ").strip()
        if not host:
            raise ValueError("A logger IP address is required")
        monitor_sn = args.serial
        if monitor_sn is None:
            print("Monitor SN could not be resolved automatically.")
            monitor_sn = _prompt_monitor_sn()
        assert monitor_sn is not None
        report = {
            "attempted": True,
            "devices_found": 0,
            "host_discovered": False,
            "monitor_sn_discovered": False,
            "target_index": 1,
            "multi_device_scan": False,
        }
        summary["targets_resolved"] = 1
        return [(host, monitor_sn, report)], summary

    if args.serial is not None and len(devices) > 1:
        raise ValueError(
            "--serial without --host is ambiguous when multiple loggers are discovered; "
            "omit --serial to scan all devices or add --host for one device"
        )

    print(f"{len(devices)} candidate logger(s) found. Every discovered logger will be captured.")
    targets: list[tuple[str, int, dict[str, Any]]] = []
    multi = len(devices) > 1
    for index, device in enumerate(devices, 1):
        monitor_sn: int | None
        discovered_sn = False
        if len(device.serial_candidates) == 1:
            monitor_sn = next(iter(device.serial_candidates))
            discovered_sn = True
        elif args.serial is not None and len(devices) == 1:
            monitor_sn = args.serial
        else:
            state = "ambiguous" if device.serial_candidates else "missing"
            print(f"Logger {index}/{len(devices)} at {device.host}: Monitor SN {state}.")
            prompt = (
                f"Monitor SN for logger {index}/{len(devices)} at {device.host}"
                + (" (Enter to skip): " if multi else ": ")
            )
            monitor_sn = _prompt_monitor_sn(prompt, allow_skip=multi)
            if monitor_sn is None:
                print(f"Skipping logger {index}/{len(devices)}; no Monitor SN supplied.")
                summary["targets_skipped"] += 1
                continue

        report = {
            "attempted": True,
            "devices_found": len(devices),
            "host_discovered": True,
            "monitor_sn_discovered": discovered_sn,
            "target_index": index,
            "multi_device_scan": multi,
        }
        targets.append((device.host, monitor_sn, report))

    if not targets:
        raise ValueError("No discovered logger has a usable Monitor SN")
    summary["targets_resolved"] = len(targets)
    return targets, summary


# ---------------------------------------------------------------------------
# Capture plans / protocol detection
# ---------------------------------------------------------------------------

def split_modbus_range(start: int, end: int) -> list[tuple[int, int]]:
    blocks: list[tuple[int, int]] = []
    cursor = start
    while cursor <= end:
        chunk_end = min(end, cursor + MAX_MODBUS_REGISTERS_PER_READ - 1)
        blocks.append((cursor, chunk_end))
        cursor = chunk_end + 1
    return blocks


def capture_plans(protocol: str, full: bool) -> tuple[list[tuple], list[tuple]]:
    if protocol == "02b0":
        dynamic = split_modbus_range(0x3000, 0x302F)
        supplemental = (
            split_modbus_range(0x2000, 0x204F)
            if full
            else [(0x2007, 0x2007), *split_modbus_range(0x2014, 0x202C)]
        )
        return dynamic, supplemental
    if protocol == "1097":
        dynamic = [
            *split_modbus_range(0x1100, 0x110F),
            *split_modbus_range(0x1200, 0x121F),
            *split_modbus_range(0x1300, 0x132F),
        ]
        supplemental = (
            [*split_modbus_range(0x1008, 0x100F), *split_modbus_range(0x1400, 0x143F)]
            if full
            else [
                *split_modbus_range(0x1008, 0x100F),
                (0x1400, 0x1400),
                (0x1423, 0x1423),
                (0x1437, 0x1437),
            ]
        )
        return dynamic, supplemental
    if protocol == "1511":
        dynamic = [
            (0xA1, 0x01, 0x0BB8, 0x0BD7),
            (0xA2, 0x02, 0x0CE4, 0x0CE7),
            (0xA3, 0x03, 0x0E10, 0x0E2D),
            (0xA4, 0x04, 0x0ED8, 0x0EF5),
        ]
        return dynamic, [(0xA1, 0x21, 0x07D0, 0x082F)]
    raise ValueError(f"Unsupported protocol: {protocol}")


def _probe_protocol(protocol: str, host: str, port: int, sn: int, timeout: float) -> None:
    if protocol == "1511":
        read_1511_block(host, port, sn, 0xA1, 0x01, 0x0BB8, 0x0BB8, timeout=timeout)
    elif protocol == "02b0":
        read_modbus_block(host, port, sn, 0x3000, 0x3000, sensor_list=0, timeout=timeout)
    elif protocol == "1097":
        read_modbus_block(host, port, sn, 0x1100, 0x1100, sensor_list=0x1097, timeout=timeout)
    else:
        raise ValueError(f"Unsupported protocol: {protocol}")


def detect_protocol(
    requested: str, host: str, port: int, sn: int, timeout: float
) -> tuple[str, list[dict[str, Any]]]:
    attempts: list[dict[str, Any]] = []
    candidates = (requested,) if requested != "auto" else SUPPORTED_PROTOCOLS
    last_error: Exception | None = None
    for protocol in candidates:
        try:
            _probe_protocol(protocol, host, port, sn, timeout)
        except Exception as err:
            last_error = err
            attempts.append(
                {"protocol": protocol, "result": "failure", "error": safe_error_details(err)}
            )
            continue
        attempts.append({"protocol": protocol, "result": "success"})
        return protocol, attempts
    raise RuntimeError("No supported TSUN local protocol detected") from last_error


def register_key(protocol: str, block: tuple, address: int) -> str:
    if protocol == "1511":
        tag, function, _start, _end = block
        return f"{tag:02X}/{function:02X}:0x{address:04X}"
    return f"0x{address:04X}"


def _block_descriptor(protocol: str, block: tuple) -> dict[str, Any]:
    if protocol == "1511":
        tag, function, start, end = block
        return {
            "address_tag": f"0x{tag:02X}",
            "function": f"0x{function:02X}",
            "start": f"0x{start:04X}",
            "end": f"0x{end:04X}",
        }
    start, end = block
    return {"function": "0x03", "start": f"0x{start:04X}", "end": f"0x{end:04X}"}


def read_plan(
    protocol: str,
    host: str,
    port: int,
    sn: int,
    plan: Iterable[tuple],
    timeout: float,
) -> tuple[dict[str, int], list[dict[str, Any]], list[dict[str, Any]]]:
    registers: dict[str, int] = {}
    blocks: list[dict[str, Any]] = []
    trace: list[dict[str, Any]] = []
    for block in plan:
        record = _block_descriptor(protocol, block)
        try:
            if protocol == "1511":
                tag, function, start, end = block
                values, request_payload, response_payload = read_1511_block(
                    host, port, sn, tag, function, start, end, timeout=timeout
                )
            else:
                start, end = block
                sensor_list = 0x1097 if protocol == "1097" else 0
                values, request_payload, response_payload = read_modbus_block(
                    host, port, sn, start, end, sensor_list=sensor_list, timeout=timeout
                )
        except Exception as err:
            record["result"] = "failure"
            record["error"] = safe_error_details(err)
            trace.append({**record, "stage": "failure"})
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
            trace.append(
                {
                    **record,
                    "stage": "complete",
                    "request_payload": request_payload.hex(" ").upper(),
                    "response_payload": response_payload.hex(" ").upper(),
                }
            )
        blocks.append(record)
    return registers, blocks, trace


# ---------------------------------------------------------------------------
# Analysis / known decoding
# ---------------------------------------------------------------------------

def analyze_snapshots(snapshots: list[dict[str, Any]]) -> dict[str, list[str]]:
    result = {
        "changing_registers": [],
        "stable_registers": [],
        "zero_registers": [],
        "ffff_registers": [],
        "incomplete_registers": [],
    }
    if not snapshots:
        return result
    maps = [snapshot.get("registers", {}) for snapshot in snapshots]
    all_keys = sorted(set().union(*(mapping.keys() for mapping in maps)))
    for key in all_keys:
        if not all(key in mapping for mapping in maps):
            result["incomplete_registers"].append(key)
            continue
        values = [mapping[key] for mapping in maps]
        if len(set(values)) > 1:
            result["changing_registers"].append(key)
        elif values[0] == 0:
            result["zero_registers"].append(key)
        elif values[0] == 0xFFFF:
            result["ffff_registers"].append(key)
        else:
            result["stable_registers"].append(key)
    return result


def _address_map(raw: dict[str, int]) -> dict[int, int]:
    result: dict[int, int] = {}
    for key, value in raw.items():
        try:
            address = int(key.rsplit("0x", 1)[1], 16)
        except (IndexError, ValueError):
            continue
        result[address] = value
    return result


def _u32(registers: dict[int, int], high: int) -> int | None:
    if high not in registers or high + 1 not in registers:
        return None
    return (registers[high] << 16) | registers[high + 1]


def firmware_version(value: int) -> str:
    raw = f"{value:04X}"
    return f"V{raw[0]}.{raw[1]}.{raw[2:]}"


def _detect_pv_count(protocol: str, r: dict[int, int]) -> int:
    if protocol == "1511":
        bases = (0x0E10, 0x0E17, 0x0E1E, 0x0ED8, 0x0EDF, 0x0EE6)
        totals = (0x0E28, 0x0E2A, 0x0E2C, 0x0EF0, 0x0EF2, 0x0EF4)
        detected = 1
        for number, (base, total) in enumerate(zip(bases, totals), 1):
            if any(0 < r.get(a, 0) < 0xFFFF for a in (base, base + 1, base + 2, base + 5, total, total + 1)):
                detected = number
        return detected
    if protocol == "1097":
        detected = 0
        for number in range(1, 7):
            base = 0x1302 + (number - 1) * 7
            if any(0 < r.get(a, 0) < 0xFFFF for a in range(base, base + 7)):
                detected = number
        return max(detected, 1)
    detected = 1
    for number in range(1, 5):
        base = 0x3010 + (number - 1) * 3
        energy = 0x301F + (number - 1) * 3
        if any(0 < r.get(a, 0) < 0xFFFF for a in (base, base + 1, base + 2, energy)):
            detected = number
    return detected


def decode_known(protocol: str, raw: dict[str, int]) -> dict[str, Any]:
    """Decode established fields only; research candidates remain raw evidence."""
    r = _address_map(raw)
    data: dict[str, Any] = {}
    pv_count = _detect_pv_count(protocol, r)

    if protocol == "02b0":
        mapping = {
            "inverter_status_raw": (0x3000, 1),
            "ac_voltage": (0x3009, 0.1),
            "ac_current": (0x300A, 0.01),
            "ac_frequency": (0x300B, 0.01),
            "inverter_temperature": (0x300C, 1),
            "rated_power": (0x300E, 1),
            "ac_power": (0x300F, 0.1),
            "ac_energy_today": (0x301C, 0.01),
            "max_designed_power": (0x2007, 1),
        }
        for key, (address, scale) in mapping.items():
            if address in r:
                value: float | int = r[address] * scale
                if key == "inverter_temperature":
                    value = r[address] - 40
                data[key] = round(value, 3) if isinstance(value, float) else value
        if 0x202C in r:
            data["output_coefficient"] = round(r[0x202C] * 100 / 1024, 2)
        for number in range(1, pv_count + 1):
            base = 0x3010 + (number - 1) * 3
            if base + 2 in r:
                data[f"pv{number}_voltage"] = round(r[base] * 0.1, 2)
                data[f"pv{number}_current"] = round(r[base + 1] * 0.01, 2)
                data[f"pv{number}_power"] = round(r[base + 2] * 0.1, 2)
        data["note_02b0_total_energy"] = (
            "Total-energy width is intentionally left raw so device variants can be validated independently."
        )

    elif protocol == "1097":
        if 0x100A in r:
            data["protocol_version"] = firmware_version(r[0x100A])
        if 0x100C in r:
            data["inverter_version"] = firmware_version(r[0x100C])
        mapping = {
            "inverter_status_raw": (0x1100, 1),
            "ac_voltage": (0x1200, 0.1),
            "ac_current": (0x1201, 0.01),
            "ac_power": (0x1202, 0.1),
            "ac_frequency": (0x1209, 0.01),
            "rated_power": (0x1210, 1),
            "ac_energy_today": (0x1212, 0.01),
        }
        for key, (address, scale) in mapping.items():
            if address in r:
                data[key] = round(r[address] * scale, 3)
        total = _u32(r, 0x1213)
        if total is not None:
            data["ac_energy_total"] = round(total * 0.01, 2)
        if 0x1216 in r:
            data["insulation_impedance_rx"] = round(r[0x1216] * 0.01, 2)
        if 0x1217 in r:
            data["insulation_impedance_ry"] = round(r[0x1217] * 0.01, 2)
        if 0x1218 in r:
            data["inverter_temperature"] = r[0x1218] - 40
        if 0x1400 in r:
            data["country_profile_raw"] = r[0x1400]
        if 0x1423 in r:
            data["output_coefficient"] = round(r[0x1423] * 100 / 1024, 2)
        if 0x1437 in r:
            data["max_designed_power"] = r[0x1437]
        for number in range(1, pv_count + 1):
            base = 0x1302 + (number - 1) * 7
            if base + 2 in r:
                data[f"pv{number}_voltage"] = round(r[base] * 0.1, 2)
                data[f"pv{number}_current"] = round(r[base + 1] * 0.01, 2)
                data[f"pv{number}_power"] = round(r[base + 2] * 0.1, 2)

    else:
        mapping = {
            "inverter_status_raw": (0x0BB8, 1),
            "ac_voltage": (0x0BC4, 0.1),
            "ac_current": (0x0BC5, 0.01),
            "ac_frequency": (0x0BC7, 0.01),
            "inverter_temperature": (0x0BC9, 1),
            "rated_power": (0x0BCC, 1),
            "ac_power": (0x0BCD, 0.1),
            "ac_energy_today": (0x0BCE, 0.01),
        }
        for key, (address, scale) in mapping.items():
            if address in r:
                value: float | int = r[address] * scale
                if key == "inverter_temperature":
                    value = r[address] - 40
                data[key] = round(value, 3) if isinstance(value, float) else value
        total = _u32(r, 0x0BCF)
        if total is not None:
            data["ac_energy_total"] = round(total * 0.01, 2)
        if 0x0BD4 in r:
            data["ambient_temperature"] = r[0x0BD4] - 40
        for key, address in {
            "dsp_firmware_version": 0x0BC0,
            "qcpu1_firmware_version": 0x0E26,
            "qcpu2_firmware_version": 0x0EEE,
        }.items():
            if address in r:
                data[key] = firmware_version(r[address])
        if 0x07D0 in r:
            data["country_profile_raw"] = r[0x07D0]
        if 0x07FA in r:
            data["max_designed_power"] = r[0x07FA]
        bases = (0x0E10, 0x0E17, 0x0E1E, 0x0ED8, 0x0EDF, 0x0EE6)
        for number, base in enumerate(bases[:pv_count], 1):
            if base + 2 in r:
                data[f"pv{number}_voltage"] = round(r[base] * 0.1, 2)
                data[f"pv{number}_current"] = round(r[base + 1] * 0.01, 2)
                data[f"pv{number}_power"] = round(r[base + 2] * 0.1, 2)

    data["detected_pv_count"] = pv_count
    return data


# ---------------------------------------------------------------------------
# Dump document / comparison / filenames
# ---------------------------------------------------------------------------

def _safe_filename_part(value: str) -> str:
    normalized = _SAFE_NAME.sub("-", value.lower()).strip("-._")
    return normalized or "unknown"


def default_output_path(
    model: str | None,
    protocol: str,
    timestamp: datetime,
    *,
    device_index: int | None = None,
) -> Path:
    stamp = timestamp.strftime("%Y%m%dT%H%M%SZ")
    device = f"device-{device_index:02d}_" if device_index is not None else ""
    return Path(
        f"tsun_{device}{_safe_filename_part(model or 'unknown')}_{protocol}_{stamp}.json"
    )


def output_path_for_target(
    requested: Path | None,
    model: str | None,
    protocol: str,
    timestamp: datetime,
    *,
    device_index: int,
    total_targets: int,
) -> Path:
    if requested is None:
        return default_output_path(
            model,
            protocol,
            timestamp,
            device_index=device_index if total_targets > 1 else None,
        )
    if total_targets == 1:
        return requested
    suffix = requested.suffix or ".json"
    stem = requested.stem if requested.suffix else requested.name
    return requested.parent / f"{stem}_device-{device_index:02d}{suffix}"


def _script_sha256() -> str | None:
    try:
        return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    except OSError:
        return None


def _flatten_raw_registers(registers: dict[str, int]) -> list[dict[str, Any]]:
    return [
        {"key": key, "raw_decimal": value, "raw_hex": f"0x{value:04X}"}
        for key, value in sorted(registers.items())
    ]


def capture(
    args: argparse.Namespace, host: str, sn: int, discovery: dict[str, Any]
) -> dict[str, Any]:
    protocol, detection_attempts = detect_protocol(
        args.protocol, host, args.port, sn, args.timeout
    )
    print(f"Protocol detected: {protocol}")
    dynamic_plan, supplemental_plan = capture_plans(protocol, args.full)
    supplemental_registers, supplemental_blocks, supplemental_trace = read_plan(
        protocol, host, args.port, sn, supplemental_plan, args.timeout
    )

    snapshots: list[dict[str, Any]] = []
    snapshot_blocks: list[dict[str, Any]] = []
    protocol_trace = list(supplemental_trace)
    for index in range(args.snapshots):
        registers, blocks, trace = read_plan(
            protocol, host, args.port, sn, dynamic_plan, args.timeout
        )
        snapshots.append(
            {
                "index": index + 1,
                "timestamp_utc": datetime.now(UTC).isoformat(),
                "registers": registers,
            }
        )
        for block in blocks:
            block["snapshot"] = index + 1
            block["scope"] = "dynamic"
            snapshot_blocks.append(block)
        protocol_trace.extend(trace)
        if index + 1 < args.snapshots and args.interval:
            time.sleep(args.interval)

    latest = snapshots[-1]["registers"] if snapshots else {}
    merged = {**supplemental_registers, **latest}
    supplemental_blocks = [
        {**block, "snapshot": None, "scope": "supplemental"}
        for block in supplemental_blocks
    ]
    all_blocks = [*supplemental_blocks, *snapshot_blocks]
    successful = sum(block["result"] == "success" for block in all_blocks)
    failed = len(all_blocks) - successful
    created_at = datetime.now(UTC)
    family = {
        "1511": "TITAN",
        "02b0": "GEN3 / GEN3 PLUS",
        "1097": "GEN3 / GEN3 PLUS (1097)",
    }[protocol]

    return {
        "format": DUMP_FORMAT,
        "schema_version": SCHEMA_VERSION,
        "metadata": {
            "timestamp_utc": created_at.isoformat(),
            "tool": "TSUN Local Hardware Validation Dump Tool",
            "tool_version": TOOL_VERSION,
            "tool_sha256": _script_sha256(),
            "tool_source": SOURCE_URL,
            "standalone": True,
            "python_required": ">=3.10",
            "read_only": True,
            "capture_mode": "full" if args.full else "standard",
            "detected_protocol": protocol,
            "model_family": family,
            "model_supplied_by_user": args.model,
            "pv_count": _detect_pv_count(protocol, _address_map(merged)),
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
            "attempts": detection_attempts,
        },
        "decoded_known_measurements": decode_known(protocol, merged),
        "capture_summary": {
            "snapshots": len(snapshots),
            "snapshot_interval_seconds": args.interval,
            "successful_block_reads": successful,
            "failed_block_reads": failed,
            "unique_raw_registers": len(merged),
        },
        "raw_registers": _flatten_raw_registers(merged),
        "snapshots": snapshots,
        "analysis": analyze_snapshots(snapshots),
        "blocks": all_blocks,
        "protocol_trace": protocol_trace,
    }


def _raw_map(document: dict[str, Any]) -> dict[str, int]:
    result: dict[str, int] = {}
    for item in document.get("raw_registers", []):
        if isinstance(item, dict) and "key" in item and "raw_decimal" in item:
            result[str(item["key"])] = int(item["raw_decimal"])
    return result


def compare_documents(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
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
        "added_registers": sorted(after_map.keys() - before_map.keys()),
        "removed_registers": sorted(before_map.keys() - after_map.keys()),
        "unchanged_register_count": sum(before_map[k] == after_map[k] for k in common),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

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
        raise argparse.ArgumentTypeError("value must be >= 0")
    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Standalone, privacy-safe, strictly read-only TSUN hardware dump for "
            "1511, 02B0 and 1097. Without --host, all discovered loggers are captured."
        )
    )
    parser.add_argument(
        "--host",
        help="logger IP address; when omitted, every discovered logger is captured",
    )
    parser.add_argument(
        "--serial",
        type=int,
        help="numeric Monitor SN for single-target use; normally discovered/prompted",
    )
    parser.add_argument("--port", type=_positive_port, default=DEFAULT_PORT)
    parser.add_argument(
        "--protocol",
        choices=("auto", *SUPPORTED_PROTOCOLS),
        default="auto",
        help="force a protocol or detect automatically",
    )
    parser.add_argument("--model", help="exact physical model for metadata/file name")
    parser.add_argument(
        "--full", action="store_true", help="read additional known-safe research ranges"
    )
    parser.add_argument("--snapshots", type=_positive_int, default=DEFAULT_SNAPSHOTS)
    parser.add_argument(
        "--interval", type=_non_negative_float, default=DEFAULT_SNAPSHOT_INTERVAL
    )
    parser.add_argument("--timeout", type=_non_negative_float, default=DEFAULT_TIMEOUT)
    parser.add_argument(
        "--discovery-timeout",
        type=_non_negative_float,
        default=DEFAULT_DISCOVERY_TIMEOUT,
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="output JSON path; multi-device scans add _device-NN automatically",
    )
    parser.add_argument(
        "--compare",
        nargs=2,
        metavar=("BEFORE_JSON", "AFTER_JSON"),
        help="compare two existing dump files without connecting to an inverter",
    )
    return parser


def _print_dump_summary(document: dict[str, Any], output: Path) -> None:
    summary = document["capture_summary"]
    privacy = document["metadata"]["privacy"]
    print("Dump completed.")
    print(f"Protocol : {document['metadata']['detected_protocol']}")
    print(
        f"Blocks   : {summary['successful_block_reads']} successful / "
        f"{summary['failed_block_reads']} failed"
    )
    print(f"Registers: {summary['unique_raw_registers']} unique raw registers")
    print(f"Snapshots: {summary['snapshots']}")
    print("Writes   : 0")
    print(
        "Privacy  : host={}, Monitor SN={}, inverter SN={}".format(
            "excluded" if not privacy["host_in_output"] else "included",
            "excluded" if not privacy["logger_sn_in_output"] else "included",
            "excluded" if not privacy["inverter_serial_in_output"] else "included",
        )
    )
    print(f"Output   : {output}")


def main() -> int:
    if sys.version_info < (3, 10):
        print("ERROR: Python 3.10 or newer is required. Use python3.", file=sys.stderr)
        return 2

    args = build_parser().parse_args()
    if args.compare:
        before_path, after_path = map(Path, args.compare)
        try:
            before = json.loads(before_path.read_text(encoding="utf-8"))
            after = json.loads(after_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as err:
            print(f"ERROR: could not read comparison files: {err}", file=sys.stderr)
            return 2
        result = compare_documents(before, after)
        print(f"Changed raw registers: {len(result['changed_registers'])}")
        for item in result["changed_registers"]:
            print(f"  {item['key']}: {item['before']} -> {item['after']}")
        if args.output:
            args.output.write_text(
                json.dumps(result, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            print(f"Comparison JSON: {args.output}")
        return 0

    print("TSUN Local Hardware Validation Dump Tool")
    print(f"Standalone v{TOOL_VERSION} · READ-ONLY · Python standard library only")
    print("No inverter configuration write operation is implemented.\n")

    try:
        targets, resolution = resolve_targets(args)
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")
        return 130
    except Exception as err:
        print(f"ERROR: {type(err).__name__}: {err}", file=sys.stderr)
        return 1

    total = len(targets)
    completed: list[Path] = []
    failed = 0
    if total > 1 and args.model:
        print("Note: --model is applied to every captured logger in this scan.")

    for sequence, (host, sn, discovery) in enumerate(targets, 1):
        discovered_index = int(discovery.get("target_index", sequence))
        print(f"\n=== Device {sequence}/{total} (discovery #{discovered_index}) ===")
        print(f"Logger   : {host}")
        try:
            document = capture(args, host, sn, discovery)
        except (KeyboardInterrupt, EOFError):
            print("\nCancelled.")
            return 130
        except Exception as err:
            failed += 1
            print(
                f"ERROR: device {sequence}/{total}: {type(err).__name__}: {err}",
                file=sys.stderr,
            )
            continue

        timestamp = datetime.fromisoformat(document["metadata"]["timestamp_utc"])
        output = output_path_for_target(
            args.output,
            args.model,
            document["metadata"]["detected_protocol"],
            timestamp,
            device_index=discovered_index,
            total_targets=total,
        )
        try:
            output.write_text(
                json.dumps(document, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        except OSError as err:
            failed += 1
            print(f"ERROR: could not write {output}: {err}", file=sys.stderr)
            continue
        completed.append(output)
        _print_dump_summary(document, output)

    print("\n=== Scan summary ===")
    print(f"Discovered: {resolution['devices_found']}")
    print(f"Resolved  : {resolution['targets_resolved']}")
    print(f"Skipped   : {resolution['targets_skipped']}")
    print(f"Captured  : {len(completed)}")
    print(f"Failed    : {failed}")
    if completed:
        print("Generated files:")
        for output in completed:
            print(f"  {output}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
