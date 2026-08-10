# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Common protocol interfaces for TSUN Local."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

DEFAULT_PROTOCOL = "1511"


@dataclass(frozen=True, slots=True)
class TsunReadResult:
    """Measurements and diagnostics returned by one complete device poll."""

    measurements: dict[str, float | int]
    duration_ms: int
    blocks_ok: int


class TsunProtocolClient(Protocol):
    """Interface implemented by every TSUN Local protocol adapter."""

    model: str
    protocol_name: str
    measurement_keys: frozenset[str]

    async def async_read_all(self) -> TsunReadResult:
        """Read and decode one complete device update."""


def create_protocol_client(
    protocol_name: str,
    host: str,
    port: int,
    logger_sn: int,
) -> TsunProtocolClient:
    """Create the adapter registered for a local TSUN protocol."""
    if protocol_name == "1511":
        from .protocol_1511 import Tsun1511Client

        return Tsun1511Client(host, port, logger_sn)
    raise ValueError(f"Unsupported TSUN protocol: {protocol_name}")
