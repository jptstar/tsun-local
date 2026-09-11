#!/usr/bin/env python3
# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later
"""TSUN Y4Z / candidate sensor-list 0x3026 — read-only local probe.

This small standalone probe is intended for hardware identification only. It
connects to a user-supplied local logger on TCP/8899, sends a Solarman/AP-wrapped
Modbus function 0x03 read for registers 0x0000..0x002C (45 registers), and saves
three raw snapshots by default.

The 0x3026 family is only a hypothesis for Y4Z hardware. The script therefore
keeps the register values raw and does not apply the DCU1000/battery mapping.
No write command, AT command, configuration change, cloud request, or GitHub
request is implemented.
"""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any

SENSOR_LIST = 0x3026
MODBUS_SLAVE = 0x01
FUNCTION = 0x03
START_REGISTER = 0x0000
REGISTER_COUNT = 45
DEFAULT_PORT = 8899
DEFAULT_SAMPLES = 3
DEFAULT_INTERVAL = 3.0
DEFAULT_TIMEOUT = 6.0


class ProbeError(Exception):
    """Raised when a Y4Z/3026 probe frame cannot be validated."""


def checksum_ap(data: bytes) -> int:
    return sum(data) & 0xFF


def crc16_modbus(data: bytes) -> bytes:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc.to_bytes(2, "little")


def build_modbus_read(start: int, count: int) -> bytes:
    body = (
        bytes((MODBUS_SLAVE, FUNCTION))
        + start.to_bytes(2, "big")
        + count.to_bytes(2, "big")
    )
    return body + crc16_modbus(body)


def build_ap_request(logger_sn: int, payload: bytes) -> bytes:
    data = b"\x02" + SENSOR_LIST.to_bytes(2, "little") + bytes(12) + payload
    scope = (
        len(data).to_bytes(2, "little")
        + b"\x10\x45\x00\x00"
        + logger_sn.to_bytes(4, "little")
        + data
    )
    return b"\xA5" + scope + bytes((checksum_ap(scope), 0x15))


async def read_ap_frame(reader: asyncio.StreamReader) -> bytes:
    header = await reader.readexactly(3)
    if header[0] != 0xA5:
        raise ProbeError(f"Unexpected AP start byte 0x{header[0]:02X}")
    remaining = int.from_bytes(header[1:3], "little") + 10
    return header + await reader.readexactly(remaining)


def parse_ap_reply(frame: bytes) -> bytes:
    if len(frame) < 27:
        raise ProbeError(f"AP frame too short: {len(frame)} bytes")
    if frame[0] != 0xA5 or frame[-1] != 0x15:
        raise ProbeError("Invalid AP frame markers")
    expected = int.from_bytes(frame[1:3], "little") + 13
    if len(frame) != expected:
        raise ProbeError(f"Invalid AP length {len(frame)} != {expected}")
    if checksum_ap(frame[1:-2]) != frame[-2]:
        raise ProbeError("Invalid AP checksum")
    if frame[11] != 0x02 or frame[12] != 0x01:
        raise ProbeError(
            "Unexpected AP response type/status: "
            f"0x{frame[11]:02X}/0x{frame[12]:02X}"
        )
    return frame[25:-2]


def parse_modbus_reply(payload: bytes, start: int, count: int) -> dict[int, int]:
    if len(payload) < 5:
        raise ProbeError("Modbus reply too short")
    if crc16_modbus(payload[:-2]) != payload[-2:]:
        raise ProbeError("Invalid Modbus CRC")
    if payload[0] != MODBUS_SLAVE:
        raise ProbeError(f"Unexpected Modbus slave {payload[0]}")
    if payload[1] == (FUNCTION | 0x80):
        code = payload[2] if len(payload) > 2 else -1
        raise ProbeError(f"Modbus exception 0x{code:02X}")
    if payload[1] != FUNCTION:
        raise ProbeError(f"Unexpected Modbus function 0x{payload[1]:02X}")

    byte_count = payload[2]
    expected_bytes = count * 2
    if byte_count != expected_bytes:
        raise ProbeError(
            f"Unexpected Modbus byte count {byte_count}, expected {expected_bytes}"
        )
    if len(payload) != 3 + byte_count + 2:
        raise ProbeError("Unexpected Modbus frame length")

    raw = payload[3 : 3 + byte_count]
    return {
        start + index: int.from_bytes(raw[index * 2 : index * 2 + 2], "big")
        for index in range(count)
    }


@dataclass
class Sample:
    timestamp_utc: str
    registers: dict[str, int]


async def read_sample(host: str, port: int, logger_sn: int, timeout: float) -> Sample:
    request = build_ap_request(
        logger_sn,
        build_modbus_read(START_REGISTER, REGISTER_COUNT),
    )

    writer: asyncio.StreamWriter | None = None
    try:
        async with asyncio.timeout(timeout):
            reader, writer = await asyncio.open_connection(host, port)
            writer.write(request)
            await writer.drain()
            frame = await read_ap_frame(reader)
        registers = parse_modbus_reply(
            parse_ap_reply(frame), START_REGISTER, REGISTER_COUNT
        )
    finally:
        if writer is not None:
            writer.close()
            try:
                await writer.wait_closed()
            except OSError:
                pass

    return Sample(
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        registers={f"0x{address:04X}": value for address, value in registers.items()},
    )


