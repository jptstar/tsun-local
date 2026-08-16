# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Local TSUN 1097 Modbus transport and decoder."""

# The experimental 1097 register mapping was informed by publicly available
# protocol research from Stefan Allius (s-allius/tsun-gen3-proxy).

from __future__ import annotations

import asyncio
import logging
import time

from . import TsunReadResult
from .ap import (
    ProtocolTrace,
    TsunProtocolError,
    build_ap_frame,
    parse_ap_frame,
    read_ap_frame,
)

_LOGGER = logging.getLogger(__name__)

PROTOCOL_NAME = "1097"
MODEL = "GEN3 / GEN3 PLUS (1097)"
SENSOR_LIST = 0x1097
MAX_PV_COUNT = 6

BLOCKS = (
    (0x03, 0x1000, 0x100F),
    (0x03, 0x1100, 0x110F),
    (0x03, 0x1200, 0x120F),
    (0x03, 0x1210, 0x121F),
    (0x03, 0x1300, 0x130F),
    (0x03, 0x1310, 0x131F),
    (0x03, 0x1320, 0x132F),
)

ALARM_REGISTERS = (0x1105, 0x1106, 0x1107, 0x1108)
ALARM_MEASUREMENT_KEYS = frozenset(
    {"alarm_active", *(f"alarm_code_{index}_raw" for index in range(1, 5))}
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


def crc16_modbus(data: bytes) -> bytes:
    """Return a standard Modbus RTU CRC in low-byte-first order."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc.to_bytes(2, "little")


def build_modbus_request(function: int, start: int, end: int) -> bytes:
    """Build a standard Modbus RTU register read request."""
    count = end - start + 1
    body = bytes((0x01, function)) + start.to_bytes(2, "big")
    body += count.to_bytes(2, "big")
    return body + crc16_modbus(body)


def parse_modbus_response(
    frame: bytes, function: int, start: int, end: int
) -> dict[int, int]:
    """Validate a Modbus RTU response and return big-endian registers."""
    if len(frame) < 5 or frame[0] != 0x01:
        raise TsunProtocolError("Invalid 1097 Modbus frame")
    if crc16_modbus(frame[:-2]) != frame[-2:]:
        raise TsunProtocolError("Invalid 1097 Modbus CRC")
    if frame[1] == (function | 0x80):
        raise TsunProtocolError(f"1097 Modbus exception 0x{frame[2]:02X}")
    if frame[1] != function:
        raise TsunProtocolError("Unexpected 1097 Modbus function")

    count = end - start + 1
    data_length = frame[2]
    if data_length != count * 2 or len(frame) != 3 + data_length + 2:
        raise TsunProtocolError("Unexpected 1097 Modbus data length")

    values = frame[3 : 3 + data_length]
    return {
        start + index: int.from_bytes(
            values[index * 2 : index * 2 + 2], "big"
        )
        for index in range(count)
    }


def _u32(registers: dict[int, int], high_address: int) -> int:
    """Decode a 32-bit value stored high-register first."""
    return (registers[high_address] << 16) | registers[high_address + 1]


def detect_pv_count(registers: dict[int, int]) -> int:
    """Return the highest PV input observed in 1097 telemetry."""
    detected = 0
    for number in range(1, MAX_PV_COUNT + 1):
        base = 0x1302 + (number - 1) * 7
        addresses = range(base, base + 7)
        if any(
            0 < registers.get(address, 0) < 0xFFFF
            for address in addresses
        ):
            detected = number
    return detected


def _measurement_keys(pv_count: int) -> frozenset[str]:
    """Return measurement keys for the advertised number of PV inputs."""
    return AC_MEASUREMENT_KEYS | ALARM_MEASUREMENT_KEYS | frozenset(
        f"pv{number}_{measurement}"
        for number in range(1, pv_count + 1)
        for measurement in PV_MEASUREMENT_NAMES
    )


def decode_measurements(
    registers: dict[int, int], pv_count: int
) -> dict[str, float | int]:
    """Decode the 1097 AC and PV measurement map."""
    data: dict[str, float | int] = {
        "ac_voltage": registers[0x1200] * 0.1,
        "ac_current": registers[0x1201] * 0.01,
        "ac_power": registers[0x1202] * 0.1,
        "ac_frequency": registers[0x1209] * 0.01,
        "ac_energy_today": registers[0x1212] * 0.01,
        "ac_energy_total": _u32(registers, 0x1213) * 0.01,
    }

    # PV1 begins at 0x1302; every PV channel spans seven registers:
    # voltage, current, power, daily energy (u32), total energy (u32).
    for number in range(1, pv_count + 1):
        base = 0x1302 + (number - 1) * 7
        prefix = f"pv{number}"
        data[f"{prefix}_voltage"] = registers[base] * 0.1
        data[f"{prefix}_current"] = registers[base + 1] * 0.01
        data[f"{prefix}_power"] = registers[base + 2] * 0.1
        data[f"{prefix}_energy_today"] = _u32(registers, base + 3) * 0.01
        data[f"{prefix}_energy_total"] = _u32(registers, base + 5) * 0.01

    data["dc_power_total"] = round(
        sum(
            float(data[f"pv{number}_power"])
            for number in range(1, pv_count + 1)
        ),
        1,
    )
    return data


def decode_alarms(registers: dict[int, int]) -> dict[str, float | int]:
    """Expose raw 1097 event values without assuming a fault-code table."""
    if not all(address in registers for address in ALARM_REGISTERS):
        return {}

    data: dict[str, float | int] = {}
    for index, address in enumerate(ALARM_REGISTERS, 1):
        data[f"alarm_code_{index}_raw"] = registers[address]
    data["alarm_active"] = int(
        any(registers[address] for address in ALARM_REGISTERS)
    )
    return data


class Tsun1097Client:
    """Async protocol 1097 client for one TSUN logger."""

    model = MODEL
    protocol_name = PROTOCOL_NAME

    def __init__(
        self, host: str, port: int, logger_sn: int, timeout: float = 10
    ) -> None:
        self.host = host
        self.port = port
        self.logger_sn = logger_sn
        self.timeout = timeout
        self._pv_count = 1
        self._trace = ProtocolTrace(PROTOCOL_NAME)

    @property
    def pv_count(self) -> int:
        """Return the number of PV inputs advertised by the device."""
        return self._pv_count

    @property
    def measurement_keys(self) -> frozenset[str]:
        """Return measurement keys supported by the detected hardware."""
        return _measurement_keys(self._pv_count)

    @property
    def diagnostic_trace(self) -> tuple[dict[str, object], ...]:
        """Return recent protocol transactions without connection identifiers."""
        return self._trace.events

    async def _read_block(self, block: tuple[int, int, int]) -> dict[int, int]:
        function, start, end = block
        payload = build_modbus_request(function, start, end)
        request = build_ap_frame(
            self.logger_sn,
            payload,
            sensor_list=SENSOR_LIST,
        )

        writer: asyncio.StreamWriter | None = None
        stage = "connection"
        response: bytes | None = None
        protocol_response: bytes | None = None

        try:
            async with asyncio.timeout(self.timeout):
                _LOGGER.debug(
                    "1097 diagnostic: opening connection for registers "
                    "0x%04X-0x%04X",
                    start,
                    end,
                )
                reader, writer = await asyncio.open_connection(
                    self.host, self.port
                )
                stage = "send"
                _LOGGER.debug(
                    "1097 diagnostic request for registers 0x%04X-0x%04X: %s",
                    start,
                    end,
                    payload.hex(" ").upper(),
                )
                writer.write(request)
                await writer.drain()
                stage = "receive"
                response = await read_ap_frame(reader)

            stage = "validation"
            protocol_response = parse_ap_frame(response)
            _LOGGER.debug(
                "1097 diagnostic response for registers 0x%04X-0x%04X: %s",
                start,
                end,
                protocol_response.hex(" ").upper(),
            )
            registers = parse_modbus_response(
                protocol_response, function, start, end
            )
            self._trace.record(
                function=function,
                start=start,
                end=end,
                stage="complete",
                request_payload=payload,
                response_payload=protocol_response,
                response_bytes=len(response),
            )
            return registers

        except Exception as err:
            self._trace.record(
                function=function,
                start=start,
                end=end,
                stage=stage,
                request_payload=payload,
                response_payload=protocol_response,
                response_bytes=len(response) if response is not None else None,
                error=err,
            )
            detail = (
                str(err)
                if isinstance(err, TsunProtocolError)
                else type(err).__name__
            )
            _LOGGER.debug(
                "1097 diagnostic failure during %s for registers "
                "0x%04X-0x%04X: %s",
                stage,
                start,
                end,
                detail,
            )
            raise

        finally:
            if writer is not None:
                writer.close()
                await writer.wait_closed()

    async def async_read_all(self) -> TsunReadResult:
        """Read one complete 1097 telemetry update."""
        started = time.monotonic()
        registers: dict[int, int] = {}

        for block in BLOCKS:
            registers.update(await self._read_block(block))

        # Keep the highest input ever observed so entities never disappear.
        detected_pv_count = detect_pv_count(registers)
        if detected_pv_count:
            self._pv_count = max(self._pv_count, detected_pv_count)

        measurements = decode_measurements(registers, self._pv_count)
        measurements.update(decode_alarms(registers))

        return TsunReadResult(
            measurements=measurements,
            duration_ms=round((time.monotonic() - started) * 1000),
            blocks_ok=len(BLOCKS),
        )
