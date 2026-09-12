# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Common protocol interfaces for TSUN Local."""

from __future__ import annotations

import asyncio
import base64
from collections import deque
from dataclasses import dataclass
import logging
import re
from typing import Any, Protocol

DEFAULT_PROTOCOL = "auto"
FORCE_PROTOCOL = "force_probe"
SUPPORTED_PROTOCOLS = ("1511", "1097", "02b0")
DETECTION_MIN_SCORE = 80
DETECTION_MIN_MARGIN = 20

_LOGGER = logging.getLogger(__name__)

_FIRMWARE_STATUS_PATHS = ("/status.html", "/index_cn.html", "/index.html", "/")
_FIRMWARE_HTTP_TIMEOUT = 1.5
_FIRMWARE_PAGE_LIMIT = 256 * 1024
_FIRMWARE_VALUE_PATTERNS = (
    re.compile(
        r"\b(?:webdata|cover)[_-]ver\s*[:=]\s*[\"']"
        r"([A-Za-z0-9][A-Za-z0-9._-]{1,79})",
        re.IGNORECASE,
    ),
    re.compile(
        r"firmware\s*version[^A-Za-z0-9]+"
        r"([A-Za-z0-9][A-Za-z0-9._-]{1,79})",
        re.IGNORECASE,
    ),
)
_FIRMWARE_PROTOCOL_TOKEN = re.compile(
    r"(?:^|[_-])(1511|1097|02b0)(?=[_-]|$)",
    re.IGNORECASE,
)
_CORE_BLOCKS = {"1511": 3, "1097": 3, "02b0": 2}
_VERSION_KEYS = {
    "1511": ("dsp_firmware_version", "qcpu1_firmware_version", "qcpu2_firmware_version"),
    "1097": ("protocol_version", "inverter_version"),
    "02b0": ("inverter_firmware_version",),
}


def protocol_from_firmware(firmware_version: str | None) -> str | None:
    """Return a supported protocol token embedded in a logger firmware name."""
    if not firmware_version:
        return None
    match = _FIRMWARE_PROTOCOL_TOKEN.search(firmware_version)
    if match is None:
        return None
    protocol_name = match.group(1).lower()
    return protocol_name if protocol_name in SUPPORTED_PROTOCOLS else None


def _firmware_version_from_document(document: str) -> str | None:
    """Extract a firmware version from a local logger status document."""
    for pattern in _FIRMWARE_VALUE_PATTERNS:
        if match := pattern.search(document):
            return match.group(1)
    return None


async def _async_read_firmware_document(
    host: str, path: str, *, authenticated: bool
) -> str | None:
    """Read one small local HTTP page without sending configuration data."""
    writer: asyncio.StreamWriter | None = None
    try:
        async with asyncio.timeout(_FIRMWARE_HTTP_TIMEOUT):
            reader, writer = await asyncio.open_connection(host, 80)
            headers = [
                f"GET {path} HTTP/1.1",
                f"Host: {host}",
                "Connection: close",
                "User-Agent: TSUN-Local",
            ]
            if authenticated:
                token = base64.b64encode(b"admin:admin").decode("ascii")
                headers.append(f"Authorization: Basic {token}")
            request = ("\r\n".join(headers) + "\r\n\r\n").encode("ascii")
            writer.write(request)
            await writer.drain()
            response = await reader.read(_FIRMWARE_PAGE_LIMIT + 1)
    except (OSError, TimeoutError, asyncio.IncompleteReadError):
        return None
    finally:
        if writer is not None:
            writer.close()
            try:
                await writer.wait_closed()
            except OSError:
                pass

    if len(response) > _FIRMWARE_PAGE_LIMIT:
        return None
    header, separator, body = response.partition(b"\r\n\r\n")
    if not separator:
        return None
    status_line = header.split(b"\r\n", 1)[0]
    if b" 200 " not in status_line:
        return None
    return body.decode("utf-8", errors="replace")


async def async_detect_protocol_from_firmware(host: str) -> str | None:
    """Best-effort read-only protocol hint from the logger firmware name."""
    for path in _FIRMWARE_STATUS_PATHS:
        for authenticated in (False, True):
            document = await _async_read_firmware_document(
                host, path, authenticated=authenticated
            )
            if document is None:
                continue
            firmware_version = _firmware_version_from_document(document)
            if protocol_name := protocol_from_firmware(firmware_version):
                return protocol_name
    return None


