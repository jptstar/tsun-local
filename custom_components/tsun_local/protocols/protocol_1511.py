# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Local TSUN 1511 protocol transport and decoder."""

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

PROTOCOL_NAME = "1511"
MODEL = "TITAN"
MAX_PV_COUNT = 6
DIAGNOSTIC_INTERVAL = 300.0
COUNTRY_PROFILE_REGISTER = 0x07D0

_LOGGER = logging.getLogger(__name__)

BLOCKS = (
    (0xA1, 0x01, 0x0BB8, 0x0BD0),
    (0xA3, 0x03, 0x0E10, 0x0E2D),
    (0xA4, 0x04, 0x0ED8, 0x0EF5),
)

ALARM_BLOCKS = (
    (0xA2, 0x02, 0x0CE4, 0x0CE7),
)

DIAGNOSTIC_BLOCKS = (
    # Full native A1/01 3000-3031 block, validated on MP3000 firmware 1.03.
    (0xA1, 0x01, 0x0BB8, 0x0BD7),
    # Native TITAN A1/21 block: decimal registers 2000-2095.
    (0xA1, 0x21, 0x07D0, 0x082F),
)

GLOBAL_ALARM_REGISTERS = (0x0BBB, 0x0BBC, 0x0BBD, 0x0BBE)
SECONDARY_ALARM_REGISTERS = (0x0CE4, 0x0CE5, 0x0CE6, 0x0CE7)
PV_ALARM_REGISTERS = (0x0E16, 0x0E1D, 0x0E24, 0x0EDE, 0x0EE5, 0x0EEC)

# On validated MP3000 hardware, bit 0x2000 in global alarm word 1 is
# repeatedly observed at dawn, dusk and during very low irradiance. Count the
# position while keeping it distinct from the operating fault state when it is
# the only active bit. Its exact functional meaning remains unconfirmed.
LOW_SOLAR_STATUS_REGISTER = GLOBAL_ALARM_REGISTERS[1]
LOW_SOLAR_STATUS_MASK = 0x2000

