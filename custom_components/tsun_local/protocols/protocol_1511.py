# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Local TSUN 1511 protocol transport and decoder."""

from __future__ import annotations

import asyncio
import time

from . import TsunReadResult
from .ap import TsunProtocolError, build_ap_frame, parse_ap_frame, read_ap_frame

PROTOCOL_NAME = "1511"
MODEL = "TITAN"

BLOCKS = (
    (0xA1, 0x01, 0x0BB8, 0x0BD0),
    (0xA3, 0x03, 0x0E10, 0x0E2D),
    (0xA4, 0x04, 0x0ED8, 0x0EF5),
)

AC_MEASUREMENT_KEYS = frozenset(
    {
        "ac_voltage",
        "ac_current",
        "ac_frequency",
        "ac_power",
        "ac_energy_today",
        "ac_energy_total",
        "dc_power_total",
    }
)
PV_MEASUREMENT_NAMES = (
    "voltage",
    "current",
    "power",
    "energy_today",
    "energy_total",
)


def crc16_1511(data: bytes) -> bytes:
    """Return Modbus CRC16 in TSUN 1511 (non-swapped) byte order."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc.to_bytes(2, "big")


def build_1511_request(address_tag: int, function: int, start: int, end: int) -> bytes:
    """Build one validated 1511 register read request."""
    count = end - start + 1
    body = bytes((address_tag, function, 0x00)) + start.to_bytes(2, "big")
    body += b"\x00\x02" + count.to_bytes(2, "big")
    return body + crc16_1511(body)


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


def _measurement_keys(pv_count: int) -> frozenset[str]:
    """Return keys exposed for the detected number of PV inputs."""
    return AC_MEASUREMENT_KEYS | frozenset(
        f"pv{number}_{measurement}"
        for number in range(1, pv_count + 1)
        for measurement in PV_MEASUREMENT_NAMES
    )


def detect_pv_count(registers: dict[int, int]) -> int:
    """Detect the highest populated PV input while always retaining PV1."""
    pv_bases = (0x0E10, 0x0E17, 0x0E1E, 0x0ED8, 0x0EDF, 0x0EE6)
    pv_total_pairs = (0x0E28, 0x0E2A, 0x0E2C, 0x0EF0, 0x0EF2, 0x0EF4)
    detected = 1
    for number, (base, total_pair) in enumerate(zip(pv_bases, pv_total_pairs), 1):
        addresses = (base, base + 1, base + 2, base + 4, total_pair, total_pair + 1)
        if any(0 < registers.get(address, 0) < 0xFFFF for address in addresses):
            detected = number
    return detected


def decode_measurements(
    registers: dict[int, int], pv_count: int = 6
) -> dict[str, float | int]:
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
    for number, (base, total_pair) in enumerate(
        zip(pv_bases[:pv_count], pv_total_pairs[:pv_count]), 1
    ):
        prefix = f"pv{number}"
        data[f"{prefix}_voltage"] = registers[base] * 0.1
        data[f"{prefix}_current"] = registers[base + 1] * 0.01
        data[f"{prefix}_power"] = registers[base + 2] * 0.1
        data[f"{prefix}_energy_today"] = registers[base + 4] * 0.01
        data[f"{prefix}_energy_total"] = _u32_type5(registers, total_pair) * 0.01
    data["dc_power_total"] = round(
        sum(float(data[f"pv{number}_power"]) for number in range(1, pv_count + 1)), 1
    )
    return data


class Tsun1511Client:
    """Async protocol 1511 client for one TSUN logger."""

    model = MODEL
    protocol_name = PROTOCOL_NAME

    def __init__(self, host: str, port: int, logger_sn: int, timeout: float = 10) -> None:
        self.host = host
        self.port = port
        self.logger_sn = logger_sn
        self.timeout = timeout
        self._pv_count = 1

    @property
    def pv_count(self) -> int:
        """Return the highest PV input detected so far."""
        return self._pv_count

    @property
    def measurement_keys(self) -> frozenset[str]:
        """Return measurement keys supported by the detected hardware."""
        return _measurement_keys(self._pv_count)

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
                response = await read_ap_frame(reader)
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
        self._pv_count = max(self._pv_count, detect_pv_count(registers))
        return TsunReadResult(
            measurements=decode_measurements(registers, self._pv_count),
            duration_ms=round((time.monotonic() - started) * 1000),
            blocks_ok=len(BLOCKS),
        )
