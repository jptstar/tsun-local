# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Local TSUN 02B0 Modbus transport and decoder."""

from __future__ import annotations

import asyncio
import logging
import time

from . import TsunReadResult
from .ap import (
    ProtocolTrace,
    TsunProtocolError,
    async_close_writer,
    build_ap_frame,
    parse_ap_frame,
    read_ap_frame,
)

_LOGGER = logging.getLogger(__name__)

PROTOCOL_NAME = "02b0"
MODEL = "GEN3 / GEN3 PLUS"
SENSOR_LIST = 0x02B0
DIAGNOSTIC_INTERVAL = 300.0

BLOCKS = (
    # 0x3008 adds the inverter firmware register; 0x300C is the inverter
    # temperature and already sits inside this regular telemetry block.
    (0x03, 0x3008, 0x301E),
    (0x03, 0x301F, 0x302A),
)

ALARM_BLOCKS = (
    # Include 0x3000 so raw inverter status is collected with the alarm words.
    (0x03, 0x3000, 0x3006),
)

DIAGNOSTIC_BLOCKS = (
    # Retain the established max-power probe while extending the same read-only
    # area with status and compliance metadata.
    (0x03, 0x2007, 0x2007),
    (0x03, 0x2000, 0x2010),
    # Advanced read-only grid parameters and output coefficient.
    (0x03, 0x2014, 0x202C),
)

