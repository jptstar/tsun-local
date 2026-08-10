# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Local TSUN 1511 protocol transport and decoder."""

from __future__ import annotations

import asyncio
from collections.abc import Iterable
from dataclasses import dataclass
import time
from typing import Any

from .const import BLOCKS


class TsunProtocolError(Exception):
    """Raised when a TSUN frame is invalid."""


def crc16_1511(data: bytes) -> bytes:
    """Return Modbus CRC16 in TSUN 1511 (non-swapped) byte order."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc.to_bytes(2, "big")


def checksum_ap(data: bytes) -> int:
    """Return the AP additive checksum."""
    return sum(data) & 0xFF


def build_1511_request(address_tag: int, function: int, start: int, end: int) -> bytes:
    """Build one validated 1511 register read request."""
    count = end - start + 1
    body = bytes((address_tag, function, 0x00)) + start.to_bytes(2, "big")
    body += b"\x00\x02" + count.to_bytes(2, "big")
    return body + crc16_1511(body)


def build_ap_frame(logger_sn: int, payload: bytes) -> bytes:
    """Wrap a 1511 request in an AP frame."""
    data = b"\x02\x00\x00" + bytes(12) + payload
    scope = (
        len(data).to_bytes(2, "little")
        + b"\x10\x45\x00\x00"
        + logger_sn.to_bytes(4, "little")
        + data
    )
    return b"\xA5" + scope + bytes((checksum_ap(scope), 0x15))


def parse_ap_frame(frame: bytes) -> bytes:
    """Validate an AP response and return its embedded 1511 frame."""
    if len(frame) < 16 or frame[0] != 0xA5 or frame[-1] != 0x15:
        raise TsunProtocolError("Invalid AP frame markers")
    expected_length = int.from_bytes(frame[1:3], "little") + 13
    if len(frame) != expected_length:
        raise TsunProtocolError(f"Invalid AP frame length: {len(frame)} != {expected_length}")
    if checksum_ap(frame[1:-2]) != frame[-2]:
        raise TsunProtocolError("Invalid AP checksum")
    try:
        inner_start = frame.index(0x7E, 12, -2)
    except ValueError as err:
        raise TsunProtocolError("1511 payload not found") from err
    return frame[inner_start:-2]


def parse_1511_response(
    frame: bytes, address_tag: int, function: int, start: int, end: int
) -> dict[int, int]:
    """Validate and parse a response into little-endian 16-bit registers."""
    if len(frame) < 11 or frame[0] != 0x7E:
        raise TsunProtocolError("Invalid 1511 frame")
    if crc16_1511(frame[1:-2]) != frame[-2:]:
        raise TsunProtocolError("Invalid 1511 CRC")
    if frame[1] != address_tag or frame[2] != (function | 0x80):
        raise TsunProtocolError("Unexpected 1511 address or response function")
    if frame[3] != 0x01:
        raise TsunProtocolError(f"Protocol 1511 returned status 0x{frame[3]:02X}")
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


def _u32_type5(registers: dict[int, int], high_address: int) -> int:
    """Decode official byte-order type 5: high 16-bit register then low register."""
    return (registers[high_address] << 16) | registers[high_address + 1]


def decode_measurements(registers: dict[int, int]) -> dict[str, float | int]:
    """Decode the validated AC and PV register map."""
    data: dict[str, float | int] = {
        "ac_voltage": registers[0x0BC4] * 0.1,
        "ac_current": registers[0x0BC5] * 0.01,
        "ac_frequency": registers[0x0BC7] * 0.01,
        "ac_power": registers[0x0BCD] * 0.1,
        "ac_energy_today": registers[0x0BCE] * 0.01,
        "ac_energy_total": _u32_type5(registers, 0x0BCF) * 0.01,
    }
    pv_bases = (0x0E10, 0x0E17, 0x0E1E, 0x0ED8, 0x0EDF, 0x0EE6)
    pv_total_pairs = (0x0E28, 0x0E2A, 0x0E2C, 0x0EF0, 0x0EF2, 0x0EF4)
    for number, (base, total_pair) in enumerate(zip(pv_bases, pv_total_pairs), 1):
        prefix = f"pv{number}"
        data[f"{prefix}_voltage"] = registers[base] * 0.1
        data[f"{prefix}_current"] = registers[base + 1] * 0.01
        data[f"{prefix}_power"] = registers[base + 2] * 0.1
        data[f"{prefix}_energy_today"] = registers[base + 4] * 0.01
        data[f"{prefix}_energy_total"] = _u32_type5(registers, total_pair) * 0.01
    data["dc_power_total"] = round(
        sum(float(data[f"pv{number}_power"]) for number in range(1, 7)), 1
    )
    return data


@dataclass(slots=True)
class TsunReadResult:
    """A complete device poll."""

    measurements: dict[str, float | int]
    duration_ms: int
    blocks_ok: int


class TsunClient:
    """Async local client for one TSUN logger."""

    def __init__(self, host: str, port: int, logger_sn: int, timeout: float = 10) -> None:
        self.host = host
        self.port = port
        self.logger_sn = logger_sn
        self.timeout = timeout

    async def _read_frame(self, reader: asyncio.StreamReader) -> bytes:
        header = await reader.readexactly(3)
        if header[0] != 0xA5:
            raise TsunProtocolError("Invalid AP start marker")
        remaining = int.from_bytes(header[1:3], "little") + 10
        return header + await reader.readexactly(remaining)

    async def _read_block(self, block: tuple[int, int, int, int]) -> dict[int, int]:
        address_tag, function, start, end = block
        request = build_ap_frame(
            self.logger_sn, build_1511_request(address_tag, function, start, end)
        )
        writer: asyncio.StreamWriter | None = None
        try:
            async with asyncio.timeout(self.timeout):
                reader, writer = await asyncio.open_connection(self.host, self.port)
                writer.write(request)
                await writer.drain()
                response = await self._read_frame(reader)
            return parse_1511_response(
                parse_ap_frame(response), address_tag, function, start, end
            )
        finally:
            if writer is not None:
                writer.close()
                await writer.wait_closed()

    async def async_read_all(self) -> TsunReadResult:
        """Read the three validated blocks sequentially."""
        started = time.monotonic()
        registers: dict[int, int] = {}
        for block in BLOCKS:
            registers.update(await self._read_block(block))
        return TsunReadResult(
            measurements=decode_measurements(registers),
            duration_ms=round((time.monotonic() - started) * 1000),
            blocks_ok=len(BLOCKS),
        )
