# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Common protocol interfaces for TSUN Local."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import logging
from typing import Any, Protocol

DEFAULT_PROTOCOL = "auto"
SUPPORTED_PROTOCOLS = ("1511", "1097", "02b0")

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class TsunReadResult:
    """Measurements and diagnostics returned by one complete device poll."""

    measurements: dict[str, float | int]
    duration_ms: int
    blocks_ok: int


class TsunProtocolClient(Protocol):
    """Interface implemented by every TSUN Local protocol adapter."""

    @property
    def model(self) -> str:
        """Return the detected model family."""
        ...

    @property
    def protocol_name(self) -> str:
        """Return the selected local protocol."""
        ...

    @property
    def measurement_keys(self) -> frozenset[str]:
        """Return measurement keys supported by the detected hardware."""
        ...

    @property
    def pv_count(self) -> int:
        """Return the highest PV input detected so far."""
        ...

    @property
    def diagnostic_trace(self) -> tuple[dict[str, Any], ...]:
        """Return recent privacy-safe protocol transactions."""
        ...

    async def async_read_all(self) -> TsunReadResult:
        """Read and decode one complete device update."""
        ...


def _create_specific_client(
    protocol_name: str,
    host: str,
    port: int,
    logger_sn: int,
) -> TsunProtocolClient:
    """Create one concrete local-protocol adapter."""
    if protocol_name == "1511":
        from .protocol_1511 import Tsun1511Client

        return Tsun1511Client(host, port, logger_sn)
    if protocol_name == "1097":
        from .protocol_1097 import Tsun1097Client

        return Tsun1097Client(host, port, logger_sn)
    if protocol_name == "02b0":
        from .protocol_02b0 import Tsun02b0Client

        return Tsun02b0Client(host, port, logger_sn)
    raise ValueError(f"Unsupported TSUN protocol: {protocol_name}")


class TsunAutoClient:
    """Detect a supported local protocol, then retain the selected adapter."""

    def __init__(self, host: str, port: int, logger_sn: int) -> None:
        self.host = host
        self.port = port
        self.logger_sn = logger_sn
        self._client: TsunProtocolClient | None = None
        self._failed_trace: deque[dict[str, Any]] = deque(maxlen=24)

    @property
    def model(self) -> str:
        """Return the detected model family."""
        return self._client.model if self._client is not None else "Automatic detection"

    @property
    def protocol_name(self) -> str:
        """Return the detected protocol or auto before the first successful read."""
        return (
            self._client.protocol_name
            if self._client is not None
            else DEFAULT_PROTOCOL
        )

    @property
    def measurement_keys(self) -> frozenset[str]:
        """Return keys supported by the detected adapter."""
        return (
            self._client.measurement_keys
            if self._client is not None
            else frozenset()
        )

    @property
    def pv_count(self) -> int:
        """Return the PV count reported by the detected adapter."""
        return self._client.pv_count if self._client is not None else 0

    @property
    def diagnostic_trace(self) -> tuple[dict[str, Any], ...]:
        """Return failed detection attempts and the selected adapter trace."""
        events = list(self._failed_trace)
        if self._client is not None:
            events.extend(self._client.diagnostic_trace)
        return tuple(events[-24:])

    async def async_read_all(self) -> TsunReadResult:
        """Detect the protocol once, then delegate subsequent polls."""
        if self._client is not None:
            return await self._client.async_read_all()

        last_error: Exception | None = None
        for protocol_name in SUPPORTED_PROTOCOLS:
            candidate = _create_specific_client(
                protocol_name, self.host, self.port, self.logger_sn
            )
            _LOGGER.debug("Automatic protocol detection: trying %s", protocol_name)
            try:
                result = await candidate.async_read_all()
            except Exception as err:  # Detection intentionally tries the next adapter.
                last_error = err
                self._failed_trace.extend(candidate.diagnostic_trace)
                _LOGGER.debug(
                    "Automatic protocol detection: %s failed with %s",
                    protocol_name,
                    type(err).__name__,
                )
                continue
            self._client = candidate
            _LOGGER.debug(
                "Automatic protocol detection: selected %s", protocol_name
            )
            return result

        raise RuntimeError("No supported TSUN local protocol detected") from last_error


def create_protocol_client(
    protocol_name: str,
    host: str,
    port: int,
    logger_sn: int,
) -> TsunProtocolClient:
    """Create an automatic or explicit local-protocol adapter."""
    if protocol_name == DEFAULT_PROTOCOL:
        return TsunAutoClient(host, port, logger_sn)
    return _create_specific_client(protocol_name, host, port, logger_sn)
