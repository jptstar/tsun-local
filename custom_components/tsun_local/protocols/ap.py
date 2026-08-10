# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Shared TSUN AP transport framing."""

from __future__ import annotations

import asyncio


class TsunProtocolError(Exception):
    """Raised when a TSUN protocol frame is invalid."""


def checksum_ap(data: bytes) -> int:
    """Return the AP additive checksum."""
    return sum(data) & 0xFF


def build_ap_frame(logger_sn: int, payload: bytes) -> bytes:
    """Wrap a local-protocol request in a TSUN AP frame."""
    data = b"\x02\x00\x00" + bytes(12) + payload
    scope = (
        len(data).to_bytes(2, "little")
        + b"\x10\x45\x00\x00"
        + logger_sn.to_bytes(4, "little")
        + data
    )
    return b"\xA5" + scope + bytes((checksum_ap(scope), 0x15))


def parse_ap_frame(frame: bytes) -> bytes:
    """Validate an AP response and return its embedded protocol payload."""
    if len(frame) < 27 or frame[0] != 0xA5 or frame[-1] != 0x15:
        raise TsunProtocolError("Invalid AP frame markers or length")
    expected_length = int.from_bytes(frame[1:3], "little") + 13
    if len(frame) != expected_length:
        raise TsunProtocolError(
            f"Invalid AP frame length: {len(frame)} != {expected_length}"
        )
    if checksum_ap(frame[1:-2]) != frame[-2]:
        raise TsunProtocolError("Invalid AP checksum")
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