ALARM_REGISTERS = (0x3003, 0x3004, 0x3005, 0x3006)
ALARM_MEASUREMENT_KEYS = frozenset(
    {
        "alarm_active",
        "alarm_active_count",
        "active_alarm_names",
        *(f"alarm_code_{index}_raw" for index in range(1, 5)),
    }
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
DEVICE_DIAGNOSTIC_KEYS = frozenset(
    {
        "inverter_status_raw",
        "rated_power",
        "max_designed_power",
        "inverter_firmware_version",
        "inverter_temperature",
        "boot_status_raw",
        "dsp_status_raw",
        "work_mode_raw",
        "output_shutdown_raw",
        "rated_level_raw",
        "input_coefficient",
        "product_compliance_type_raw",
    }
)
ADVANCED_GRID_KEYS = frozenset(
    {
        "grid_overvoltage_recovery_voltage",
        "grid_undervoltage_recovery_voltage",
        "grid_overfrequency_recovery_frequency",
        "grid_underfrequency_recovery_frequency",
        "grid_undervoltage_level_1",
        "grid_undervoltage_level_2",
        "grid_undervoltage_time_1",
        "grid_undervoltage_time_2",
        "grid_overvoltage_level_1",
        "grid_overvoltage_level_2",
        "grid_overvoltage_time_1",
        "grid_overvoltage_time_2",
        "grid_underfrequency_level_1",
        "grid_underfrequency_level_2",
        "grid_underfrequency_time_1",
        "grid_underfrequency_time_2",
        "grid_overfrequency_level_1",
        "grid_overfrequency_level_2",
        "grid_overfrequency_time_1",
        "grid_overfrequency_time_2",
        "grid_undervoltage_level_3",
        "grid_undervoltage_time_3",
        "output_coefficient",
    }
)

ADVANCED_GRID_REGISTERS: dict[str, tuple[int, float]] = {
    "grid_overvoltage_recovery_voltage": (0x2014, 0.1),
    "grid_undervoltage_recovery_voltage": (0x2015, 0.1),
    "grid_overfrequency_recovery_frequency": (0x2016, 0.01),
    "grid_underfrequency_recovery_frequency": (0x2017, 0.01),
    "grid_undervoltage_level_1": (0x2019, 0.1),
    "grid_undervoltage_level_2": (0x201A, 0.1),
    "grid_undervoltage_time_1": (0x201B, 0.02),
    "grid_undervoltage_time_2": (0x201C, 0.02),
    "grid_overvoltage_level_1": (0x201D, 0.1),
    "grid_overvoltage_level_2": (0x201E, 0.1),
    "grid_overvoltage_time_1": (0x201F, 0.02),
    "grid_overvoltage_time_2": (0x2020, 0.02),
    "grid_underfrequency_level_1": (0x2022, 0.01),
    "grid_underfrequency_level_2": (0x2023, 0.01),
    "grid_underfrequency_time_1": (0x2024, 0.02),
    "grid_underfrequency_time_2": (0x2025, 0.02),
    "grid_overfrequency_level_1": (0x2026, 0.01),
    "grid_overfrequency_level_2": (0x2027, 0.01),
    "grid_overfrequency_time_1": (0x2028, 0.02),
    "grid_overfrequency_time_2": (0x2029, 0.02),
    "grid_undervoltage_level_3": (0x202A, 0.1),
    "grid_undervoltage_time_3": (0x202B, 0.02),
    "output_coefficient": (0x202C, 100 / 1024),
}


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
        raise TsunProtocolError("Invalid 02B0 Modbus frame")
    if crc16_modbus(frame[:-2]) != frame[-2:]:
        raise TsunProtocolError("Invalid 02B0 Modbus CRC")
    if frame[1] == (function | 0x80):
        raise TsunProtocolError(f"02B0 Modbus exception 0x{frame[2]:02X}")
    if frame[1] != function:
        raise TsunProtocolError("Unexpected 02B0 Modbus function")
    count = end - start + 1
    data_length = frame[2]
    if data_length != count * 2 or len(frame) != 3 + data_length + 2:
        raise TsunProtocolError("Unexpected 02B0 Modbus data length")
    values = frame[3 : 3 + data_length]
    return {
        start + index: int.from_bytes(values[index * 2 : index * 2 + 2], "big")
        for index in range(count)
    }


def _u32_type5(registers: dict[int, int], high_address: int) -> int:
    """Decode parser type 5: high 16-bit register followed by low register."""
    return (registers[high_address] << 16) | registers[high_address + 1]


def firmware_version(value: int) -> str:
    """Decode the packed TSUN 16-bit firmware version used by 02B0."""
    raw = f"{value:04X}"
    return f"V{raw[0]}.{raw[1]}.{raw[2:]}"


def detect_pv_count(registers: dict[int, int]) -> int:
    """Detect the highest populated PV input while always retaining PV1."""
    detected = 1
    for number in range(1, 5):
        base = 0x3010 + (number - 1) * 3
        energy_base = 0x301F + (number - 1) * 3
        addresses = (
            base,
            base + 1,
            base + 2,
            energy_base,
            energy_base + 1,
            energy_base + 2,
        )
        if any(0 < registers.get(address, 0) < 0xFFFF for address in addresses):
            detected = number
    return detected


def _measurement_keys(pv_count: int) -> frozenset[str]:
    """Return keys exposed for the detected number of PV inputs."""
    return (
        AC_MEASUREMENT_KEYS
        | DEVICE_DIAGNOSTIC_KEYS
        | ADVANCED_GRID_KEYS
        | ALARM_MEASUREMENT_KEYS
        | frozenset(
            f"pv{number}_{measurement}"
            for number in range(1, pv_count + 1)
            for measurement in PV_MEASUREMENT_NAMES
        )
    )


def decode_measurements(
    registers: dict[int, int], pv_count: int
) -> dict[str, float | int | str]:
    """Decode the official 02B0 AC and PV measurement map."""
    data: dict[str, float | int | str] = {
        "ac_voltage": registers[0x3009] * 0.1,
        "ac_current": registers[0x300A] * 0.01,
        "ac_frequency": registers[0x300B] * 0.01,
        "rated_power": registers[0x300E],
        "ac_power": registers[0x300F] * 0.1,
        "ac_energy_today": registers[0x301C] * 0.01,
        "ac_energy_total": _u32_type5(registers, 0x301D) * 0.01,
    }
    if 0x3000 in registers:
        data["inverter_status_raw"] = registers[0x3000]
    if 0x3008 in registers:
        data["inverter_firmware_version"] = firmware_version(registers[0x3008])
    if 0x300C in registers:
        data["inverter_temperature"] = registers[0x300C] - 40
    if 0x2007 in registers:
        data["max_designed_power"] = registers[0x2007]

    for number in range(1, pv_count + 1):
        base = 0x3010 + (number - 1) * 3
        energy_base = 0x301F + (number - 1) * 3
        prefix = f"pv{number}"
        data[f"{prefix}_voltage"] = registers[base] * 0.1
        data[f"{prefix}_current"] = registers[base + 1] * 0.01
        data[f"{prefix}_power"] = registers[base + 2] * 0.1
        data[f"{prefix}_energy_today"] = registers[energy_base] * 0.01
        data[f"{prefix}_energy_total"] = _u32_type5(registers, energy_base + 1) * 0.01
    data["dc_power_total"] = round(
        sum(float(data[f"pv{number}_power"]) for number in range(1, pv_count + 1)),
        1,
    )
    return data


def decode_device_diagnostics(
    registers: dict[int, int],
) -> dict[str, float | int]:
    """Decode additional read-only 02B0 status and configuration metadata."""
    raw_registers = {
        "boot_status_raw": 0x2000,
        "dsp_status_raw": 0x2001,
        "work_mode_raw": 0x2003,
        "output_shutdown_raw": 0x2006,
        "rated_level_raw": 0x2008,
        "product_compliance_type_raw": 0x2010,
    }
    data: dict[str, float | int] = {
        key: registers[address]
        for key, address in raw_registers.items()
        if address in registers
    }
    if 0x2009 in registers:
        data["input_coefficient"] = round(registers[0x2009] * 100 / 1024, 2)
    return data


def decode_advanced_diagnostics(registers: dict[int, int]) -> dict[str, float]:
    """Decode read-only grid protection diagnostics."""
    return {
        key: round(registers[address] * factor, 2)
        for key, (address, factor) in ADVANCED_GRID_REGISTERS.items()
        if address in registers
    }


def decode_alarms(registers: dict[int, int]) -> dict[str, float | int]:
    """Expose 02B0 ERR1-ERR4 values without assuming a fault-code table."""
    if not all(address in registers for address in ALARM_REGISTERS):
        return {}

    data: dict[str, float | int] = {}
    for index, address in enumerate(ALARM_REGISTERS, 1):
        data[f"alarm_code_{index}_raw"] = registers[address]
    data["alarm_active"] = int(
        any(registers[address] for address in ALARM_REGISTERS)
    )
    return data


class Tsun02b0Client:
    """Async protocol 02B0 client for one TSUN logger."""

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
        self._diagnostic_registers: dict[int, int] = {}
        self._last_diagnostic_read = 0.0

    @property
    def pv_count(self) -> int:
        """Return the highest PV input detected so far."""
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
        # 02B0 is the protocol's Solarman sensor-list selector. Some loggers
        # tolerate 0x0000, but LSW5BLE/PLAY2 requires the explicit 0x02B0 value.
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
                    "02B0 diagnostic: opening connection for registers 0x%04X-0x%04X",
                    start,
                    end,
                )
                reader, writer = await asyncio.open_connection(self.host, self.port)
                stage = "send"
                _LOGGER.debug(
                    "02B0 diagnostic request for registers 0x%04X-0x%04X: %s",
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
                "02B0 diagnostic response for registers 0x%04X-0x%04X: %s",
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
                "02B0 diagnostic failure during %s for registers "
                "0x%04X-0x%04X: %s",
                stage,
                start,
                end,
                detail,
            )
            raise
        finally:
            await async_close_writer(writer)

    async def async_read_all(self) -> TsunReadResult:
        """Read telemetry and the additional 02B0 alarm block."""
        started = time.monotonic()
        registers: dict[int, int] = {}
        for block in BLOCKS:
            registers.update(await self._read_block(block))
        blocks_ok = len(BLOCKS)
        for block in ALARM_BLOCKS:
            try:
                registers.update(await self._read_block(block))
            except Exception as err:
                _LOGGER.debug(
                    "02B0 alarm block 0x%04X-0x%04X is unavailable: %s",
                    block[1],
                    block[2],
                    type(err).__name__,
                )
            else:
                blocks_ok += 1

        now = time.monotonic()
        if now - self._last_diagnostic_read >= DIAGNOSTIC_INTERVAL:
            self._last_diagnostic_read = now
            for block in DIAGNOSTIC_BLOCKS:
                try:
                    self._diagnostic_registers.update(await self._read_block(block))
                except Exception as err:
                    _LOGGER.debug(
                        "02B0 diagnostic block 0x%04X-0x%04X is unavailable: %s",
                        block[1],
                        block[2],
                        type(err).__name__,
                    )
                else:
                    blocks_ok += 1
        registers.update(self._diagnostic_registers)

        self._pv_count = max(self._pv_count, detect_pv_count(registers))
        measurements = decode_measurements(registers, self._pv_count)
        measurements.update(decode_device_diagnostics(registers))
        measurements.update(decode_advanced_diagnostics(registers))
        measurements.update(decode_alarms(registers))
        return TsunReadResult(
            measurements=measurements,
            duration_ms=round((time.monotonic() - started) * 1000),
            blocks_ok=blocks_ok,
        )
