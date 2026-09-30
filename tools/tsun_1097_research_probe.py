#!/usr/bin/env python3
# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later
"""Isolated read-only research fallback for changed TSUN 1097 logger transport.

This module intentionally does not replace normal 1511/02B0/1097 detection.
It is installed as a wrapper around ``tsun_dump.capture`` and runs only after
normal protocol detection has failed on an HTTP-identified 1097 logger whose
expected TCP 8899 transport is unavailable.

The research path is bounded and non-destructive:
- one directed ``smartlinkfind`` UDP discovery request to port 48899;
- one getter-only ``AT+UPURL`` query over the logger's UDP 48899 AT assistant;
- a bounded TCP-connect inventory of common/1097-adjacent ports;
- GET-only HTTP summaries on likely alternate web ports;
- TLS handshake-only metadata on likely TLS ports;
- passive banner receives (no application request) on other open ports.

No smart_config/config_ack, AT+UPURL assignment, POST, configuration, reboot,
OTA or inverter write is implemented here. Raw network payloads, IP addresses
and device identifiers are never stored in the generated report.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import http.client
import json
import re
import socket
import ssl
import time
from typing import Any, Iterable
from urllib.parse import urlsplit, urlunsplit


SMARTLINKFIND_PAYLOAD = b"smartlinkfind"
SMARTLINKFIND_PORT = 48899
SMARTLINKFIND_MAX_REPLY = 4096
AT_DISCOVERY_MESSAGES = (
    b"WIFIKIT-214028-READ",
    b"HF-A11ASSISTHREAD",
)
AT_UPURL_QUERY = b"AT+UPURL\n"
AT_QUIT = b"AT+Q\n"
AT_MAX_RESPONSE = 4096
_UPDATE_URL_PATTERN = re.compile(
    r"(?P<url>(?:https?|ftp)://[^\s\x00<>\"']+)",
    re.IGNORECASE,
)

# Keep standard mode very small. Full mode adds only bounded, targeted ranges
# around legacy TSUN 8899 and the logger discovery/config ports seen in TSUN Smart.
STANDARD_TCP_PORTS = frozenset(
    {
        22,
        23,
        53,
        80,
        443,
        1883,
        5000,
        5001,
        6668,
        7000,
        8000,
        8080,
        8443,
        8883,
        8888,
        8890,
        8898,
        8899,
        9000,
        9001,
        9443,
        10000,
        10001,
        48899,
        49999,
    }
)
FULL_TCP_RANGES = (
    (1, 1024),
    (8800, 8910),
    (48750, 50050),
)
HTTP_CANDIDATE_PORTS = frozenset({80, 8000, 8080, 8888})
TLS_CANDIDATE_PORTS = frozenset({443, 8443, 8883, 9443})
SAFE_HTTP_MARKERS = (
    "1097",
    "LSW5",
    "webdata",
    "cover_",
    "smartlinkfind",
    "8899",
)
SAFE_UDP_MARKERS = (
    "smartlinkfind",
    "devicelinkfind",
    "wifikit",
    "hf-a11",
    "1097",
)


def _safe_discovery(discovery: dict[str, Any]) -> dict[str, Any]:
    """Copy only fields already designed for the anonymized report."""
    allowed = (
        "attempted",
        "devices_found",
        "host_discovered",
        "monitor_sn_discovered",
        "target_index",
        "multi_device_scan",
        "sources",
        "firmware_version",
        "protocol_hint",
    )
    result = {key: discovery.get(key) for key in allowed if key in discovery}
    if isinstance(result.get("sources"), (list, tuple, set)):
        result["sources"] = sorted(str(item) for item in result["sources"])
    return result


def _is_eligible_failure(args: Any, discovery: dict[str, Any], exc: BaseException) -> bool:
    """Return true only for the narrow 1097/HTTP/8899-loss research condition."""
    if "No supported TSUN local protocol detected" not in str(exc):
        return False
    if str(getattr(args, "protocol", "auto")).lower() not in {"auto", "1097"}:
        return False
    if discovery.get("transport_kind") == "tuya_oem_candidate":
        return False

    firmware = str(discovery.get("firmware_version") or "")
    hint = str(discovery.get("protocol_hint") or "").lower()
    if hint != "1097" and "1097" not in firmware.lower():
        return False

    sources = {str(item).lower() for item in (discovery.get("sources") or [])}
    if "http80" not in sources:
        return False
    if "tcp8899" in sources:
        return False
    return True


def _classify_payload(payload: bytes) -> str:
    if not payload:
        return "empty"
    stripped = payload.lstrip()
    if stripped.startswith((b"{", b"[")):
        try:
            json.loads(stripped.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            pass
        else:
            return "json"
    printable = sum(32 <= byte <= 126 or byte in (9, 10, 13) for byte in payload)
    if printable / max(1, len(payload)) >= 0.85:
        return "text"
    if payload.startswith(b"\x55\xaa"):
        return "55aa"
    return "binary"


def _fingerprint_payload(payload: bytes, markers: Iterable[str]) -> dict[str, Any]:
    """Describe a payload without keeping its contents or identifiers."""
    lowered = payload.lower()
    return {
        "length": len(payload),
        "sha256_12": hashlib.sha256(payload).hexdigest()[:12],
        "kind": _classify_payload(payload),
        "known_markers": sorted(
            marker
            for marker in markers
            if marker.encode("ascii", errors="ignore").lower() in lowered
        ),
        "raw_payload_stored": False,
    }


def _smartlinkfind_probe(host: str, timeout: float) -> dict[str, Any]:
    """Send only the TSUN Smart read-only discovery keyword to the target logger."""
    bounded_timeout = min(max(float(timeout), 0.15), 2.5)
    replies: list[dict[str, Any]] = []
    sent = False
    error_name: str | None = None

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.settimeout(bounded_timeout)
        sock.bind(("0.0.0.0", 0))
        sock.sendto(SMARTLINKFIND_PAYLOAD, (host, SMARTLINKFIND_PORT))
        sent = True
        while len(replies) < 4:
            try:
                payload, address = sock.recvfrom(SMARTLINKFIND_MAX_REPLY)
            except socket.timeout:
                break
            except OSError as exc:
                error_name = type(exc).__name__
                break
            if not address or address[0] != host:
                continue
            item = _fingerprint_payload(payload, SAFE_UDP_MARKERS)
            item["source_port"] = int(address[1])
            replies.append(item)
    except OSError as exc:
        error_name = type(exc).__name__
    finally:
        sock.close()

    return {
        "attempted": True,
        "destination_port": SMARTLINKFIND_PORT,
        "request": "smartlinkfind",
        "request_sent": sent,
        "response_count": len(replies),
        "responses": replies,
        "error": error_name,
        "broadcast_used": False,
        "configuration_write_performed": False,
        "raw_response_payload_stored": False,
    }


def _sanitize_update_url(value: str) -> dict[str, Any] | None:
    """Keep a useful OTA URL while removing credentials, query and fragment."""
    candidate = value.strip().strip("\x00\r\n \t,;)")
    try:
        parsed = urlsplit(candidate)
        port = parsed.port
    except ValueError:
        return None
    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https", "ftp"} or not parsed.hostname:
        return None

    hostname = parsed.hostname.lower()
    if ":" in hostname and not hostname.startswith("["):
        safe_host = f"[{hostname}]"
    else:
        safe_host = hostname
    netloc = f"{safe_host}:{port}" if port is not None else safe_host
    path = parsed.path or "/"
    if len(path) > 512:
        path = path[:512]
    sanitized_url = urlunsplit((scheme, netloc, path, "", ""))
    filename = path.rsplit("/", 1)[-1] or None
    if filename and len(filename) > 160:
        filename = filename[:160]

    return {
        "scheme": scheme,
        "hostname": hostname,
        "port": port,
        "path": path,
        "filename": filename,
        "sanitized_url": sanitized_url,
        "credentials_stripped": parsed.username is not None or parsed.password is not None,
        "query_stripped": bool(parsed.query),
        "fragment_stripped": bool(parsed.fragment),
        "external_url_contacted": False,
    }


def _summarize_upurl_response(response: bytes) -> dict[str, Any]:
    """Extract privacy-safe OTA URL candidates from an AT+UPURL getter response."""
    text = response.decode("utf-8", errors="replace").strip("\x00\r\n \t")
    urls: list[dict[str, Any]] = []
    seen: set[str] = set()
    for match in _UPDATE_URL_PATTERN.finditer(text):
        item = _sanitize_update_url(match.group("url"))
        if item is None:
            continue
        key = str(item["sanitized_url"])
        if key in seen:
            continue
        seen.add(key)
        urls.append(item)

    lowered = text.lower()
    supported = bool(urls) or "+ok" in lowered
    return {
        "supported": supported,
        "candidate_count": len(urls),
        "url_candidates": urls,
        "response_length": len(response),
        "response_sha256_12": hashlib.sha256(response).hexdigest()[:12],
        "raw_response_stored": False,
    }


def _query_upurl_read_only(host: str, timeout: float) -> dict[str, Any]:
    """Read the configured firmware URL using only the getter form AT+UPURL."""
    bounded_timeout = min(max(float(timeout), 0.25), 2.5)
    last_error: str | None = None
    last_summary: dict[str, Any] | None = None

    for handshake in AT_DISCOVERY_MESSAGES:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        session_open = False
        try:
            sock.settimeout(bounded_timeout)
            sock.connect((host, SMARTLINKFIND_PORT))
            sock.send(handshake)
            handshake_response = sock.recv(AT_MAX_RESPONSE)
            if not handshake_response:
                continue

            # Enter the existing local AT assistant session. The only setting
            # command sent below is the documented getter form without '='.
            sock.send(b"+ok")
            session_open = True
            time.sleep(0.05)
            sock.send(AT_UPURL_QUERY)
            response = sock.recv(AT_MAX_RESPONSE)
            summary = _summarize_upurl_response(response)
            last_summary = summary
            if summary["supported"]:
                return {
                    "attempted": True,
                    "read_only": True,
                    "transport": "udp48899",
                    "command": "AT+UPURL",
                    "getter_form_only": True,
                    "assignment_sent": False,
                    "ota_trigger_sent": False,
                    "external_url_contacted": False,
                    "handshake": (
                        "WIFIKIT-214028-READ"
                        if handshake.startswith(b"WIFIKIT")
                        else "HF-A11ASSISTHREAD"
                    ),
                    **summary,
                }
        except OSError as exc:
            last_error = type(exc).__name__
        finally:
            if session_open:
                try:
                    sock.send(AT_QUIT)
                except OSError:
                    pass
            sock.close()

    result: dict[str, Any] = {
        "attempted": True,
        "read_only": True,
        "transport": "udp48899",
        "command": "AT+UPURL",
        "getter_form_only": True,
        "assignment_sent": False,
        "ota_trigger_sent": False,
        "external_url_contacted": False,
        "supported": False,
        "candidate_count": 0,
        "url_candidates": [],
        "raw_response_stored": False,
    }
    if last_summary is not None:
        result.update(last_summary)
    if last_error is not None:
        result["error"] = last_error
    return result


def _ports_to_scan(full: bool) -> list[int]:
    ports = set(STANDARD_TCP_PORTS)
    if full:
        for start, end in FULL_TCP_RANGES:
            ports.update(range(start, end + 1))
    return sorted(port for port in ports if 1 <= port <= 65535)


def _one_tcp_open(host: str, port: int, timeout: float) -> int | None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.settimeout(timeout)
        return port if sock.connect_ex((host, port)) == 0 else None
    except OSError:
        return None
    finally:
        sock.close()


def _scan_tcp_ports(host: str, *, full: bool, timeout: float) -> dict[str, Any]:
    ports = _ports_to_scan(full)
    bounded_timeout = min(max(float(timeout), 0.03), 0.15)
    with ThreadPoolExecutor(max_workers=32) as executor:
        results = executor.map(
            lambda port: _one_tcp_open(host, port, bounded_timeout),
            ports,
        )
        opened = sorted(port for port in results if port is not None)
    return {
        "attempted": True,
        "mode": "bounded_extended" if full else "common_ports",
        "ports_tested": len(ports),
        "open_ports": opened,
        "per_port_timeout_seconds": bounded_timeout,
        "full_65535_scan_performed": False,
    }


def _http_probe(host: str, port: int, timeout: float, user_agent: str) -> dict[str, Any]:
    """Perform one GET / and retain only non-identifying response metadata."""
    connection = http.client.HTTPConnection(
        host, port=port, timeout=min(max(timeout, 0.2), 2.0)
    )
    try:
        connection.request(
            "GET",
            "/",
            headers={"User-Agent": user_agent, "Accept": "text/html,*/*;q=0.1"},
        )
        response = connection.getresponse()
        body = response.read(64 * 1024)
        lowered = body.lower()
        return {
            "port": port,
            "status": int(response.status),
            "content_type": (response.getheader("Content-Type") or "")[:96],
            "server": (response.getheader("Server") or "")[:96],
            "body_length": len(body),
            "body_sha256_12": hashlib.sha256(body).hexdigest()[:12],
            "known_markers": sorted(
                marker
                for marker in SAFE_HTTP_MARKERS
                if marker.encode("ascii", errors="ignore").lower() in lowered
            ),
            "body_stored": False,
            "method": "GET",
        }
    except (OSError, http.client.HTTPException) as exc:
        return {
            "port": port,
            "error": type(exc).__name__,
            "body_stored": False,
            "method": "GET",
        }
    finally:
        connection.close()


def _tls_probe(host: str, port: int, timeout: float) -> dict[str, Any]:
    """Perform a TLS ClientHello/handshake only; send no application data."""
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    raw: socket.socket | None = None
    wrapped: ssl.SSLSocket | None = None
    try:
        raw = socket.create_connection(
            (host, port), timeout=min(max(timeout, 0.2), 2.0)
        )
        raw.settimeout(min(max(timeout, 0.2), 2.0))
        wrapped = context.wrap_socket(raw, server_hostname=None)
        certificate = wrapped.getpeercert(binary_form=True) or b""
        cipher = wrapped.cipher()
        return {
            "port": port,
            "handshake_ok": True,
            "tls_version": wrapped.version(),
            "cipher": cipher[0] if cipher else None,
            "certificate_sha256_12": (
                hashlib.sha256(certificate).hexdigest()[:12]
                if certificate
                else None
            ),
            "certificate_contents_stored": False,
            "application_data_sent": False,
        }
    except (OSError, ssl.SSLError) as exc:
        return {
            "port": port,
            "handshake_ok": False,
            "error": type(exc).__name__,
            "certificate_contents_stored": False,
            "application_data_sent": False,
        }
    finally:
        if wrapped is not None:
            try:
                wrapped.close()
            except OSError:
                pass
        elif raw is not None:
            try:
                raw.close()
            except OSError:
                pass


def _passive_banner_probe(
    host: str, port: int, timeout: float
) -> dict[str, Any] | None:
    """Connect and receive only; do not send an application payload."""
    try:
        with socket.create_connection(
            (host, port), timeout=min(max(timeout, 0.1), 0.6)
        ) as sock:
            sock.settimeout(min(max(timeout, 0.1), 0.6))
            try:
                payload = sock.recv(512)
            except socket.timeout:
                return None
    except OSError:
        return None
    if not payload:
        return None
    item = _fingerprint_payload(payload, SAFE_UDP_MARKERS)
    item.update({"port": port, "application_data_sent": False})
    return item


def capture_research(
    tsun_dump_module: Any,
    args: Any,
    host: str,
    discovery: dict[str, Any],
    reason: str,
) -> dict[str, Any]:
    """Build one schema-compatible privacy-safe transport-change research report."""
    created_at = datetime.now(timezone.utc)
    full = bool(getattr(args, "full", False))
    timeout = float(getattr(args, "timeout", 2.0))
    tcp_timeout = float(getattr(args, "tcp_scan_timeout", 0.1))
    http_timeout = float(getattr(args, "http_page_timeout", 1.0))

    smartlink = _smartlinkfind_probe(host, min(timeout, 2.5))
    update_url = _query_upurl_read_only(host, min(timeout, 2.5))
    tcp_inventory = _scan_tcp_ports(host, full=full, timeout=tcp_timeout)
    open_ports = list(tcp_inventory["open_ports"])

    http_probes = [
        _http_probe(
            host,
            port,
            http_timeout,
            f"TSUN-Local-Diagnostic/{getattr(tsun_dump_module, 'TOOL_VERSION', 'unknown')}",
        )
        for port in open_ports
        if port in HTTP_CANDIDATE_PORTS
    ]
    tls_probes = [
        _tls_probe(host, port, min(timeout, 2.0))
        for port in open_ports
        if port in TLS_CANDIDATE_PORTS
    ]
    banner_probes = []
    for port in open_ports:
        if port in HTTP_CANDIDATE_PORTS or port in TLS_CANDIDATE_PORTS:
            continue
        item = _passive_banner_probe(host, port, min(timeout, 0.6))
        if item is not None:
            banner_probes.append(item)

    try:
        logger_web = tsun_dump_module.capture_logger_web_pages(host, http_timeout)
    except Exception as exc:  # research fallback must never mask the transport report
        logger_web = {
            "attempted": True,
            "pages_found": 0,
            "error": type(exc).__name__,
            "privacy": {"raw_html_stored": False, "host_ip_stored": False},
        }

    safe_reason = "normal TSUN protocol detection failed after bounded retries"
    firmware = str(discovery.get("firmware_version") or "") or None
    return {
        "format": tsun_dump_module.DUMP_FORMAT,
        "schema_version": tsun_dump_module.SCHEMA_VERSION,
        "metadata": {
            "timestamp_utc": created_at.isoformat(),
            "tool": "TSUN Local Hardware Validation Dump Tool",
            "tool_version": tsun_dump_module.TOOL_VERSION,
            "tool_sha256": None,
            "tool_source": tsun_dump_module.SOURCE_URL,
            "standalone": False,
            "python_required": ">=3.10",
            "read_only": True,
            "capture_mode": "full" if full else "standard",
            "capture_status": "partial_success",
            "detected_protocol": "1097-research",
            "protocol_validation_status": "known_firmware_transport_changed",
            "capture_limitation": "legacy_tcp_8899_unavailable",
            "measurements_available": False,
            "device_reachable": True,
            "model_family": "GEN4 / 1097 transport research",
            "model_supplied_by_user": getattr(args, "model", None),
            "pv_count": None,
            "port": getattr(args, "port", 8899),
            "privacy": {
                "host_in_output": False,
                "logger_sn_in_output": False,
                "inverter_serial_in_output": False,
                "udp_discovery_payload_in_output": False,
                "network_banner_payload_in_output": False,
                "tls_certificate_contents_in_output": False,
                "http_body_in_transport_probe_output": False,
                "ota_url_credentials_in_output": False,
                "ota_url_query_in_output": False,
                "ota_url_fragment_in_output": False,
            },
        },
        "discovery": _safe_discovery(discovery),
        "logger_web": logger_web,
        "transport_research": {
            "trigger": {
                "firmware_version": firmware,
                "protocol_hint": discovery.get("protocol_hint"),
                "http_identity_available": True,
                "legacy_tcp_8899_discovered": False,
                "normal_detection_failure": safe_reason,
            },
            "smartlinkfind_udp": smartlink,
            "firmware_update_url_query": update_url,
            "tcp_inventory": tcp_inventory,
            "http_get_probes": http_probes,
            "tls_handshake_probes": tls_probes,
            "passive_banner_probes": banner_probes,
            "safety": {
                "read_only": True,
                "smartlinkfind_only_udp_request": True,
                "upurl_query_only": True,
                "upurl_assignment_sent": False,
                "external_firmware_url_contacted": False,
                "smart_config_sent": False,
                "config_ack_sent": False,
                "http_post_performed": False,
                "configuration_write_performed": False,
                "inverter_write_performed": False,
                "reboot_performed": False,
                "firmware_update_performed": False,
                "ota_performed": False,
                "full_65535_tcp_scan_performed": False,
            },
        },
        "protocol_detection": {
            "requested": getattr(args, "protocol", "auto"),
            "selected": "1097-research",
            "confidence": (
                "1097 logger firmware identified by HTTP while legacy TCP 8899 "
                "is absent and normal TSUN protocol detection failed"
            ),
            "attempts": [],
        },
        "decoded_known_measurements": {},
        "capture_summary": {
            "snapshots": 0,
            "snapshot_interval_seconds": getattr(args, "interval", 0.0),
            "coherent_snapshots": 0,
            "decoded_snapshot_index": None,
            "successful_block_reads": 0,
            "failed_block_reads": 0,
            "unique_raw_registers": 0,
        },
        "raw_registers": [],
        "snapshots": [],
        "analysis": tsun_dump_module.analyze_snapshots([]),
        "blocks": [],
        "protocol_trace": [],
        "logger_dns_probe": {
            "attempted": False,
            "read_only": True,
            "reason": "legacy TCP 8899 transport unavailable",
        },
    }


def install(tsun_dump_module: Any) -> None:
    """Install the fallback once without changing any successful normal capture."""
    if getattr(tsun_dump_module, "_research_1097_probe_installed", False):
        return
    original = tsun_dump_module.capture

    def wrapped(args: Any, host: str, sn: int, discovery: dict[str, Any]):
        try:
            return original(args, host, sn, discovery)
        except RuntimeError as exc:
            if not _is_eligible_failure(args, discovery, exc):
                raise
            print(
                "1097 logger identified over HTTP but TCP 8899 is unavailable; "
                "running bounded read-only transport research..."
            )
            return capture_research(tsun_dump_module, args, host, discovery, str(exc))

    tsun_dump_module.capture = wrapped
    tsun_dump_module._research_1097_probe_installed = True
