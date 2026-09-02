# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Shared TSUN AP transport framing."""

from __future__ import annotations

import asyncio
from collections import deque
from copy import deepcopy
from typing import Any

STREAM_CLOSE_TIMEOUT = 2.0


class TsunProtocolError(Exception):
    """Raised when a TSUN protocol frame is invalid."""


def safe_error_details(error: Exception) -> dict[str, str]:
    """Return diagnostic error details without network addresses or identifiers."""
    details = {"type": type(error).__name__}
    if isinstance(error, TsunProtocolError):
        details["detail"] = str(error)
    return details


class ProtocolTrace:
    """Keep a small privacy-safe circular trace of protocol transactions."""

    def __init__(self, protocol: str, max_events: int = 24) -> None:
        self.protocol = protocol
        self._events: deque[dict[str, Any]] = deque(maxlen=max_events)

    def record(
        self,
        *,
        function: int,
        start: int,
        end: int,
        stage: str,
        request_payload: bytes,
        address_tag: int | None = None,
        response_payload: bytes | None = None,
        response_bytes: int | None = None,
        error: Exception | None = None,
    ) -> None:
        """Record one transaction without the AP envelope or connection details."""
        event: dict[str, Any] = {
            "protocol": self.protocol,
            "function": f"0x{function:02X}",
            "start_register": f"0x{start:04X}",
            "end_register": f"0x{end:04X}",
            "stage": stage,
            "request_payload": request_payload.hex(" ").upper(),
        }
        if address_tag is not None:
            event["address_tag"] = f"0x{address_tag:02X}"
        if response_payload is not None:
            event["response_payload"] = response_payload.hex(" ").upper()
        if response_bytes is not None:
            event["response_bytes"] = response_bytes
        if error is not None:
            event["error"] = safe_error_details(error)
        self._events.append(event)

    @property
    def events(self) -> tuple[dict[str, Any], ...]:
        """Return a detached snapshot suitable for diagnostics export."""
        return tuple(deepcopy(event) for event in self._events)


def checksum_ap(data: bytes) -> int:
    """Return the AP additive checksum."""
    return sum(data) & 0xFF


def format_ap_frame_for_log(frame: bytes) -> str:
    """Return a readable AP frame with the logger identifier hidden."""
    octets = [f"{byte:02X}" for byte in frame]
    for index in range(7, min(11, len(octets))):
        octets[index] = "XX"
    return " ".join(octets)


def build_ap_frame(
    logger_sn: int,
    payload: bytes,
    sensor_list: int = 0,
) -> bytes:
    """Wrap a local-protocol request in a TSUN AP frame."""
    data = b"\x02" + sensor_list.to_bytes(2, "little") + bytes(12) + payload
    scope = (
        len(data).to_bytes(2, "little")
        + b"\x10\x45\x00\x00"
        + logger_sn.to_bytes(4, "little")
        + data
    )
    return b"\xA5" + scope + bytes((checksum_ap(scope), 0x15))


def _validate_ap_frame(frame: bytes) -> None:
    """Validate the common AP response envelope."""
    if len(frame) < 27 or frame[0] != 0xA5 or frame[-1] != 0x15:
        raise TsunProtocolError("Invalid AP frame markers or length")
    expected_length = int.from_bytes(frame[1:3], "little") + 13
    if len(frame) != expected_length:
        raise TsunProtocolError(
            f"Invalid AP frame length: {len(frame)} != {expected_length}"
        )
    if checksum_ap(frame[1:-2]) != frame[-2]:
        raise TsunProtocolError("Invalid AP checksum")


def extract_ap_logger_sn(frame: bytes) -> int:
    """Return the logger identifier carried by a validated AP response."""
    _validate_ap_frame(frame)
    logger_sn = int.from_bytes(frame[7:11], "little")
    if logger_sn == 0:
        raise TsunProtocolError("AP response does not contain a logger identifier")
    return logger_sn


def parse_ap_frame(frame: bytes) -> bytes:
    """Validate an AP response and return its embedded protocol payload."""
    _validate_ap_frame(frame)
    if frame[11] != 0x02:
        raise TsunProtocolError(f"Unexpected AP frame type 0x{frame[11]:02X}")
    if frame[12] != 0x01:
        raise TsunProtocolError(f"AP returned status 0x{frame[12]:02X}")
    return frame[25:-2]


async def read_ap_frame(reader: asyncio.StreamReader) -> bytes:
    """Read one complete AP frame from a TCP stream."""
    header = await reader.readexactly(3)
    if header[0] != 0xA5:
        raise TsunProtocolError("Invalid AP start marker")
    remaining = int.from_bytes(header[1:3], "little") + 10
    return header + await reader.readexactly(remaining)


async def async_close_writer(writer: asyncio.StreamWriter | None) -> None:
    """Close a TCP writer without turning a completed poll into a failure."""
    if writer is None:
        return
    try:
        writer.close()
    except (OSError, RuntimeError):
        return
    try:
        async with asyncio.timeout(STREAM_CLOSE_TIMEOUT):
            await writer.wait_closed()
    except (OSError, TimeoutError, RuntimeError):
        return