@dataclass(frozen=True, slots=True)
class TsunReadResult:
    """Measurements and diagnostics returned by one complete device poll."""

    measurements: dict[str, float | int | str]
    duration_ms: int
    blocks_ok: int


@dataclass(frozen=True, slots=True)
class ProtocolDetectionAssessment:
    """Conservative confidence assessment for one successful protocol read."""

    protocol_name: str
    score: int
    hard_valid: bool
    reasons: tuple[str, ...]


def _numeric(measurements: dict[str, float | int | str], key: str) -> float | None:
    value = measurements.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _has_version_signature(protocol_name: str, measurements: dict[str, float | int | str]) -> bool:
    for key in _VERSION_KEYS[protocol_name]:
        value = measurements.get(key)
        if not isinstance(value, str):
            continue
        normalized = value.strip().upper()
        if not normalized or normalized in {"0", "V0.0.00", "V0.0.0"}:
            continue
        if "15.15" in normalized and normalized.endswith("F"):
            continue
        return True
    return False


def score_protocol_candidate(
    protocol_name: str,
    result: TsunReadResult,
) -> ProtocolDetectionAssessment:
    """Score one already validated read without relying on solar production.

    Transport/framing validation is performed by each protocol adapter before
    this function is called. Here we add protocol-independent plausibility and
    family-signature checks. Zero production is neutral so night-time setup is
    supported.
    """
    if protocol_name not in SUPPORTED_PROTOCOLS:
        return ProtocolDetectionAssessment(protocol_name, 0, False, ("unsupported",))

    measurements = result.measurements
    reasons: list[str] = []
    required_blocks = _CORE_BLOCKS[protocol_name]
    if result.blocks_ok < required_blocks:
        return ProtocolDetectionAssessment(
            protocol_name,
            0,
            False,
            (f"insufficient_blocks:{result.blocks_ok}/{required_blocks}",),
        )

    plausibility_ranges = {
        "ac_voltage": (70.0, 300.0),
        "ac_frequency": (40.0, 70.0),
        "inverter_temperature": (-50.0, 150.0),
        "ambient_temperature": (-50.0, 150.0),
    }
    for key, (minimum, maximum) in plausibility_ranges.items():
        value = _numeric(measurements, key)
        if value is None or value == 0:
            continue
        if not minimum <= value <= maximum:
            return ProtocolDetectionAssessment(
                protocol_name,
                0,
                False,
                (f"implausible_{key}:{value:g}",),
            )

    for key in ("rated_power", "max_designed_power"):
        value = _numeric(measurements, key)
        if value is None or value == 0:
            continue
        if not 50.0 <= value <= 30000.0:
            return ProtocolDetectionAssessment(
                protocol_name,
                0,
                False,
                (f"implausible_{key}:{value:g}",),
            )

    score = 60
    reasons.extend(("validated_transport", "complete_core_blocks"))

    rated_power = _numeric(measurements, "rated_power")
    if rated_power is not None and 50.0 <= rated_power <= 30000.0:
        score += 10
        reasons.append("rated_power")

    max_power = _numeric(measurements, "max_designed_power")
    if max_power is not None and 50.0 <= max_power <= 30000.0:
        score += 10
        reasons.append("max_designed_power")

    if _has_version_signature(protocol_name, measurements):
        score += 20
        reasons.append("family_version_signature")

    ac_voltage = _numeric(measurements, "ac_voltage")
    if ac_voltage is not None and 70.0 <= ac_voltage <= 300.0:
        score += 5
        reasons.append("plausible_ac_voltage")

    ac_frequency = _numeric(measurements, "ac_frequency")
    if ac_frequency is not None and 40.0 <= ac_frequency <= 70.0:
        score += 5
        reasons.append("plausible_ac_frequency")

    total_energy = _numeric(measurements, "ac_energy_total")
    if total_energy is not None and total_energy > 0:
        score += 5
        reasons.append("nonzero_total_energy")

    return ProtocolDetectionAssessment(
        protocol_name,
        min(score, 100),
        True,
        tuple(reasons),
    )


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


