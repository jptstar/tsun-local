#!/usr/bin/env python3
# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later
"""Bounded read-only follow-up research for changed 1097 logger transport.

Installed after ``tsun_1097_research_probe``. It only enriches reports already
classified as ``1097-research`` with ``legacy_tcp_8899_unavailable``. Normal
1511/02B0/1097/3026/Tuya captures are returned untouched.

The extension is deliberately split into ordered phases:
1. inspect already-fetched static logger configuration;
2. verify the configured legacy TCP listener lifecycle;
3. sample ``/status.html`` repeatedly to validate whether measurements remain
   available through HTTP on GEN4 / firmware 1097 loggers;
4. re-check safe HTTP endpoints and query read-only AT getters;
5. perform bounded UDP/TCP transport research only, without configuration
   changes or Modbus writes.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import errno
import hashlib
import http.client
import ipaddress
import re
import socket
import time
from typing import Any, Iterable

import tsun_1097_research_probe as base

EXTENSION_VERSION = 2
LEGACY_PORT = 8899
HTTP_MEASUREMENT_PATH = "/status.html"
HTTP_SAMPLE_STANDARD_COUNT = 3
HTTP_SAMPLE_FULL_COUNT = 6
HTTP_SAMPLE_STANDARD_INTERVAL = 2.0
HTTP_SAMPLE_FULL_INTERVAL = 3.0

AT_QUERY_CATALOG = (
    ("version", b"AT+VER\r"),
    ("network", b"AT+NETP\r"),
    ("uart", b"AT+UART\r"),
    ("transfer_mode", b"AT+TMODE\r"),
    ("tcp_timeout", b"AT+TCPTO\r"),
    ("uart_frame", b"AT+UARTF\r"),
    ("uart_frame_time", b"AT+UARTFT\r"),
    ("uart_frame_length", b"AT+UARTFL\r"),
    ("max_sockets", b"AT+MAXSK\r"),
    ("tcp_link", b"AT+TCPLK\r"),
)
EXTRA_PORTS = frozenset(
    {
        502,
        1502,
        2000,
        2001,
        4000,
        4001,
        5000,
        5001,
        7000,
        8000,
        8080,
        8888,
        8899,
        9000,
        9001,
        10000,
        10001,
        10443,
        10500,
        48899,
        49999,
    }
)
FULL_RANGES = (
    (1025, 4096),
    (5000, 8192),
    (10000, 11050),
    (20000, 20100),
    (30000, 30100),
)
HTTP_PORTS = frozenset({80, 8000, 8080, 8888})
TLS_PORTS = frozenset({443, 8443, 8883, 9443, 10443})
NO_1097_PROBE = HTTP_PORTS | TLS_PORTS | frozenset(
    {22, 23, 53, 1883, 8883, 48899, 49999}
)
ACTIVE_1097_CANDIDATE_PORTS = frozenset(
    {502, 1502, 2000, 2001, 4000, 4001, 5000, 5001, 7000, 8890, 8898, 9000, 9001, 10000, 10001, 10500}
)
SAFE_HTTP_PATHS = (
    "/status.html",
    "/hide_set_edit.html",
    "/remote.html",
    "/port.html",
    "/select.html",
)
VAR_RE = re.compile(
    r"\bvar\s+(yz_tmode|server_a|server_b|uart_setting_baud|uart_setting_data|"
    r"uart_setting_parity|uart_setting_stop|uart_setting_fc|net_setting_pro|"
    r"net_setting_cs|net_setting_port|net_setting_ip|net_setting_to|inv_set|"
    r"inv_tp|inv_tp_seld)\s*=\s*[\"']([^\"']*)[\"']",
    re.I,
)
STATUS_VAR_RE = re.compile(
    r"\bvar\s+(webdata_msvn|webdata_ssvn|webdata_pv_type|webdata_rate_p|"
    r"webdata_now_p|webdata_today_e|webdata_total_e|webdata_alarm|"
    r"webdata_utime|status_a|status_b|status_c)\s*=\s*[\"']([^\"']*)[\"']",
    re.I,
)
NUMERIC_STATUS_FIELDS = {
    "webdata_rate_p": "rated_power_w",
    "webdata_now_p": "current_power_w",
    "webdata_today_e": "yield_today_kwh",
    "webdata_total_e": "total_yield_kwh",
    "webdata_utime": "last_update_value",
}
TEXT_STATUS_FIELDS = {
    "webdata_msvn": "inverter_firmware_main",
    "webdata_ssvn": "inverter_firmware_slave",
    "webdata_pv_type": "inverter_model",
    "webdata_alarm": "alarm",
}
REMOTE_STATUS_FIELDS = {
    "status_a": "remote_server_a",
    "status_b": "remote_server_b",
    "status_c": "remote_server_c",
}
MEASUREMENT_FIELDS = (
    "rated_power_w",
    "current_power_w",
    "yield_today_kwh",
    "total_yield_kwh",
)


def _target(doc: Any) -> bool:
    meta = doc.get("metadata") if isinstance(doc, dict) else None
    return (
        isinstance(meta, dict)
        and meta.get("detected_protocol") == "1097-research"
        and meta.get("capture_limitation") == "legacy_tcp_8899_unavailable"
    )


def _strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _strings(item)


def _endpoint(raw: str) -> dict[str, Any]:
    parts = [part.strip() for part in raw.split(",")]
    host = parts[1] if len(parts) > 1 else ""
    try:
        port = int(parts[2]) if len(parts) > 2 else None
    except ValueError:
        port = None
    kind = None
    private = None
    if host:
        try:
            parsed = ipaddress.ip_address(host.strip("[]"))
        except ValueError:
            kind = "hostname"
        else:
            kind, private = "ip", bool(parsed.is_private)
    return {
        "configured": bool(raw),
        "host_kind": kind,
        "host_sha256_12": hashlib.sha256(host.lower().encode()).hexdigest()[:12]
        if host
        else None,
        "host_is_private": private,
        "port": port,
        "transport": parts[3].upper() if len(parts) > 3 else None,
        "raw_host_stored": False,
    }


def extract_static_logger_config(logger_web: Any) -> dict[str, Any]:
    found: dict[str, str] = {}
    for text in _strings(logger_web):
        for match in VAR_RE.finditer(text):
            found.setdefault(match.group(1).lower(), match.group(2).strip())

    def integer(key: str) -> int | None:
        try:
            return int(found.get(key, ""))
        except ValueError:
            return None

    ip_summary = None
    raw_ip = found.get("net_setting_ip")
    if raw_ip is not None:
        try:
            parsed = ipaddress.ip_address(raw_ip.strip("[]"))
        except ValueError:
            ip_summary = {
                "present": bool(raw_ip),
                "kind": "non_ip",
                "raw_value_stored": False,
            }
        else:
            ip_summary = {
                "present": True,
                "kind": "ip",
                "private": bool(parsed.is_private),
                "raw_value_stored": False,
            }
    return {
        "attempted": True,
        "source": "already_fetched_logger_web_static_content",
        "variables_found": sorted(found),
        "mode": found.get("yz_tmode"),
        "network": {
            "protocol": found.get("net_setting_pro", "").upper() or None,
            "role": found.get("net_setting_cs", "").upper() or None,
            "port": integer("net_setting_port"),
            "timeout_seconds": integer("net_setting_to"),
            "configured_ip": ip_summary,
        },
        "uart": {
            "baud": integer("uart_setting_baud"),
            "data": found.get("uart_setting_data"),
            "parity": found.get("uart_setting_parity"),
            "stop": found.get("uart_setting_stop"),
            "flow_control": found.get("uart_setting_fc"),
        },
        "inverter_profile": {
            "inv_set": found.get("inv_set"),
            "profile": found.get("inv_tp"),
            "selected": found.get("inv_tp_seld"),
        },
        "remote_a": _endpoint(found.get("server_a", "")),
        "remote_b": _endpoint(found.get("server_b", "")),
        "raw_ip_stored": False,
        "raw_remote_hostname_stored": False,
    }


def _result(code: int) -> str:
    if code == 0:
        return "open"
    if code == errno.ECONNREFUSED:
        return "refused"
    if code in {errno.ETIMEDOUT, getattr(errno, "EWOULDBLOCK", -1)}:
        return "timeout"
    if code in {errno.EHOSTUNREACH, errno.ENETUNREACH}:
        return "unreachable"
    return errno.errorcode.get(code, f"errno_{code}").lower()


def tcp_lifecycle(
    host: str,
    port: int,
    attempts: int,
    timeout: float,
    delay: float,
) -> dict[str, Any]:
    rows = []
    for index in range(max(1, min(attempts, 16))):
        started = time.monotonic()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        code = -1
        banner = None
        try:
            sock.settimeout(min(max(timeout, 0.05), 0.5))
            code = int(sock.connect_ex((host, int(port))))
            if code == 0:
                sock.settimeout(0.20)
                try:
                    payload = sock.recv(512)
                except (socket.timeout, OSError):
                    payload = b""
                if payload:
                    banner = base._fingerprint_payload(payload, base.SAFE_UDP_MARKERS)
                    banner["application_data_sent"] = False
        except OSError as exc:
            code = int(getattr(exc, "errno", -1) or -1)
        finally:
            sock.close()
        rows.append(
            {
                "attempt": index + 1,
                "result": _result(code),
                "errno": code if code >= 0 else None,
                "latency_ms": round((time.monotonic() - started) * 1000, 1),
                "passive_banner": banner,
                "application_data_sent": False,
            }
        )
        if index + 1 < attempts:
            time.sleep(min(max(delay, 0.0), 0.5))
    return {
        "attempted": True,
        "port": int(port),
        "attempt_count": len(rows),
        "open_count": sum(row["result"] == "open" for row in rows),
        "results": rows,
        "application_data_sent": False,
    }


def _http_fetch(host: str, path: str, timeout: float) -> dict[str, Any]:
    """Perform one bounded GET and keep the body only in memory for parsing."""
    conn = http.client.HTTPConnection(host, 80, timeout=min(max(timeout, 0.2), 1.5))
    try:
        conn.request(
            "GET",
            path,
            headers={"User-Agent": "TSUN-Local-Diagnostic/1097-research"},
        )
        response = conn.getresponse()
        body = response.read(65536)
        return {
            "path": path,
            "status": int(response.status),
            "content_type": (response.getheader("Content-Type") or "")[:96],
            "body_length": len(body),
            "body_sha256_12": hashlib.sha256(body).hexdigest()[:12],
            "method": "GET",
            "body": body,
        }
    except (OSError, http.client.HTTPException) as exc:
        return {
            "path": path,
            "error": type(exc).__name__,
            "method": "GET",
            "body": b"",
        }
    finally:
        conn.close()


def _http_get(host: str, path: str, timeout: float) -> dict[str, Any]:
    fetched = _http_fetch(host, path, timeout)
    return {
        key: value
        for key, value in fetched.items()
        if key != "body"
    } | {"body_stored": False}


def _safe_status_text(value: str, limit: int = 120) -> str | None:
    value = re.sub(r"[^A-Za-z0-9_.:+/() -]", "", value.strip())[:limit]
    return value or None


def _status_number(value: str) -> int | float | None:
    cleaned = value.strip().replace(",", ".")
    if not cleaned:
        return None
    try:
        number = float(cleaned)
    except ValueError:
        return None
    if number.is_integer():
        return int(number)
    return number


def parse_status_measurements(body: bytes) -> dict[str, Any]:
    """Extract privacy-safe values from ``status.html`` without storing HTML."""
    text = body.decode("utf-8", errors="replace")
    raw: dict[str, str] = {}
    for match in STATUS_VAR_RE.finditer(text):
        raw.setdefault(match.group(1).lower(), match.group(2).strip())

    values: dict[str, Any] = {}
    for source, target in NUMERIC_STATUS_FIELDS.items():
        values[target] = _status_number(raw.get(source, ""))
    for source, target in TEXT_STATUS_FIELDS.items():
        values[target] = _safe_status_text(raw.get(source, ""))
    for source, target in REMOTE_STATUS_FIELDS.items():
        status = raw.get(source)
        values[target] = (
            "connected" if status == "1" else "not_connected" if status == "0" else None
        )

    variables_found = sorted(raw)
    measurement_fields_seen = sorted(
        target
        for source, target in NUMERIC_STATUS_FIELDS.items()
        if source in raw
    )
    return {
        "variables_found": variables_found,
        "measurement_fields_seen": measurement_fields_seen,
        "values": values,
        "serial_number_stored": False,
        "raw_html_stored": False,
    }


def _distinct_values(samples: list[dict[str, Any]], field: str) -> list[Any]:
    distinct: list[Any] = []
    for sample in samples:
        value = sample.get("values", {}).get(field)
        if value is None:
            continue
        if value not in distinct:
            distinct.append(value)
    return distinct


def sample_http_measurements(
    host: str,
    timeout: float,
    *,
    full: bool,
    sleep_fn: Any = time.sleep,
) -> dict[str, Any]:
    """Repeatedly sample status.html to validate a possible HTTP data transport."""
    count = HTTP_SAMPLE_FULL_COUNT if full else HTTP_SAMPLE_STANDARD_COUNT
    interval = HTTP_SAMPLE_FULL_INTERVAL if full else HTTP_SAMPLE_STANDARD_INTERVAL
    samples: list[dict[str, Any]] = []
    started = time.monotonic()

    for index in range(count):
        fetched = _http_fetch(host, HTTP_MEASUREMENT_PATH, timeout)
        parsed = parse_status_measurements(fetched.get("body", b""))
        samples.append(
            {
                "index": index + 1,
                "elapsed_seconds": round(time.monotonic() - started, 2),
                "http_status": fetched.get("status"),
                "content_type": fetched.get("content_type"),
                "body_length": fetched.get("body_length", 0),
                "body_sha256_12": fetched.get("body_sha256_12"),
                "error": fetched.get("error"),
                **parsed,
            }
        )
        if index + 1 < count and fetched.get("status") == 200:
            sleep_fn(interval)

    successful = [sample for sample in samples if sample.get("http_status") == 200]
    fields_seen = sorted(
        {
            field
            for sample in successful
            for field in sample.get("measurement_fields_seen", [])
        }
    )
    changing_fields = sorted(
        field
        for field in (*MEASUREMENT_FIELDS, "last_update_value")
        if len(_distinct_values(successful, field)) > 1
    )
    nonzero_fields = sorted(
        field
        for field in MEASUREMENT_FIELDS
        if any(
            isinstance(sample.get("values", {}).get(field), (int, float))
            and sample["values"][field] > 0
            for sample in successful
        )
    )
    live_production_seen = any(
        isinstance(sample.get("values", {}).get("current_power_w"), (int, float))
        and sample["values"]["current_power_w"] > 0
        for sample in successful
    )
    energy_today_seen = any(
        isinstance(sample.get("values", {}).get("yield_today_kwh"), (int, float))
        and sample["values"]["yield_today_kwh"] > 0
        for sample in successful
    )
    measurement_fields_present = bool(fields_seen)

    if not successful:
        conclusion = "status_page_unavailable"
    elif not measurement_fields_present:
        conclusion = "measurement_fields_missing"
    elif live_production_seen or energy_today_seen:
        conclusion = (
            "live_http_measurements_validated"
            if changing_fields
            else "http_measurements_nonzero_seen"
        )
    elif nonzero_fields:
        conclusion = "http_measurements_present_no_live_production"
    else:
        conclusion = "http_measurements_zero_during_sampling"

    return {
        "attempted": True,
        "path": HTTP_MEASUREMENT_PATH,
        "method": "GET",
        "sample_count_requested": count,
        "sample_count_completed": len(samples),
        "successful_http_reads": len(successful),
        "interval_seconds": interval,
        "measurement_fields_seen": fields_seen,
        "changing_fields": changing_fields,
        "nonzero_measurement_fields": nonzero_fields,
        "live_production_seen": live_production_seen,
        "energy_today_seen": energy_today_seen,
        "http_measurements_candidate": measurement_fields_present,
        "http_live_measurements_validated": conclusion == "live_http_measurements_validated",
        "conclusion": conclusion,
        "samples": samples,
        "privacy": {
            "raw_html_stored": False,
            "host_ip_stored": False,
            "logger_sn_stored": False,
            "inverter_serial_stored": False,
            "wifi_credentials_stored": False,
        },
        "safety": {
            "read_only": True,
            "http_get_only": True,
            "http_post_performed": False,
            "configuration_write_performed": False,
        },
    }


def _at_summary(name: str, response: bytes) -> dict[str, Any]:
    text = response.decode("utf-8", errors="replace").strip("\x00\r\n \t")
    payload = text.split("=", 1)[1].strip() if "=" in text else text
    out: dict[str, Any] = {
        "response_length": len(response),
        "response_sha256_12": hashlib.sha256(response).hexdigest()[:12],
        "supported": "+ok" in text.lower(),
        "raw_response_stored": False,
    }
    if name == "network":
        parts = [p.strip() for p in payload.split(",")]
        if len(parts) >= 3:
            out.update(
                {
                    "protocol": parts[0].upper() or None,
                    "role": parts[1].upper() or None,
                    "port": int(parts[2]) if parts[2].isdigit() else None,
                    "remote_ip_present": bool(parts[3]) if len(parts) > 3 else False,
                }
            )
    elif name == "uart":
        out["parameters"] = [
            re.sub(r"[^A-Za-z0-9_.:+-]", "", p)[:40]
            for p in payload.split(",")[:5]
        ]
    elif name == "version":
        out["value"] = re.sub(r"[^A-Za-z0-9_.:+/-]", "", payload)[:120] or None
    else:
        out["value"] = re.sub(r"[^A-Za-z0-9_.:+-]", "", payload)[:80] or None
    return out


def query_at_getters(host: str, timeout: float) -> dict[str, Any]:
    for handshake in base.AT_DISCOVERY_MESSAGES:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        opened = False
        try:
            sock.settimeout(min(max(timeout, 0.25), 2.0))
            sock.connect((host, base.SMARTLINKFIND_PORT))
            sock.send(handshake)
            if not sock.recv(base.AT_MAX_RESPONSE):
                continue
            sock.send(b"+ok")
            opened = True
            time.sleep(0.05)
            rows = []
            for name, command in AT_QUERY_CATALOG:
                sock.send(command)
                try:
                    response = sock.recv(base.AT_MAX_RESPONSE)
                except socket.timeout:
                    rows.append(
                        {
                            "name": name,
                            "command": command.decode().strip(),
                            "query_only": True,
                            "supported": False,
                            "result": "timeout",
                            "raw_response_stored": False,
                        }
                    )
                else:
                    rows.append(
                        {
                            "name": name,
                            "command": command.decode().strip(),
                            "query_only": True,
                            **_at_summary(name, response),
                        }
                    )
                time.sleep(0.03)
            return {
                "attempted": True,
                "transport": "udp48899",
                "queries": rows,
                "query_count": len(rows),
                "assignment_sent": False,
                "configuration_write_performed": False,
                "raw_response_stored": False,
            }
        except OSError as exc:
            last_error = type(exc).__name__
        finally:
            if opened:
                try:
                    sock.send(base.AT_QUIT)
                except OSError:
                    pass
            sock.close()
    return {
        "attempted": True,
        "transport": "udp48899",
        "queries": [],
        "query_count": 0,
        "assignment_sent": False,
        "configuration_write_performed": False,
        "raw_response_stored": False,
        "error": locals().get("last_error"),
    }


def _ports(full: bool, configured: int | None) -> list[int]:
    ports = set(EXTRA_PORTS)
    if configured and 1 <= configured <= 65535:
        ports.add(configured)
    if full:
        for start, end in FULL_RANGES:
            ports.update(range(start, end + 1))
    return sorted(ports)


def _open(host: str, port: int, timeout: float) -> int | None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.settimeout(timeout)
        return port if sock.connect_ex((host, port)) == 0 else None
    except OSError:
        return None
    finally:
        sock.close()


def extra_tcp_inventory(
    host: str,
    full: bool,
    configured: int | None,
    timeout: float,
) -> dict[str, Any]:
    ports = _ports(full, configured)
    bounded = min(max(timeout, 0.025), 0.08)
    with ThreadPoolExecutor(max_workers=24 if full else 12) as pool:
        opened = sorted(
            p for p in pool.map(lambda p: _open(host, p, bounded), ports) if p is not None
        )
    return {
        "attempted": True,
        "mode": "targeted_extended" if full else "targeted_common",
        "ports_tested": len(ports),
        "open_ports": opened,
        "per_port_timeout_seconds": bounded,
        "full_65535_scan_performed": False,
    }


def udp_1097_read(
    tsun_dump: Any,
    host: str,
    sn: int,
    port: int,
    timeout: float,
) -> dict[str, Any]:
    request = tsun_dump.build_modbus_read_request(0x1000, 0x1000, function=0x03)
    rows = []
    for sequence in (0, 1, 2):
        frame = tsun_dump.build_ap_frame(
            sn,
            request,
            sensor_list=0x1097,
            sequence=sequence,
        )
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.settimeout(min(max(timeout, 0.2), 1.0))
            sock.sendto(frame, (host, int(port)))
            try:
                response, _ = sock.recvfrom(4096)
            except socket.timeout:
                rows.append({"sequence": sequence, "result": "timeout"})
                continue
            summary = tsun_dump._summarize_v5_frame(response)
            rows.append(
                {
                    "sequence": sequence,
                    "result": "response",
                    "length": len(response),
                    "sha256_12": hashlib.sha256(response).hexdigest()[:12],
                    "v5_valid": bool(summary.get("valid")),
                    "control": summary.get("control"),
                    "control_name": summary.get("control_name"),
                    "raw_response_stored": False,
                }
            )
        except OSError as exc:
            rows.append(
                {
                    "sequence": sequence,
                    "result": "socket_error",
                    "error": type(exc).__name__,
                }
            )
        finally:
            sock.close()
    return {
        "attempted": True,
        "transport": "udp",
        "port": int(port),
        "sensor_list": "0x1097",
        "function": "0x03",
        "start": "0x1000",
        "count": 1,
        "attempts": rows,
        "write_function_sent": False,
        "configuration_write_performed": False,
    }


def alternate_1097(
    tsun_dump: Any,
    host: str,
    sn: int,
    ports: Iterable[int],
    timeout: float,
) -> list[dict[str, Any]]:
    rows = []
    for port in [
        p
        for p in sorted(set(ports))
        if p in ACTIVE_1097_CANDIDATE_PORTS
        and p not in NO_1097_PROBE
        and p != LEGACY_PORT
    ][:8]:
        try:
            protocol, attempts = tsun_dump.detect_protocol(
                "1097",
                host,
                port,
                sn,
                min(max(timeout, 0.2), 0.8),
            )
        except Exception as exc:
            rows.append(
                {
                    "port": port,
                    "result": "no_valid_1097",
                    "error": type(exc).__name__,
                }
            )
        else:
            rows.append(
                {
                    "port": port,
                    "result": "valid_1097",
                    "protocol": protocol,
                    "detection_attempt_groups": len(attempts)
                    if isinstance(attempts, list)
                    else None,
                }
            )
    return rows


def extend_document(
    tsun_dump: Any,
    args: Any,
    host: str,
    sn: int,
    doc: dict[str, Any],
) -> dict[str, Any]:
    if not _target(doc):
        return doc

    full = bool(getattr(args, "full", False))
    timeout = float(getattr(args, "timeout", 1.0))

    # Phase 1: understand what the logger says it is configured to expose.
    static = extract_static_logger_config(doc.get("logger_web", {}))
    configured = static.get("network", {}).get("port") or LEGACY_PORT

    # Phase 2: confirm the old listener is actually unavailable.
    before = tcp_lifecycle(
        host,
        configured,
        10 if full else 4,
        min(timeout, 0.3),
        0.20,
    )

    # Phase 3: test the safest alternative first: repeated HTTP status reads.
    http_sampling = sample_http_measurements(host, timeout, full=full)

    # Phase 4: preserve the existing GET/AT/lifecycle evidence.
    gets = [_http_get(host, path, timeout) for path in SAFE_HTTP_PATHS]
    after_http = tcp_lifecycle(
        host,
        configured,
        5 if full else 2,
        min(timeout, 0.3),
        0.15,
    )
    at = query_at_getters(host, timeout)
    after_at = tcp_lifecycle(
        host,
        configured,
        5 if full else 2,
        min(timeout, 0.3),
        0.15,
    )

    # Phase 5: bounded protocol research. No configuration or write functions.
    udp = udp_1097_read(tsun_dump, host, sn, configured, timeout)
    inventory = extra_tcp_inventory(
        host,
        full,
        configured,
        float(getattr(args, "tcp_scan_timeout", 0.08)),
    )
    base_ports = set(
        doc.get("transport_research", {}).get("tcp_inventory", {}).get("open_ports", [])
    )
    all_open = sorted(base_ports | set(inventory["open_ports"]))
    alternate = alternate_1097(tsun_dump, host, sn, all_open, timeout)

    network = static.get("network", {})
    http_candidate = bool(http_sampling.get("http_measurements_candidate"))
    http_live_validated = bool(http_sampling.get("http_live_measurements_validated"))
    if http_live_validated:
        recommended_transport = "http_status_page"
        next_step = "implement_and_validate_1097_http_transport"
    elif http_candidate:
        recommended_transport = "http_status_page_candidate"
        next_step = "repeat_http_sampling_while_inverter_is_producing"
    else:
        recommended_transport = "undetermined"
        next_step = "continue_bounded_transport_research"

    evidence = {
        "version": EXTENSION_VERSION,
        "attempted": True,
        "full_mode": full,
        "phase_order": [
            "static_logger_config",
            "legacy_tcp_lifecycle",
            "http_measurement_sampling",
            "safe_http_and_at_rechecks",
            "bounded_alternate_transport_research",
        ],
        "static_logger_config": static,
        "tcp_configured_port_lifecycle_before": before,
        "http_measurement_sampling": http_sampling,
        "http_get_rechecks": gets,
        "tcp_configured_port_lifecycle_after_http": after_http,
        "at_query_catalog": at,
        "tcp_configured_port_lifecycle_after_at": after_at,
        "udp_1097_fc03_probe": udp,
        "extra_tcp_inventory": inventory,
        "alternate_tcp_1097_probes": alternate,
        "summary": {
            "logger_reports_tcp_server_8899": network.get("protocol") == "TCP"
            and network.get("role") == "SERVER"
            and network.get("port") == 8899,
            "configured_port_ever_open": any(
                stage.get("open_count", 0) for stage in (before, after_http, after_at)
            ),
            "http_measurement_fields_seen": http_sampling.get(
                "measurement_fields_seen", []
            ),
            "http_measurements_candidate": http_candidate,
            "http_live_measurements_validated": http_live_validated,
            "http_sampling_conclusion": http_sampling.get("conclusion"),
            "recommended_transport": recommended_transport,
            "next_step": next_step,
            "udp_1097_response_seen": any(
                row.get("result") == "response" for row in udp["attempts"]
            ),
            "alternate_tcp_1097_validated": any(
                row.get("result") == "valid_1097" for row in alternate
            ),
            "open_ports_combined": all_open,
        },
        "safety": {
            "read_only": True,
            "http_get_only": True,
            "http_post_performed": False,
            "at_queries_only": True,
            "at_assignment_sent": False,
            "modbus_functions_sent": ["0x03"],
            "modbus_write_sent": False,
            "configuration_write_performed": False,
            "reboot_performed": False,
            "ota_performed": False,
            "full_65535_tcp_scan_performed": False,
            "raw_network_payload_stored": False,
            "raw_http_body_stored": False,
        },
    }
    doc.setdefault("transport_research", {})["extended_1097"] = evidence
    return doc


def install(tsun_dump: Any) -> None:
    if getattr(tsun_dump, "_research_1097_transport_extension_installed", False):
        return
    original = tsun_dump.capture

    def wrapped(args: Any, host: str, sn: int, discovery: dict[str, Any]):
        doc = original(args, host, sn, discovery)
        if not _target(doc):
            return doc
        try:
            return extend_document(tsun_dump, args, host, sn, doc)
        except Exception as exc:
            doc.setdefault("transport_research", {})["extended_1097"] = {
                "version": EXTENSION_VERSION,
                "attempted": True,
                "error": type(exc).__name__,
                "safety": {
                    "read_only": True,
                    "configuration_write_performed": False,
                    "modbus_write_sent": False,
                },
            }
            return doc

    tsun_dump.capture = wrapped
    tsun_dump._research_1097_transport_extension_installed = True