def masked_logger_sn(value: int) -> str:
    text = str(value)
    if len(text) <= 4:
        return "****"
    return "*" * (len(text) - 4) + text[-4:]


def changed_registers(samples: list[Sample]) -> list[dict[str, Any]]:
    if len(samples) < 2:
        return []
    keys = samples[0].registers.keys()
    result: list[dict[str, Any]] = []
    for key in keys:
        values = [sample.registers[key] for sample in samples]
        if len(set(values)) > 1:
            result.append({"register": key, "values": values})
    return result


async def async_main(args: argparse.Namespace) -> int:
    samples: list[Sample] = []

    print("TSUN Y4Z / candidate 3026 READ-ONLY local probe")
    print(f"Target      : {args.host}:{args.port}")
    print(f"Sensor list : candidate 0x{SENSOR_LIST:04X}")
    print(
        f"Read        : 0x{START_REGISTER:04X}.."
        f"0x{START_REGISTER + REGISTER_COUNT - 1:04X} ({REGISTER_COUNT} registers)"
    )
    print(f"Logger SN   : {masked_logger_sn(args.logger_sn)}")
    print(f"Model       : {args.model or 'unknown'}")
    print(f"Serial pref.: {args.serial_prefix}")
    print(f"Samples     : {args.samples}")
    print("Writes      : NONE")
    print("Cloud       : NONE")
    print()

    for index in range(args.samples):
        print(f"[{index + 1}/{args.samples}] reading...", flush=True)
        sample = await read_sample(args.host, args.port, args.logger_sn, args.timeout)
        samples.append(sample)
        preview = " ".join(
            f"{key}={value}"
            for key, value in list(sample.registers.items())[:12]
        )
        print(f"  {preview}")
        if index + 1 < args.samples:
            await asyncio.sleep(args.interval)

    result = {
        "probe": "TSUN Y4Z / candidate sensor-list 0x3026",
        "mode": "read_only_local",
        "candidate_only": True,
        "candidate_notice": (
            "0x3026 is being tested as a protocol/register-family hypothesis. "
            "No DCU1000/battery interpretation is applied; raw registers are the "
            "primary evidence."
        ),
        "device": {
            "model_supplied_by_user": args.model,
            "inverter_serial_prefix": args.serial_prefix,
            "port": args.port,
            "logger_sn_masked": masked_logger_sn(args.logger_sn),
            "host_stored": False,
        },
        "request": {
            "sensor_list": "0x3026",
            "transport": "Solarman/AP-wrapped Modbus RTU",
            "modbus_slave": MODBUS_SLAVE,
            "modbus_function": FUNCTION,
            "start_register": "0x0000",
            "end_register": f"0x{START_REGISTER + REGISTER_COUNT - 1:04X}",
            "register_count": REGISTER_COUNT,
        },
        "samples": [
            {
                "timestamp_utc": sample.timestamp_utc,
                "registers": sample.registers,
            }
            for sample in samples
        ],
        "changed_registers": changed_registers(samples),
        "privacy": {
            "logger_ip_stored": False,
            "full_inverter_serial_stored": False,
            "full_logger_serial_stored": False,
            "mac_address_stored": False,
            "credentials_stored": False,
        },
    }

    output = args.output
    if output is None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = Path.cwd() / f"y4z_3026_probe_{stamp}.json"
    output = output.expanduser().resolve()
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    print()
    print(f"Saved: {output}")
    print("Please attach the JSON to the TSUN Local Y4Z issue.")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only local probe for Y4Z hardware using the candidate 3026 "
            "register family."
        )
    )
    parser.add_argument("--host", required=True, help="Local TSUN logger IP address.")
    parser.add_argument("--logger-sn", required=True, type=int, help="Monitoring/logger SN.")
    parser.add_argument("--model", help="Exact model from the inverter label, if known.")
    parser.add_argument(
        "--serial-prefix",
        default="Y4Z",
        help="Only the non-sensitive inverter serial prefix (default: Y4Z).",
    )
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--samples", type=int, default=DEFAULT_SAMPLES)
    parser.add_argument("--interval", type=float, default=DEFAULT_INTERVAL)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.samples < 1 or args.samples > 20:
        print("ERROR: --samples must be between 1 and 20", file=sys.stderr)
        return 2
    if args.interval < 0:
        print("ERROR: --interval cannot be negative", file=sys.stderr)
        return 2
    if not (1 <= args.port <= 65535):
        print("ERROR: --port must be between 1 and 65535", file=sys.stderr)
        return 2
    if not (0 <= args.logger_sn <= 0xFFFFFFFF):
        print("ERROR: --logger-sn must fit in an unsigned 32-bit integer", file=sys.stderr)
        return 2
    if not args.serial_prefix or len(args.serial_prefix) > 8:
        print("ERROR: --serial-prefix must contain 1..8 characters", file=sys.stderr)
        return 2
    try:
        return asyncio.run(async_main(args))
    except (OSError, TimeoutError, asyncio.IncompleteReadError, ProbeError) as exc:
        print()
        print(f"PROBE FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        print(
            "No configuration was changed. A failed 3026 probe is still useful: "
            "please report the error together with the exact inverter model.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
