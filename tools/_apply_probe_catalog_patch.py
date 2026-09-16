#!/usr/bin/env python3
"""Temporary branch-local patch helper for the diagnostic probe-catalog change."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DUMP = ROOT / "tools" / "tsun_dump.py"
TEST = ROOT / "tests" / "test_tsun_dump_tool.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, got {count}")
    return text.replace(old, new, 1)


source = DUMP.read_text(encoding="utf-8")
source = replace_once(source, 'TOOL_VERSION = "2.8.6"', 'TOOL_VERSION = "2.9.0"', "tool version")

source = replace_once(
    source,
    'SUPPORTED_PROTOCOLS = (*VALIDATED_PROTOCOLS, *EXPERIMENTAL_PROTOCOLS)\n',
    '''SUPPORTED_PROTOCOLS = (*VALIDATED_PROTOCOLS, *EXPERIMENTAL_PROTOCOLS)\n\n# Probe catalogs are deliberately capability-based.  Public diagnostics expose\n# protocol/framing names only, never the names of third-party implementations.\nRESEARCH_PROBE_TIMEOUT_CAP = 2.0\nRESEARCH_PROBE_DELAY = 0.12\nRESEARCH_PASSIVE_WAIT = 0.25\nV5_COMMAND_RESPONSE_CONTROLS = (0x1510, 0x0510)\nLOCAL_PROBE_CATALOG: tuple[dict[str, Any], ...] = (\n    {\n        "id": "local_1511_min",\n        "maturity": "validated",\n        "protocol": "1511",\n        "envelope": "solarman_v5",\n        "kind": "native_1511",\n        "sensor_list": 0x0000,\n        "address_tag": 0xA1,\n        "native_function": 0x01,\n        "start": 0x0BB8,\n        "count": 1,\n        "sequence_mode": "legacy_zero",\n    },\n    {\n        "id": "local_02b0_min",\n        "maturity": "validated",\n        "protocol": "02b0",\n        "envelope": "solarman_v5",\n        "kind": "modbus_rtu",\n        "function": 0x03,\n        "sensor_list": 0x02B0,\n        "start": 0x3000,\n        "count": 1,\n        "sequence_mode": "legacy_zero",\n    },\n    {\n        "id": "local_1097_min",\n        "maturity": "validated",\n        "protocol": "1097",\n        "envelope": "solarman_v5",\n        "kind": "modbus_rtu",\n        "function": 0x03,\n        "sensor_list": 0x1097,\n        "start": 0x1100,\n        "count": 1,\n        "sequence_mode": "legacy_zero",\n    },\n    {\n        "id": "local_3026_min",\n        "maturity": "experimental",\n        "protocol": "3026",\n        "envelope": "solarman_v5",\n        "kind": "modbus_rtu",\n        "function": 0x03,\n        "sensor_list": 0x3026,\n        "start": 0x0000,\n        "count": 1,\n        "sequence_mode": "legacy_zero",\n    },\n)\n\n# Broader read-only fingerprints are attempted only after the validated/local\n# path failed.  They intentionally reproduce known protocol transactions rather\n# than associating a probe with a product, project or integration name.\nRESEARCH_PROBE_CATALOG: tuple[dict[str, Any], ...] = (\n    {\n        "id": "v5_02b0_full",\n        "maturity": "research",\n        "protocol": "02b0",\n        "envelope": "solarman_v5",\n        "kind": "modbus_rtu",\n        "function": 0x03,\n        "sensor_list": 0x02B0,\n        "start": 0x3000,\n        "count": 48,\n        "sequence_mode": "adaptive",\n    },\n    {\n        "id": "v5_1097_identity",\n        "maturity": "research",\n        "protocol": "1097",\n        "envelope": "solarman_v5",\n        "kind": "modbus_rtu",\n        "function": 0x03,\n        "sensor_list": 0x1097,\n        "start": 0x1000,\n        "count": 16,\n        "sequence_mode": "adaptive",\n    },\n    {\n        "id": "v5_3026_full",\n        "maturity": "research",\n        "protocol": "3026",\n        "envelope": "solarman_v5",\n        "kind": "modbus_rtu",\n        "function": 0x03,\n        "sensor_list": 0x3026,\n        "start": 0x0000,\n        "count": 45,\n        "sequence_mode": "adaptive",\n    },\n    {\n        "id": "v5_1511_full",\n        "maturity": "research",\n        "protocol": "1511",\n        "envelope": "solarman_v5",\n        "kind": "native_1511",\n        "sensor_list": 0x1511,\n        "address_tag": 0xA1,\n        "native_function": 0x01,\n        "start": 0x0BB8,\n        "count": 32,\n        "sequence_mode": "adaptive",\n    },\n)\n\n# Extra probes are useful for difficult full captures but are not part of the\n# automatic minimal fallback.  Only Modbus read functions are allowed.\nRESEARCH_EXTENDED_PROBE_CATALOG: tuple[dict[str, Any], ...] = (\n    {\n        "id": "v5_02b0_fc04_min",\n        "maturity": "research",\n        "protocol": "02b0",\n        "envelope": "solarman_v5",\n        "kind": "modbus_rtu",\n        "function": 0x04,\n        "sensor_list": 0x02B0,\n        "start": 0x3000,\n        "count": 1,\n        "sequence_mode": "adaptive",\n    },\n    {\n        "id": "v5_1097_fc04_min",\n        "maturity": "research",\n        "protocol": "1097",\n        "envelope": "solarman_v5",\n        "kind": "modbus_rtu",\n        "function": 0x04,\n        "sensor_list": 0x1097,\n        "start": 0x1100,\n        "count": 1,\n        "sequence_mode": "adaptive",\n    },\n)\n''',
    "probe catalog constants",
)

source = replace_once(
    source,
    '''def build_ap_frame(logger_sn: int, payload: bytes, sensor_list: int = 0) -> bytes:\n    if logger_sn != 0 and not _valid_monitor_sn(logger_sn):\n        raise ValueError("Monitor SN must fit the four-byte logger field")\n    if not 0 <= sensor_list <= 0xFFFF:\n        raise ValueError("sensor_list must fit the two-byte AP field")\n    data = b"\\x02" + sensor_list.to_bytes(2, "little") + bytes(12) + payload\n    scope = (\n        len(data).to_bytes(2, "little")\n        + b"\\x10\\x45\\x00\\x00"\n        + logger_sn.to_bytes(4, "little")\n        + data\n    )\n    return b"\\xA5" + scope + bytes((checksum_ap(scope), 0x15))\n''',
    '''def build_ap_frame(\n    logger_sn: int,\n    payload: bytes,\n    sensor_list: int = 0,\n    *,\n    sequence: int = 0,\n) -> bytes:\n    if logger_sn != 0 and not _valid_monitor_sn(logger_sn):\n        raise ValueError("Monitor SN must fit the four-byte logger field")\n    if not 0 <= sensor_list <= 0xFFFF:\n        raise ValueError("sensor_list must fit the two-byte AP field")\n    if not 0 <= sequence <= 0xFFFF:\n        raise ValueError("sequence must fit the two-byte AP field")\n    data = b"\\x02" + sensor_list.to_bytes(2, "little") + bytes(12) + payload\n    scope = (\n        len(data).to_bytes(2, "little")\n        + b"\\x10\\x45"\n        + sequence.to_bytes(2, "little")\n        + logger_sn.to_bytes(4, "little")\n        + data\n    )\n    return b"\\xA5" + scope + bytes((checksum_ap(scope), 0x15))\n''',
    "AP sequence support",
)

source = replace_once(
    source,
    '''def build_modbus_request(start: int, end: int) -> bytes:\n    """Build an FC03 Modbus RTU read request."""\n    count = end - start + 1\n    body = b"\\x01\\x03" + start.to_bytes(2, "big") + count.to_bytes(2, "big")\n    return body + crc16_modbus(body)\n''',
    '''def build_modbus_request(start: int, end: int) -> bytes:\n    """Build an FC03 Modbus RTU read request."""\n    count = end - start + 1\n    body = b"\\x01\\x03" + start.to_bytes(2, "big") + count.to_bytes(2, "big")\n    return body + crc16_modbus(body)\n\n\ndef build_modbus_read_request(\n    start: int, end: int, *, function: int = 0x03\n) -> bytes:\n    """Build a strictly read-only Modbus RTU FC03/FC04 request."""\n    if function not in (0x03, 0x04):\n        raise ValueError("Only read-only Modbus functions 0x03 and 0x04 are allowed")\n    if not 0 <= start <= end <= 0xFFFF:\n        raise ValueError("Invalid Modbus register range")\n    count = end - start + 1\n    if not 1 <= count <= 125:\n        raise ValueError("Modbus read count must be between 1 and 125 registers")\n    body = b"\\x01" + bytes((function,)) + start.to_bytes(2, "big")\n    body += count.to_bytes(2, "big")\n    return body + crc16_modbus(body)\n''',
    "generic read-only Modbus builder",
)

research_code = r'''

@dataclass(slots=True)
class _V5SequenceState:
    """Sequence state used by a direct Solarman V5 client session."""

    receive_index: int = 0
    send_index: int = 0

    def next_send(self) -> int:
        self.send_index = (self.send_index + 1) & 0xFF
        return (self.receive_index << 8) | self.send_index

    def observe(self, value: int) -> None:
        self.receive_index = (value >> 8) & 0xFF
        self.send_index = value & 0xFF


def _probe_descriptor(probe: dict[str, Any]) -> dict[str, Any]:
    """Return a stable, privacy-safe catalog descriptor for reports/tests."""
    result: dict[str, Any] = {
        "id": str(probe["id"]),
        "maturity": str(probe["maturity"]),
        "protocol": str(probe["protocol"]),
        "envelope": str(probe["envelope"]),
        "kind": str(probe["kind"]),
        "sequence_mode": str(probe.get("sequence_mode", "n/a")),
        "read_only": True,
    }
    if "sensor_list" in probe:
        result["sensor_list"] = f"0x{int(probe['sensor_list']):04X}"
    if "function" in probe:
        result["function"] = f"0x{int(probe['function']):02X}"
    if "start" in probe:
        result["start"] = f"0x{int(probe['start']):04X}"
    if "count" in probe:
        result["count"] = int(probe["count"])
    return result


def diagnostic_probe_catalogs(*, full: bool) -> dict[str, list[dict[str, Any]]]:
    """Expose the capability catalogs without implementation provenance names."""
    research = [*RESEARCH_PROBE_CATALOG]
    if full:
        research.extend(RESEARCH_EXTENDED_PROBE_CATALOG)
    return {
        "local": [_probe_descriptor(item) for item in LOCAL_PROBE_CATALOG],
        "research": [_probe_descriptor(item) for item in research],
    }


def _order_research_probes(
    requested: str, hint: str | None, *, full: bool
) -> list[dict[str, Any]]:
    probes = [dict(item) for item in RESEARCH_PROBE_CATALOG]
    if full:
        probes.extend(dict(item) for item in RESEARCH_EXTENDED_PROBE_CATALOG)
    if requested != "auto":
        probes = [item for item in probes if item["protocol"] == requested]
    elif hint in SUPPORTED_PROTOCOLS:
        probes.sort(key=lambda item: item["protocol"] != hint)
    return probes


def _build_catalog_payload(probe: dict[str, Any]) -> bytes:
    start = int(probe["start"])
    end = start + int(probe["count"]) - 1
    if probe["kind"] == "modbus_rtu":
        return build_modbus_read_request(
            start, end, function=int(probe.get("function", 0x03))
        )
    if probe["kind"] == "native_1511":
        return build_1511_request(
            int(probe.get("address_tag", 0xA1)),
            int(probe.get("native_function", 0x01)),
            start,
            end,
        )
    raise ValueError(f"Unsupported read-only probe kind: {probe['kind']}")


def _summarize_v5_frame(frame: bytes) -> dict[str, Any]:
    """Summarize a V5 envelope without retaining logger identity bytes."""
    try:
        _validate_ap_frame(frame)
    except Exception as err:
        return {"valid": False, "error": safe_error_details(err)}
    control = int.from_bytes(frame[3:5], "little")
    sequence = int.from_bytes(frame[5:7], "little")
    return {
        "valid": True,
        "control": f"0x{control:04X}",
        "control_is_command_response": control in V5_COMMAND_RESPONSE_CONTROLS,
        "sequence": sequence,
        "frame_type": frame[11] if len(frame) > 11 else None,
        "status": frame[12] if len(frame) > 12 else None,
        "payload_bytes": max(0, len(frame) - 27),
        "logger_identity_stored": False,
    }


def _classify_catalog_payload(
    probe: dict[str, Any], response_payload: bytes
) -> dict[str, Any]:
    """Classify one embedded response while keeping unknown payloads raw-free."""
    if response_payload in SHORT_LOGGER_MARKERS:
        return {
            "result": "short_marker_only",
            "marker": response_payload.hex(" ").upper(),
            "valid_data": False,
        }
    start = int(probe["start"])
    count = int(probe["count"])
    end = start + count - 1
    if probe["kind"] == "modbus_rtu":
        function = int(probe.get("function", 0x03))
        if len(response_payload) < 5 or response_payload[0] != 0x01:
            return {"result": "non_modbus_payload", "valid_data": False}
        if crc16_modbus(response_payload[:-2]) != response_payload[-2:]:
            return {"result": "invalid_modbus_crc", "valid_data": False}
        response_function = response_payload[1]
        if response_function == (function | 0x80):
            return {
                "result": "modbus_exception",
                "function": f"0x{response_function:02X}",
                "exception_code": response_payload[2],
                "valid_data": False,
                "transport_valid": True,
            }
        if response_function != function:
            return {
                "result": "unexpected_modbus_function",
                "function": f"0x{response_function:02X}",
                "valid_data": False,
            }
        data_length = response_payload[2]
        expected = count * 2
        valid_length = (
            data_length == expected
            and len(response_payload) == 3 + data_length + 2
        )
        return {
            "result": "valid_read_response" if valid_length else "unexpected_modbus_length",
            "function": f"0x{response_function:02X}",
            "register_count": count if valid_length else None,
            "valid_data": valid_length,
            "transport_valid": True,
        }
    if probe["kind"] == "native_1511":
        try:
            registers = parse_1511_response(
                response_payload,
                int(probe.get("address_tag", 0xA1)),
                int(probe.get("native_function", 0x01)),
                start,
                end,
            )
        except Exception as err:
            return {
                "result": "invalid_native_response",
                "error": safe_error_details(err),
                "valid_data": False,
            }
        return {
            "result": "valid_read_response",
            "register_count": len(registers),
            "valid_data": True,
            "transport_valid": True,
        }
    return {"result": "unsupported_probe_kind", "valid_data": False}


def _build_solarman_v4_read_request(logger_sn: int) -> bytes:
    """Build the historical V4 command 0x0001 (read inverter data)."""
    if not _valid_monitor_sn(logger_sn):
        raise ValueError("Monitor SN must fit the four-byte logger field")
    serial = logger_sn.to_bytes(4, "little")
    body = b"\x02\x41\xB1" + serial + serial + b"\x01\x00"
    return b"\x68" + body + bytes((sum(body) & 0xFF, 0x16))


def _recv_v4_bounded(sock: socket.socket, timeout: float) -> bytes:
    data = bytearray()
    deadline = time.monotonic() + timeout
    while len(data) < 8192 and (remaining := deadline - time.monotonic()) > 0:
        sock.settimeout(min(remaining, 0.35 if data else remaining))
        try:
            chunk = sock.recv(min(2048, 8192 - len(data)))
        except socket.timeout:
            break
        if not chunk:
            break
        data.extend(chunk)
    return bytes(data)


def _run_v4_read_probe(
    host: str, port: int, sn: int, timeout: float
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "attempted": True,
        "id": "v4_read_inverter_data",
        "envelope": "solarman_v4",
        "command": "0x0001",
        "read_only": True,
    }
    try:
        request = _build_solarman_v4_read_request(sn)
        with socket.create_connection((host, port), timeout=timeout) as sock:
            sock.settimeout(timeout)
            sock.sendall(request)
            response = _recv_v4_bounded(sock, timeout)
    except Exception as err:
        result["result"] = "transport_error"
        result["error"] = safe_error_details(err)
        return result
    result["response_bytes"] = len(response)
    if not response:
        result["result"] = "no_response"
        return result
    result["looks_like_v4"] = response[:1] == b"\x68" and response[-1:] == b"\x16"
    result["result"] = "v4_response" if result["looks_like_v4"] else "unknown_response"
    result["raw_response_stored"] = False
    return result


def run_research_probe_catalog(
    host: str,
    port: int,
    sn: int,
    timeout: float,
    *,
    requested: str = "auto",
    hint: str | None = None,
    full: bool = False,
) -> dict[str, Any]:
    """Run the additive read-only fallback after the local catalog failed.

    The existing zero-sequence detection path is deliberately untouched.  This
    fallback uses a single V5 session, adaptive sequence state and known bounded
    read transactions, stopping as soon as a strong candidate is found.
    """
    probes = _order_research_probes(requested, hint, full=full)
    probe_timeout = min(timeout, RESEARCH_PROBE_TIMEOUT_CAP)
    result: dict[str, Any] = {
        "attempted": bool(probes),
        "read_only": True,
        "strategy": "adaptive_v5_after_local_failure",
        "catalogs": diagnostic_probe_catalogs(full=full),
        "attempts": [],
        "passive_observation": {"attempted": False},
        "v5_transport_detected": False,
        "candidate_protocol": None,
        "matched_probe": None,
        "confidence": "none",
        "safety": {
            "configuration_write_performed": False,
            "inverter_write_performed": False,
            "cloud_access_performed": False,
            "allowed_modbus_functions": ["0x03", "0x04"],
            "same_connection": True,
            "stops_on_valid_read": True,
        },
    }
    if not probes:
        result["reason"] = "no research probe matches the requested protocol"
        return result

    sequence = _V5SequenceState()
    try:
        with socket.create_connection((host, port), timeout=probe_timeout) as sock:
            sock.settimeout(probe_timeout)
            result["passive_observation"] = {
                "attempted": True,
                "wait_seconds": RESEARCH_PASSIVE_WAIT,
                "received": False,
            }
            ready, _, _ = select.select([sock], [], [], RESEARCH_PASSIVE_WAIT)
            if ready:
                try:
                    passive_frame = read_ap_frame(sock)
                    summary = _summarize_v5_frame(passive_frame)
                    result["passive_observation"].update(
                        {"received": True, "frame": summary}
                    )
                    if summary.get("valid") and isinstance(summary.get("sequence"), int):
                        sequence.observe(int(summary["sequence"]))
                    if summary.get("control_is_command_response"):
                        result["v5_transport_detected"] = True
                except Exception as err:
                    result["passive_observation"].update(
                        {"received": True, "error": safe_error_details(err)}
                    )

            for probe in probes:
                payload = _build_catalog_payload(probe)
                sequence_value = sequence.next_send()
                request = build_ap_frame(
                    sn,
                    payload,
                    sensor_list=int(probe.get("sensor_list", 0)),
                    sequence=sequence_value,
                )
                attempt: dict[str, Any] = {
                    **_probe_descriptor(probe),
                    "sequence_sent": sequence_value,
                    "result": "pending",
                }
                if full:
                    attempt["request_payload"] = payload.hex(" ").upper()
                started = time.monotonic()
                try:
                    sock.settimeout(probe_timeout)
                    sock.sendall(request)
                    frame = read_ap_frame(sock)
                except (socket.timeout, TimeoutError):
                    attempt["result"] = "timeout"
                    attempt["latency_ms"] = round(
                        (time.monotonic() - started) * 1000, 1
                    )
                    result["attempts"].append(attempt)
                    time.sleep(RESEARCH_PROBE_DELAY)
                    continue
                except Exception as err:
                    attempt["result"] = "transport_error"
                    attempt["error"] = safe_error_details(err)
                    attempt["latency_ms"] = round(
                        (time.monotonic() - started) * 1000, 1
                    )
                    result["attempts"].append(attempt)
                    break

                attempt["latency_ms"] = round(
                    (time.monotonic() - started) * 1000, 1
                )
                summary = _summarize_v5_frame(frame)
                attempt["frame"] = summary
                if summary.get("valid") and isinstance(summary.get("sequence"), int):
                    sequence.observe(int(summary["sequence"]))
                if summary.get("control_is_command_response"):
                    result["v5_transport_detected"] = True
                try:
                    response_payload = parse_ap_frame(frame)
                except Exception as err:
                    attempt["result"] = "invalid_v5_response"
                    attempt["error"] = safe_error_details(err)
                    result["attempts"].append(attempt)
                    time.sleep(RESEARCH_PROBE_DELAY)
                    continue

                classification = _classify_catalog_payload(probe, response_payload)
                attempt["classification"] = classification
                attempt["result"] = str(classification["result"])

                # Some loggers first return a two-byte marker and then the real
                # read response on the same connection.  Keep that behavior
                # bounded and read-only rather than declaring a false failure.
                if response_payload in SHORT_LOGGER_MARKERS:
                    try:
                        sock.settimeout(min(probe_timeout, CHARACTERIZATION_MARKER_WAIT))
                        followup_frame = read_ap_frame(sock)
                        followup_summary = _summarize_v5_frame(followup_frame)
                        attempt["followup_frame"] = followup_summary
                        if (
                            followup_summary.get("valid")
                            and isinstance(followup_summary.get("sequence"), int)
                        ):
                            sequence.observe(int(followup_summary["sequence"]))
                        followup_payload = parse_ap_frame(followup_frame)
                        followup = _classify_catalog_payload(probe, followup_payload)
                        attempt["followup_classification"] = followup
                        if followup.get("valid_data"):
                            classification = followup
                            attempt["result"] = "valid_read_response_after_short_marker"
                    except (socket.timeout, TimeoutError):
                        attempt["followup"] = "none_before_timeout"
                    except Exception as err:
                        attempt["followup"] = "invalid"
                        attempt["followup_error"] = safe_error_details(err)

                result["attempts"].append(attempt)
                if classification.get("valid_data"):
                    result["candidate_protocol"] = str(probe["protocol"])
                    result["matched_probe"] = str(probe["id"])
                    result["confidence"] = "valid_read_response"
                    break
                time.sleep(RESEARCH_PROBE_DELAY)
    except Exception as err:
        result["session_error"] = safe_error_details(err)

    if result["candidate_protocol"] is None and result["v5_transport_detected"]:
        result["confidence"] = "v5_transport_only"

    # The historical V4 read is deliberately a full-capture fallback only, and
    # is skipped as soon as V5 transport has been established.
    result["v4_read_probe"] = (
        _run_v4_read_probe(host, port, sn, probe_timeout)
        if full
        and result["candidate_protocol"] is None
        and not result["v5_transport_detected"]
        else {
            "attempted": False,
            "read_only": True,
            "reason": "not needed" if full else "requires --full",
        }
    )
    return result
'''

source = replace_once(
    source,
    '''    raise ProtocolDetectionError(\n        "No supported TSUN local protocol detected after "\n        f"{PROTOCOL_PROBE_RETRIES} attempts per protocol",\n        attempts,\n    ) from last_error\n\n\ndef register_key(protocol: str, block: tuple, address: int) -> str:\n''',
    '''    raise ProtocolDetectionError(\n        "No supported TSUN local protocol detected after "\n        f"{PROTOCOL_PROBE_RETRIES} attempts per protocol",\n        attempts,\n    ) from last_error\n''' + research_code + '''\n\ndef register_key(protocol: str, block: tuple, address: int) -> str:\n''',
    "research engine insertion",
)

source = replace_once(
    source,
    '''    raw_observations = (\n        _capture_failed_protocol_observations(host, args.port, sn, args.timeout)\n        if full\n        else []\n    )\n    try:\n''',
    '''    raw_observations = (\n        _capture_failed_protocol_observations(host, args.port, sn, args.timeout)\n        if full\n        else []\n    )\n    research_detection = run_research_probe_catalog(\n        host,\n        args.port,\n        sn,\n        args.timeout,\n        requested=args.protocol,\n        hint=discovery.get("protocol_hint"),\n        full=full,\n    )\n    try:\n''',
    "failure fallback invocation",
)

source = replace_once(
    source,
    '''        "protocol_characterization": {\n            "attempted": False,\n            "reason": "no supported protocol selected",\n        },\n        "discovery": discovery,\n''',
    '''        "protocol_characterization": {\n            "attempted": False,\n            "reason": "no supported protocol selected",\n        },\n        "research_detection": research_detection,\n        "discovery": discovery,\n''',
    "failure report research section",
)

DUMP.write_text(source, encoding="utf-8")

tests = TEST.read_text(encoding="utf-8")
tests = replace_once(
    tests,
    'self.assertEqual(TOOL.TOOL_VERSION, "2.8.6")',
    'self.assertEqual(TOOL.TOOL_VERSION, "2.9.0")',
    "test version",
)

new_tests = r'''
    def test_ap_frame_default_sequence_remains_legacy_zero(self) -> None:
        frame = TOOL.build_ap_frame(123456789, b"\x01\x03\x00\x00", sensor_list=0x02B0)
        self.assertEqual(frame[5:7], b"\x00\x00")

    def test_ap_frame_supports_explicit_v5_sequence(self) -> None:
        frame = TOOL.build_ap_frame(
            123456789,
            b"\x01\x03\x00\x00",
            sensor_list=0x3026,
            sequence=1,
        )
        self.assertEqual(frame[5:7], b"\x01\x00")

    def test_v5_sequence_state_starts_at_one_and_tracks_peer(self) -> None:
        sequence = TOOL._V5SequenceState()
        self.assertEqual(sequence.next_send(), 0x0001)
        sequence.observe(0x0101)
        self.assertEqual(sequence.next_send(), 0x0102)

    def test_local_probe_catalog_preserves_existing_detection_transactions(self) -> None:
        probes = {item["protocol"]: item for item in TOOL.LOCAL_PROBE_CATALOG}
        self.assertEqual(probes["1511"]["sequence_mode"], "legacy_zero")
        self.assertEqual((probes["02b0"]["start"], probes["02b0"]["count"]), (0x3000, 1))
        self.assertEqual((probes["1097"]["start"], probes["1097"]["count"]), (0x1100, 1))
        self.assertEqual((probes["3026"]["start"], probes["3026"]["count"]), (0x0000, 1))

    def test_research_catalog_contains_exact_bounded_v5_fingerprints(self) -> None:
        probes = {item["id"]: item for item in TOOL.RESEARCH_PROBE_CATALOG}
        self.assertEqual(
            (probes["v5_02b0_full"]["sensor_list"], probes["v5_02b0_full"]["start"], probes["v5_02b0_full"]["count"]),
            (0x02B0, 0x3000, 48),
        )
        self.assertEqual(
            (probes["v5_1097_identity"]["sensor_list"], probes["v5_1097_identity"]["start"], probes["v5_1097_identity"]["count"]),
            (0x1097, 0x1000, 16),
        )
        self.assertEqual(
            (probes["v5_3026_full"]["sensor_list"], probes["v5_3026_full"]["start"], probes["v5_3026_full"]["count"]),
            (0x3026, 0x0000, 45),
        )

    def test_every_catalog_probe_is_strictly_read_only(self) -> None:
        for probe in (
            *TOOL.LOCAL_PROBE_CATALOG,
            *TOOL.RESEARCH_PROBE_CATALOG,
            *TOOL.RESEARCH_EXTENDED_PROBE_CATALOG,
        ):
            if probe["kind"] == "modbus_rtu":
                self.assertIn(probe["function"], (0x03, 0x04))
            else:
                self.assertEqual(probe["kind"], "native_1511")
        manifest = TOOL.diagnostic_probe_catalogs(full=True)
        self.assertTrue(all(item["read_only"] for group in manifest.values() for item in group))

    def test_user_facing_probe_catalog_has_no_implementation_names(self) -> None:
        rendered = repr(TOOL.diagnostic_probe_catalogs(full=True)).lower()
        self.assertNotIn("proxy", rendered)
        self.assertNotIn("hacs", rendered)
        self.assertIn("solarman_v5", rendered)

    def test_modbus_research_builder_rejects_write_functions(self) -> None:
        with self.assertRaises(ValueError):
            TOOL.build_modbus_read_request(0x0000, 0x0000, function=0x06)
'''

tests = replace_once(
    tests,
    '\n\nif __name__ == "__main__":\n    unittest.main()\n',
    '\n' + new_tests + '\n\nif __name__ == "__main__":\n    unittest.main()\n',
    "catalog tests insertion",
)
TEST.write_text(tests, encoding="utf-8")
print("Applied diagnostic probe catalog patch")