def _ordered_protocols(firmware_protocol: str | None) -> tuple[str, ...]:
    """Return every runtime protocol, using firmware only as first priority."""
    if firmware_protocol not in SUPPORTED_PROTOCOLS:
        return SUPPORTED_PROTOCOLS
    return (firmware_protocol,) + tuple(
        protocol for protocol in SUPPORTED_PROTOCOLS if protocol != firmware_protocol
    )


class TsunAutoClient:
    """Detect a supported local protocol, then retain the selected adapter."""

    def __init__(
        self,
        host: str,
        port: int,
        logger_sn: int,
        *,
        use_firmware_hint: bool = True,
    ) -> None:
        self.host = host
        self.port = port
        self.logger_sn = logger_sn
        self._use_firmware_hint = use_firmware_hint
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
        """Return failed detection attempts, confidence scores and selected trace."""
        events = list(self._failed_trace)
        if self._client is not None:
            events.extend(self._client.diagnostic_trace)
        return tuple(events[-24:])

    def _record_assessment(self, assessment: ProtocolDetectionAssessment) -> None:
        self._failed_trace.append(
            {
                "protocol": assessment.protocol_name,
                "stage": "detection_score",
                "score": assessment.score,
                "hard_valid": assessment.hard_valid,
                "reasons": list(assessment.reasons),
            }
        )

    async def async_read_all(self) -> TsunReadResult:
        """Detect once using hard validation and confidence scoring, then retain it."""
        if self._client is not None:
            return await self._client.async_read_all()

        last_error: Exception | None = None
        firmware_protocol = (
            await async_detect_protocol_from_firmware(self.host)
            if self._use_firmware_hint
            else None
        )
        protocol_names = _ordered_protocols(firmware_protocol)
        if firmware_protocol is not None:
            _LOGGER.debug(
                "Automatic protocol detection: firmware prioritizes %s",
                firmware_protocol,
            )

        candidates: list[
            tuple[ProtocolDetectionAssessment, int, TsunProtocolClient, TsunReadResult]
        ] = []
        for priority, protocol_name in enumerate(protocol_names):
            candidate = _create_specific_client(
                protocol_name, self.host, self.port, self.logger_sn
            )
            _LOGGER.debug("Automatic protocol detection: trying %s", protocol_name)
            try:
                result = await candidate.async_read_all()
            except Exception as err:  # Detection intentionally tries every adapter.
                last_error = err
                self._failed_trace.extend(candidate.diagnostic_trace)
                _LOGGER.debug(
                    "Automatic protocol detection: %s failed with %s",
                    protocol_name,
                    type(err).__name__,
                )
                continue

            assessment = score_protocol_candidate(protocol_name, result)
            self._record_assessment(assessment)
            if assessment.hard_valid:
                candidates.append((assessment, priority, candidate, result))

        eligible = [
            candidate
            for candidate in candidates
            if candidate[0].score >= DETECTION_MIN_SCORE
        ]
        if not eligible:
            raise RuntimeError(
                "No supported TSUN local protocol reached the confidence threshold"
            ) from last_error

        eligible.sort(key=lambda item: (-item[0].score, item[1]))
        best = eligible[0]
        runner_up = max(
            (candidate for candidate in candidates if candidate is not best),
            key=lambda item: item[0].score,
            default=None,
        )
        if (
            runner_up is not None
            and best[0].score - runner_up[0].score < DETECTION_MIN_MARGIN
        ):
            raise RuntimeError(
                "Ambiguous TSUN local protocol detection: confidence margin is too small"
            )

        self._client = best[2]
        _LOGGER.debug(
            "Automatic protocol detection: selected %s with score %d",
            best[0].protocol_name,
            best[0].score,
        )
        return best[3]


def create_protocol_client(
    protocol_name: str,
    host: str,
    port: int,
    logger_sn: int,
) -> TsunProtocolClient:
    """Create an automatic or explicit local-protocol adapter."""
    if protocol_name == DEFAULT_PROTOCOL:
        return TsunAutoClient(host, port, logger_sn)
    if protocol_name == FORCE_PROTOCOL:
        return TsunAutoClient(
            host, port, logger_sn, use_firmware_hint=False
        )
    return _create_specific_client(protocol_name, host, port, logger_sn)
