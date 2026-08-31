#!/usr/bin/env python3
# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later
"""
TSUN DCU1000 / sensor-list 0x3026 — READ-ONLY local probe.

Purpose
-------
Validate the current 3026 register hypothesis on a real DCU1000-class device.

What it does
------------
- Connects only to a user-supplied LOCAL IP/port (default TCP/8899).
- Sends a Solarman/AP-wrapped Modbus function 0x03 read.
- Reads registers 0x0000..0x002C (45 registers).
- Decodes the current candidate DCU1000/3026 map.
- Saves raw + decoded samples to JSON.

What it DOES NOT do
-------------------
- No Modbus writes.
- No AT commands.
- No configuration changes.
- No TSUN/Talent cloud traffic.
- No GitHub access.
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


class ProbeError(Exception):
    pass


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
            f"Unexpected AP response type/status: "
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
        start + i: int.from_bytes(raw[i * 2 : i * 2 + 2], "big")
        for i in range(count)
    }


def signed16(value: int) -> int:
    return value - 0x10000 if value & 0x8000 else value


def u32(registers: dict[int, int], high: int) -> int:
    return (registers[high] << 16) | registers[high + 1]


def decode_3026(r: dict[int, int]) -> dict[str, Any]:
    d: dict[str, Any] = {
        "pv1_voltage": r[0] * 0.01,
        "pv1_current": r[1] * 0.01,
        "pv2_voltage": r[2] * 0.01,
        "pv2_current": r[3] * 0.01,
        "battery_energy_total_charge": u32(r, 4) * 0.01,
        "pv1_status_raw": r[6],
        "pv2_status_raw": r[7],
        "battery_voltage": signed16(r[8]) * 0.01,
        "battery_current": signed16(r[9]) * 0.01,
        "battery_soc": r[10] * 0.01,
    }

    for cell in range(1, 17):
        d[f"battery_cell_{cell}_voltage"] = r[10 + cell] * 0.001

    d.update(
        {
            "battery_temperature_1": signed16(r[27]),
            "battery_temperature_2": signed16(r[28]),
            "battery_temperature_3": signed16(r[29]),
            "battery_output_voltage": r[30] * 0.01,
            "battery_output_current": r[31] * 0.01,
            "battery_output_status_raw": r[32],
            "battery_ambient_temperature": signed16(r[33]),
            "battery_alarm_raw": r[34],
            "battery_hardware_version_raw": signed16(r[35]),
            "battery_software_version_raw": signed16(r[36]),
        }
    )

    d["battery_power"] = round(
        float(d["battery_voltage"]) * float(d["battery_current"]), 2
    )
    d["pv_power"] = round(
        float(d["pv1_voltage"]) * float(d["pv1_current"])
        + float(d["pv2_voltage"]) * float(d["pv2_current"]),
        2,
    )

    for address in range(37, REGISTER_COUNT):
        d[f"register_0x{address:04X}_raw"] = r[address]

    return d


@dataclass
class Sample:
    timestamp_utc: str
    registers: dict[str, int]
    decoded: dict[str, Any]


async def read_sample(host: str, port: int, logger_sn: int, timeout: float) -> Sample:
    payload = build_modbus_read(START_REGISTER, REGISTER_COUNT)
    request = build_ap_request(logger_sn, payload)

    writer: asyncio.StreamWriter | None = None
    try:
        async with asyncio.timeout(timeout):
            reader, writer = await asyncio.open_connection(host, port)
            writer.write(request)
            await writer.drain()
            frame = await read_ap_frame(reader)

        protocol_payload = parse_ap_reply(frame)
        registers = parse_modbus_reply(
            protocol_payload, START_REGISTER, REGISTER_COUNT
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
        registers={f"0x{k:04X}": v for k, v in registers.items()},
        decoded=decode_3026(registers),
    )


def masked_logger_sn(value: int) -> str:
    text = str(value)
    if len(text) <= 4:
        return "****"
    return "*" * (len(text) - 4) + text[-4:]


async def async_main(args: argparse.Namespace) -> int:
    samples: list[Sample] = []

    print("TSUN DCU1000 / 3026 READ-ONLY local probe")
    print(f"Target      : {args.host}:{args.port}")
    print(f"Sensor list : 0x{SENSOR_LIST:04X}")
    print(
        f"Read        : 0x{START_REGISTER:04X}.."
        f"0x{START_REGISTER + REGISTER_COUNT - 1:04X}"
    )
    print(f"Logger SN   : {masked_logger_sn(args.logger_sn)}")
    print(f"Samples     : {args.samples}")
    print("Writes      : NONE")
    print("Cloud       : NONE")
    print()

    for index in range(args.samples):
        print(f"[{index + 1}/{args.samples}] reading...", flush=True)
        sample = await read_sample(
            args.host, args.port, args.logger_sn, args.timeout
        )
        samples.append(sample)

        d = sample.decoded
        print(
            "  "
            f"SOC={d['battery_soc']}%  "
            f"Batt={d['battery_voltage']}V / {d['battery_current']}A  "
            f"PV={d['pv_power']}W  "
            f"Out={d['battery_output_voltage']}V / "
            f"{d['battery_output_current']}A  "
            f"AlarmRaw={d['battery_alarm_raw']}"
        )
        print(
            "  "
            f"Temps={d['battery_temperature_1']}, "
            f"{d['battery_temperature_2']}, "
            f"{d['battery_temperature_3']} °C  "
            f"Ambient={d['battery_ambient_temperature']} °C  "
            f"OutStatus={d['battery_output_status_raw']}"
        )

        if index + 1 < args.samples:
            await asyncio.sleep(args.interval)

    result = {
        "probe": "TSUN DCU1000 / sensor-list 0x3026",
        "mode": "read_only_local",
        "target": {
            "port": args.port,
            "logger_sn_masked": masked_logger_sn(args.logger_sn),
        },
        "request": {
            "sensor_list": "0x3026",
            "modbus_function": 3,
            "start_register": "0x0000",
            "register_count": REGISTER_COUNT,
        },
        "candidate_mapping_notice": (
            "Decoded field names/addresses are current 3026 candidates. "
            "The raw register dump is the primary validation evidence."
        ),
        "samples": [
            {
                "timestamp_utc": s.timestamp_utc,
                "registers": s.registers,
                "decoded": s.decoded,
            }
            for s in samples
        ],
    }

    output = args.output
    if output is None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = Path.cwd() / f"dc1000_3026_probe_{stamp}.json"
    output = output.expanduser().resolve()
    output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print()
    print(f"Saved: {output}")
    print("Please share the JSON file; the logger SN is masked in the output.")
    return 0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Read-only local probe for TSUN DCU1000 / sensor-list 3026."
    )
    p.add_argument("--host", required=True, help="Local DCU/logger IP address.")
    p.add_argument("--logger-sn", required=True, type=int, help="Monitoring/logger SN.")
    p.add_argument("--port", type=int, default=8899)
    p.add_argument("--samples", type=int, default=3)
    p.add_argument("--interval", type=float, default=2.0)
    p.add_argument("--timeout", type=float, default=5.0)
    p.add_argument("--output", type=Path)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    if args.samples < 1 or args.samples > 20:
        print("ERROR: --samples must be between 1 and 20", file=sys.stderr)
        return 2
    if args.interval < 0:
        print("ERROR: --interval cannot be negative", file=sys.stderr)
        return 2
    try:
        return asyncio.run(async_main(args))
    except (OSError, TimeoutError, asyncio.IncompleteReadError, ProbeError) as exc:
        print()
        print(f"PROBE FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        print(
            "No configuration was changed. "
            "If direct local TCP/8899 is unavailable, use a proxy trace instead.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