ALARM_MEASUREMENT_KEYS = frozenset(
    {
        "alarm_active",
        "alarm_active_count",
        "inverter_operating_state",
        *(f"alarm_global_{index}_raw" for index in range(4)),
        *(f"alarm_secondary_{index}_raw" for index in range(4)),
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

TITAN_DIAGNOSTIC_KEYS = frozenset(
    {
        "inverter_status_raw",
        "rated_power",
        "max_designed_power",
        "register_3018_raw",
        "inverter_temperature",
        "ambient_temperature",
        "country_profile_raw",
    }
)

ADVANCED_GRID_KEYS = frozenset(
    {
        "grid_qp_voltage_threshold",
        "grid_recovery_rate",
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
        "grid_overvoltage_10min",
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
        "grid_overfrequency_reduction_frequency",
        "grid_overfrequency_reduction_coefficient",
        "overtemperature_protection_temperature",
        "grid_start_upper_voltage_limit",
        "grid_start_lower_voltage_limit",
        "grid_start_upper_frequency_limit",
        "grid_start_lower_frequency_limit",
        "output_coefficient_candidate",
    }
)

ADVANCED_GRID_REGISTERS: dict[str, tuple[int, float]] = {
    # The ten fields marked "field validation" below correlate one-to-one
    # between a real MP3000 A1/21 dump and the names/values exposed by the
    # TSUN/Talent device profile. Their local addresses still require an
    # independent physical change/test before being considered validated.
    "grid_recovery_rate": (0x07D3, 0.5),  # field validation
    "grid_overvoltage_recovery_voltage": (0x07D4, 0.1),
    "grid_undervoltage_recovery_voltage": (0x07D5, 0.1),
    "grid_overfrequency_recovery_frequency": (0x07D6, 0.01),
    "grid_underfrequency_recovery_frequency": (0x07D7, 0.01),
    "grid_undervoltage_level_1": (0x07D9, 0.1),
    "grid_undervoltage_level_2": (0x07DA, 0.1),
    "grid_undervoltage_time_1": (0x07DB, 0.02),
    "grid_undervoltage_time_2": (0x07DC, 0.02),
    "grid_overvoltage_level_1": (0x07DD, 0.1),
    "grid_overvoltage_level_2": (0x07DE, 0.1),
    "grid_overvoltage_time_1": (0x07DF, 0.02),
    "grid_overvoltage_time_2": (0x07E0, 0.02),
    "grid_overvoltage_10min": (0x07E1, 0.1),  # field validation
    "grid_underfrequency_level_1": (0x07E2, 0.01),
    "grid_underfrequency_level_2": (0x07E3, 0.01),
    "grid_underfrequency_time_1": (0x07E4, 0.02),
    "grid_underfrequency_time_2": (0x07E5, 0.02),
    "grid_overfrequency_level_1": (0x07E6, 0.01),
    "grid_overfrequency_level_2": (0x07E7, 0.01),
    "grid_overfrequency_time_1": (0x07E8, 0.02),
    "grid_overfrequency_time_2": (0x07E9, 0.02),
    "grid_undervoltage_level_3": (0x07EA, 0.1),
    "grid_undervoltage_time_3": (0x07EB, 0.02),
    # Candidate inferred from the adjacent protocol layout; keep the
    # candidate label until confirmed independently on 1511 hardware.
    "output_coefficient_candidate": (0x07EC, 100 / 1024),
    "grid_overfrequency_reduction_frequency": (0x07EE, 0.01),  # field validation
    "grid_overfrequency_reduction_coefficient": (0x07EF, 1.0),  # field validation
    "overtemperature_protection_temperature": (0x07F0, 1.0),  # field validation
    "grid_start_upper_voltage_limit": (0x07FB, 0.1),  # field validation
    "grid_start_lower_voltage_limit": (0x07FC, 0.1),  # field validation
    "grid_start_upper_frequency_limit": (0x07FD, 0.01),  # field validation
    "grid_start_lower_frequency_limit": (0x07FE, 0.01),  # field validation
    "grid_qp_voltage_threshold": (0x0800, 1.0),  # field validation
}


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
    return (
        AC_MEASUREMENT_KEYS
        | TITAN_DIAGNOSTIC_KEYS
        | ADVANCED_GRID_KEYS
        | ALARM_MEASUREMENT_KEYS
        | frozenset(
            f"pv{number}_{measurement}"
            for number in range(1, pv_count + 1)
            for measurement in PV_MEASUREMENT_NAMES
        )
        | frozenset(f"pv{number}_alarm_raw" for number in range(1, pv_count + 1))
    )


def detect_pv_count(registers: dict[int, int]) -> int:
    """Detect the highest populated PV input while always retaining PV1."""
    pv_bases = (0x0E10, 0x0E17, 0x0E1E, 0x0ED8, 0x0EDF, 0x0EE6)
    pv_total_pairs = (0x0E28, 0x0E2A, 0x0E2C, 0x0EF0, 0x0EF2, 0x0EF4)
    detected = 1
    for number, (base, total_pair) in enumerate(zip(pv_bases, pv_total_pairs), 1):
        addresses = (base, base + 1, base + 2, base + 5, total_pair, total_pair + 1)
        if any(0 < registers.get(address, 0) < 0xFFFF for address in addresses):
            detected = number
    return detected


def decode_measurements(
    registers: dict[int, int], pv_count: int = 1
) -> dict[str, float | int]:
    """Decode the validated AC and PV register map."""
    data: dict[str, float | int] = {
        "inverter_status_raw": registers[0x0BB8],
        "ac_voltage": registers[0x0BC4] * 0.1,
        "ac_current": registers[0x0BC5] * 0.01,
        "ac_frequency": registers[0x0BC7] * 0.01,
        "inverter_temperature": registers[0x0BC9] - 40,
        "rated_power": registers[0x0BCC],
        "ac_power": registers[0x0BCD] * 0.1,
        "ac_energy_today": registers[0x0BCE] * 0.01,
        "ac_energy_total": _u32_type5(registers, 0x0BCF) * 0.01,
    }
    if 0x0BCA in registers:
        data["register_3018_raw"] = registers[0x0BCA]
    if 0x0BD4 in registers:
        data["ambient_temperature"] = registers[0x0BD4] - 40
    if 0x07FA in registers:
        data["max_designed_power"] = registers[0x07FA]

    pv_bases = (0x0E10, 0x0E17, 0x0E1E, 0x0ED8, 0x0EDF, 0x0EE6)
    pv_total_pairs = (0x0E28, 0x0E2A, 0x0E2C, 0x0EF0, 0x0EF2, 0x0EF4)
    for number, (base, total_pair) in enumerate(
        zip(pv_bases[:pv_count], pv_total_pairs[:pv_count]), 1
    ):
        prefix = f"pv{number}"
        data[f"{prefix}_voltage"] = registers[base] * 0.1
        data[f"{prefix}_current"] = registers[base + 1] * 0.01
        data[f"{prefix}_power"] = registers[base + 2] * 0.1
        data[f"{prefix}_energy_today"] = registers.get(base + 5, 0) * 0.01
        data[f"{prefix}_energy_total"] = _u32_type5(registers, total_pair) * 0.01
    data["dc_power_total"] = round(
        sum(float(data[f"pv{number}_power"]) for number in range(1, pv_count + 1)), 1
    )
    return data


def decode_advanced_diagnostics(
    registers: dict[int, int],
) -> dict[str, float | int]:
    """Decode read-only grid protection and field-validation diagnostics."""
    data: dict[str, float | int] = {
        key: round(registers[address] * factor, 2)
        for key, (address, factor) in ADVANCED_GRID_REGISTERS.items()
        if address in registers
    }

    # Stefan Allius's public 1097 country table identifies code 8 as France.
    # The live MP3000 1511 A1/21 block repeatedly reports raw 8 at 0x07D0.
    # Expose the raw candidate only; independent validation is still pending.
    if COUNTRY_PROFILE_REGISTER in registers:
        data["country_profile_raw"] = registers[COUNTRY_PROFILE_REGISTER]

    return data


def decode_alarms(
    registers: dict[int, int], pv_count: int
) -> dict[str, float | int | str]:
    """Expose all 1511 alarm words while separating low-solar standby."""
    data: dict[str, float | int | str] = {}
    fault_values: list[int] = []
    active_values: list[int] = []
    low_solar = False

    for index, address in enumerate(GLOBAL_ALARM_REGISTERS):
        if address in registers:
            value = registers[address]
            data[f"alarm_global_{index}_raw"] = value
            active_values.append(value)
            fault_value = value
            if address == LOW_SOLAR_STATUS_REGISTER:
                low_solar = bool(value & LOW_SOLAR_STATUS_MASK)
                fault_value &= ~LOW_SOLAR_STATUS_MASK
            fault_values.append(fault_value)

    secondary_complete = all(
        address in registers for address in SECONDARY_ALARM_REGISTERS
    )
    for index, address in enumerate(SECONDARY_ALARM_REGISTERS):
        if address in registers:
            value = registers[address]
            data[f"alarm_secondary_{index}_raw"] = value
            active_values.append(value)
            fault_values.append(value)

    # Decode all six PV alarm words independently from topology detection.
    # This preserves every alarm position even before a PV input has produced
    # enough telemetry to receive its own Home Assistant sensor entities.
    for number, address in enumerate(PV_ALARM_REGISTERS, 1):
        if address in registers:
            value = registers[address]
            data[f"pv{number}_alarm_raw"] = value
            active_values.append(value)
            fault_values.append(value)

    # A complete fault status still requires the separate secondary-alarm
    # block. Raw values remain available if that optional read fails.
    if secondary_complete:
        has_fault = any(fault_values)
        data["alarm_active"] = int(any(active_values))
        data["alarm_active_count"] = sum(
            value.bit_count() for value in active_values
        )
        if has_fault:
            operating_state = "fault"
        elif low_solar:
            operating_state = "standby_low_solar"
        elif registers.get(0x0BB8) == 1:
            operating_state = "active"
        else:
            operating_state = "standby"
        data["inverter_operating_state"] = operating_state

    return data


class Tsun1511Client:
    """Async protocol 1511 client for one TSUN logger."""

    model = MODEL
    protocol_name = PROTOCOL_NAME

    def __init__(
        self, host: str, port: int, logger_sn: int, timeout: float = 10
    ) -> None:
        self.host = host
        self.port = port
        self.logger_sn = logger_sn
        self.timeout = timeout
        # Start conservatively with PV1. Additional inputs are added after
        # they are observed in live or accumulated telemetry and never removed.
        self._pv_count = 1
        self._trace = ProtocolTrace(PROTOCOL_NAME)
        self._diagnostic_registers: dict[int, int] = {}
        # Collect optional diagnostics on the first poll, then at a slow cadence.
        # A diagnostic failure never makes normal telemetry fail.
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

    async def _read_block(self, block: tuple[int, int, int, int]) -> dict[int, int]:
        address_tag, function, start, end = block
        payload = build_1511_request(address_tag, function, start, end)
        request = build_ap_frame(self.logger_sn, payload)
        writer: asyncio.StreamWriter | None = None
        stage = "connection"
        response: bytes | None = None
        protocol_response: bytes | None = None
        try:
            async with asyncio.timeout(self.timeout):
                _LOGGER.debug(
                    "1511 diagnostic: opening connection for registers 0x%04X-0x%04X",
                    start,
                    end,
                )
                reader, writer = await asyncio.open_connection(self.host, self.port)
                stage = "send"
                _LOGGER.debug(
                    "1511 diagnostic request for registers 0x%04X-0x%04X: %s",
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
                "1511 diagnostic response for registers 0x%04X-0x%04X: %s",
                start,
                end,
                protocol_response.hex(" ").upper(),
            )
            registers = parse_1511_response(
                protocol_response, address_tag, function, start, end
            )
            self._trace.record(
                address_tag=address_tag,
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
                address_tag=address_tag,
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
                "1511 diagnostic failure during %s for registers "
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
        """Read telemetry plus optional alarm and diagnostic blocks sequentially."""
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
                    "1511 alarm block 0x%04X-0x%04X is unavailable: %s",
                    block[2],
                    block[3],
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
                        "1511 diagnostic block %d-%d is unavailable: %s",
                        block[2],
                        block[3],
                        type(err).__name__,
                    )
                else:
                    blocks_ok += 1
        registers.update(self._diagnostic_registers)

        self._pv_count = max(self._pv_count, detect_pv_count(registers))
        measurements = decode_measurements(registers, self._pv_count)
        measurements.update(decode_advanced_diagnostics(registers))
        measurements.update(decode_alarms(registers, self._pv_count))
        return TsunReadResult(
            measurements=measurements,
            duration_ms=round((time.monotonic() - started) * 1000),
            blocks_ok=blocks_ok,
        )
