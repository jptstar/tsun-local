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
- passive banner receives (no application request) on other open ports;
- a privacy-safe structured snapshot of the local transport settings already
  exposed by the logger web UI;
- a bounded connection-only availability watch of the configured local TCP
  server port (normally 8899), without sending application data;
- one GET-only runtime snapshot of ``/status.html`` to retain AP/STA mode,
  remote-status flags and only boolean inverter-data availability;
- when the logger advertises a private AP address, bounded connection-only
  checks of HTTP 80 and the configured local server port on that AP interface.

No smart_config/config_ack, AT+UPURL assignment, POST, configuration, reboot,
OTA or inverter write is implemented here. Raw network payloads, IP addresses,
cloud server hostnames and device identifiers are never added to the new
structured transport snapshot.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import http.client
import ipaddress
import json
import re
import socket
import ssl
import time
from typing import Any, Iterable
from urllib.parse import urlsplit, urlunsplit


PROBE_REVISION = 3
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
_WEB_TRANSPORT_VARIABLES = (
    "yz_tmode",
    "server_a",
    "server_b",
    "uart_setting_baud",
    "uart_setting_data",
    "uart_setting_parity",
    "uart_setting_stop",
    "uart_setting_fc",
    "net_setting_pro",
    "net_setting_cs",
    "net_setting_port",
    "net_setting_ip",
    "net_setting_to",
    "inv_set",
    "apsta_mode",
    "inv_tp",
    "inv_tp_seld",
)
_WEB_TRANSPORT_PATHS = frozenset({"/hide_set_edit.html", "/remote.html"})
_STATUS_VARIABLES = (
    "cover_wmode",
    "cover_ap_ip",
    "status_a",
    "status_b",
    "status_c",
    "webdata_sn",
    "webdata_msvn",
    "webdata_ssvn",
    "webdata_pv_type",
    "webdata_rate_p",
    "webdata_now_p",
    "webdata_today_e",
    "webdata_total_e",
    "webdata_alarm",
    "webdata_utime",
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


def _parse_int(value: str | None, *, minimum: int = 0, maximum: int = 65535) -> int | None:
    try:
        parsed = int(str(value).strip())
    except (TypeError, ValueError):
        return None
    return parsed if minimum <= parsed <= maximum else None


def _parse_float(value: str | None) -> float | None:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def _extract_named_js_variables(document: str, names: Iterable[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for name in names:
        match = re.search(
            rf"\bvar\s+{re.escape(name)}\s*=\s*\"([^\"]*)\"\s*;",
            document,
        )
        if match:
            result[name] = match.group(1)[:256]
    return result


def _extract_js_variables(document: str) -> dict[str, str]:
    """Extract only the bounded transport/profile variables we explicitly need."""
    return _extract_named_js_variables(document, _WEB_TRANSPORT_VARIABLES)


def _endpoint_kind(value: str) -> str:
    value = value.strip()
    if not value:
        return "empty"
    if value.startswith("<") and value.endswith(">"):
        return "redacted"
    try:
        socket.inet_pton(socket.AF_INET, value)
    except OSError:
        try:
            socket.inet_pton(socket.AF_INET6, value)
        except OSError:
            return "hostname"
        return "ip"
    return "ip"


def _safe_server_endpoint(value: str | None) -> dict[str, Any]:
    """Parse server settings while deliberately dropping the hostname/address."""
    raw = str(value or "")
    parts = raw.split(",")
    if len(parts) < 4:
        return {
            "configured": bool(raw.strip()),
            "endpoint_kind": "unknown" if raw.strip() else "empty",
            "port": None,
            "protocol": None,
            "endpoint_value_stored": False,
        }
    if len(parts) == 4:
        endpoint = parts[0] or parts[1]
        port_raw = parts[2]
        protocol = parts[3]
    else:
        endpoint, port_raw, protocol = parts[-3], parts[-2], parts[-1]
    return {
        "configured": bool(endpoint or port_raw or protocol),
        "endpoint_kind": _endpoint_kind(endpoint),
        "port": _parse_int(port_raw, minimum=1),
        "protocol": protocol[:16] or None,
        "endpoint_value_stored": False,
    }


def _extract_logger_web_transport_settings(logger_web: dict[str, Any]) -> dict[str, Any]:
    """Create a privacy-safe structured snapshot from already captured web pages."""
    variables: dict[str, str] = {}
    source_paths: set[str] = set()
    for item in logger_web.get("pages") or []:
        if not isinstance(item, dict):
            continue
        path = str(item.get("path") or "")
        if path not in _WEB_TRANSPORT_PATHS:
            continue
        content = item.get("content")
        if not isinstance(content, str):
            continue
        extracted = _extract_js_variables(content)
        if not extracted:
            continue
        source_paths.add(path)
        for key, value in extracted.items():
            variables.setdefault(key, value)

    net_port = _parse_int(variables.get("net_setting_port"), minimum=1)
    net_timeout = _parse_int(variables.get("net_setting_to"), minimum=0, maximum=600)
    address_value = str(variables.get("net_setting_ip") or "")
    inv_type = str(variables.get("inv_tp") or "")
    inv_set = str(variables.get("inv_set") or "")
    profile_id: str | None = None
    profile_name: str | None = None
    if ":" in inv_type:
        profile_id, profile_name = inv_type.split(":", 1)
        profile_id = profile_id[:32] or None
        profile_name = profile_name[:96] or None

    return {
        "attempted": True,
        "found": bool(variables),
        "source_paths": sorted(source_paths),
        "transport_mode": variables.get("yz_tmode"),
        "local_network": {
            "protocol": variables.get("net_setting_pro"),
            "role": variables.get("net_setting_cs"),
            "port": net_port,
            "timeout_seconds": net_timeout,
            "address_kind": _endpoint_kind(address_value),
            "address_value_stored": False,
        },
        "uart": {
            "baud": _parse_int(variables.get("uart_setting_baud"), maximum=1_000_000),
            "data_bits": variables.get("uart_setting_data"),
            "parity": variables.get("uart_setting_parity"),
            "stop_bits": variables.get("uart_setting_stop"),
            "flow_control": variables.get("uart_setting_fc"),
        },
        "cloud_server_a": _safe_server_endpoint(variables.get("server_a")),
        "cloud_server_b": _safe_server_endpoint(variables.get("server_b")),
        "inverter_profile": {
            "id": profile_id,
            "name": profile_name,
            "selection_raw": inv_set[:64] or None,
        },
        "apsta_mode": variables.get("apsta_mode"),
        "privacy": {
            "cloud_server_endpoint_value_stored": False,
            "local_network_address_value_stored": False,
            "raw_variable_block_stored": False,
        },
    }


def _private_ipv4(value: str | None) -> str | None:
    raw = str(value or "").strip()
    try:
        parsed = ipaddress.ip_address(raw)
    except ValueError:
        return None
    if parsed.version != 4 or not parsed.is_private:
        return None
    return raw


def _extract_status_runtime_snapshot(document: str) -> tuple[dict[str, Any], str | None]:
    """Extract AP/STA and coarse telemetry facts without retaining identifiers."""
    variables = _extract_named_js_variables(document, _STATUS_VARIABLES)
    ap_ip = _private_ipv4(variables.get("cover_ap_ip"))
    identity_presence = {
        "serial_present": bool(str(variables.get("webdata_sn") or "").strip()),
        "main_software_version_present": bool(str(variables.get("webdata_msvn") or "").strip()),
        "slave_software_version_present": bool(str(variables.get("webdata_ssvn") or "").strip()),
        "pv_type_present": bool(str(variables.get("webdata_pv_type") or "").strip()),
        "rated_power_present": bool(str(variables.get("webdata_rate_p") or "").strip()),
        "alarm_present": bool(str(variables.get("webdata_alarm") or "").strip()),
        "uptime_present": bool(str(variables.get("webdata_utime") or "").strip()),
    }
    numeric = {
        "power_nonzero": bool((_parse_float(variables.get("webdata_now_p")) or 0.0) != 0.0),
        "today_energy_nonzero": bool((_parse_float(variables.get("webdata_today_e")) or 0.0) != 0.0),
        "total_energy_nonzero": bool((_parse_float(variables.get("webdata_total_e")) or 0.0) != 0.0),
    }
    safe = {
        "found": bool(variables),
        "wireless_mode": variables.get("cover_wmode"),
        "ap_address_present": bool(str(variables.get("cover_ap_ip") or "").strip()),
        "ap_address_private_ipv4": ap_ip is not None,
        "ap_address_value_stored": False,
        "remote_status_flags": {
            "a": _parse_int(variables.get("status_a"), maximum=9),
            "b": _parse_int(variables.get("status_b"), maximum=9),
            "c": _parse_int(variables.get("status_c"), maximum=9),
            "semantics_assumed": False,
        },
        "inverter_webdata_presence": {**identity_presence, **numeric},
        "raw_status_html_stored": False,
    }
    return safe, ap_ip


def _capture_logger_status_runtime(
    host: str,
    timeout: float,
    user_agent: str,
) -> tuple[dict[str, Any], str | None]:
    """GET /status.html once and keep only privacy-safe derived evidence."""
    connection = http.client.HTTPConnection(
        host, port=80, timeout=min(max(float(timeout), 0.2), 2.0)
    )
    try:
        connection.request(
            "GET",
            "/status.html",
            headers={"User-Agent": user_agent, "Accept": "text/html,*/*;q=0.1"},
        )
        response = connection.getresponse()
        body = response.read(64 * 1024)
        text = body.decode("utf-8", errors="replace")
        snapshot, ap_ip = _extract_status_runtime_snapshot(text)
        snapshot.update(
            {
                "attempted": True,
                "method": "GET",
                "path": "/status.html",
                "http_status": int(response.status),
                "response_body_stored": False,
                "configuration_write_performed": False,
            }
        )
        return snapshot, ap_ip
    except (OSError, http.client.HTTPException) as exc:
        return (
            {
                "attempted": True,
                "method": "GET",
                "path": "/status.html",
                "error": type(exc).__name__,
                "found": False,
                "ap_address_value_stored": False,
                "response_body_stored": False,
                "configuration_write_performed": False,
            },
            None,
        )
    finally:
        connection.close()


def _watch_tcp_service(
    host: str,
    port: int,
    *,
    full: bool,
    timeout: float,
) -> dict[str, Any]:
    """Repeatedly connect to one port without sending application data."""
    bounded_port = int(port) if 1 <= int(port) <= 65535 else 8899
    interval = 1.0
    duration = 20.0 if full else 5.0
    attempts = int(duration / interval) + 1
    connect_timeout = min(max(float(timeout), 0.03), 0.15)
    observations: list[dict[str, Any]] = []
    successful = 0
    first_open_offset: float | None = None
    transitions = 0
    previous: bool | None = None

    for index in range(attempts):
        if index:
            time.sleep(interval)
        is_open = _one_tcp_open(host, bounded_port, connect_timeout) is not None
        offset = round(index * interval, 3)
        observations.append({"offset_seconds": offset, "open": is_open})
        if is_open:
            successful += 1
            if first_open_offset is None:
                first_open_offset = offset
        if previous is not None and previous != is_open:
            transitions += 1
        previous = is_open

    return {
        "attempted": True,
        "port": bounded_port,
        "duration_seconds": duration,
        "interval_seconds": interval,
        "connect_timeout_seconds": connect_timeout,
        "attempts": attempts,
        "successful_connections": successful,
        "observed_open": successful > 0,
        "first_open_offset_seconds": first_open_offset,
        "state_transitions": transitions,
        "observations": observations,
        "connection_only": True,
        "application_data_sent": False,
        "configuration_write_performed": False,
    }


def _probe_ap_interface(
    ap_ip: str | None,
    configured_port: int,
    *,
    wireless_mode: str | None,
    timeout: float,
) -> dict[str, Any]:
    """Passively compare the advertised AP interface without exposing its address."""
    mode = str(wireless_mode or "").upper()
    if mode not in {"AP", "APSTA"}:
        return {
            "attempted": False,
            "reason": "logger_ap_not_advertised",
            "wireless_mode": wireless_mode,
            "ap_address_value_stored": False,
            "connection_only": True,
            "application_data_sent": False,
        }
    if ap_ip is None:
        return {
            "attempted": False,
            "reason": "advertised_ap_address_unavailable_or_not_private_ipv4",
            "wireless_mode": wireless_mode,
            "ap_address_value_stored": False,
            "connection_only": True,
            "application_data_sent": False,
        }

    port = int(configured_port) if 1 <= int(configured_port) <= 65535 else 8899
    connect_timeout = min(max(float(timeout), 0.05), 0.25)
    http_open = _one_tcp_open(ap_ip, 80, connect_timeout) is not None
    service_results: list[bool] = []
    for index in range(3):
        if index:
            time.sleep(0.2)
        service_results.append(_one_tcp_open(ap_ip, port, connect_timeout) is not None)
    service_open = any(service_results)
    reachability_confirmed = http_open or service_open

    if service_open:
        outcome = "configured_service_observed_on_ap_interface"
    elif http_open:
        outcome = "ap_interface_reachable_but_configured_service_not_observed"
    else:
        outcome = "ap_interface_not_reachable_from_current_network_or_services_closed"

    return {
        "attempted": True,
        "wireless_mode": wireless_mode,
        "ap_address_private_ipv4": True,
        "ap_address_value_stored": False,
        "http_port_80_open": http_open,
        "reachability_confirmed": reachability_confirmed,
        "configured_port": port,
        "configured_port_attempts": len(service_results),
        "configured_port_successes": sum(service_results),
        "configured_port_open": service_open,
        "outcome": outcome,
        "connection_only": True,
        "application_data_sent": False,
        "configuration_write_performed": False,
    }


def _compare_configured_service(
    settings: dict[str, Any],
    tcp_inventory: dict[str, Any],
    service_watch: dict[str, Any],
) -> dict[str, Any]:
    local = settings.get("local_network") if isinstance(settings, dict) else None
    local = local if isinstance(local, dict) else {}
    protocol = str(local.get("protocol") or "").upper()
    role = str(local.get("role") or "").upper()
    port = local.get("port") if isinstance(local.get("port"), int) else None
    configured_server = protocol == "TCP" and role == "SERVER" and port is not None
    inventory_open_ports = {
        int(item)
        for item in (tcp_inventory.get("open_ports") or [])
        if isinstance(item, int)
    }
    inventory_observed = bool(port is not None and port in inventory_open_ports)
    watch_observed = bool(service_watch.get("observed_open"))
    mismatch = configured_server and not inventory_observed and not watch_observed

    if not configured_server:
        status = "not_configured_as_tcp_server"
    elif mismatch:
        status = "configured_but_not_observed"
    else:
        status = "configured_and_observed"

    return {
        "configured_as_tcp_server": configured_server,
        "configured_port": port,
        "inventory_observed_open": inventory_observed,
        "watch_observed_open": watch_observed,
        "configuration_runtime_mismatch": mismatch,
        "status": status,
    }


def _classify_local_access(
    configuration_vs_runtime: dict[str, Any],
    ap_probe: dict[str, Any],
) -> dict[str, Any]:
    sta_open = bool(
        configuration_vs_runtime.get("inventory_observed_open")
        or configuration_vs_runtime.get("watch_observed_open")
    )
    ap_attempted = bool(ap_probe.get("attempted"))
    ap_open = ap_probe.get("configured_port_open") is True
    ap_reachable = ap_probe.get("reachability_confirmed") is True

    if sta_open and ap_open:
        status = "configured_service_observed_on_sta_and_ap"
    elif sta_open:
        status = "configured_service_observed_on_sta"
    elif ap_open:
        status = "configured_service_observed_on_ap_only_candidate"
    elif ap_attempted and ap_reachable:
        status = "configured_service_not_observed_on_sta_or_reachable_ap"
    elif ap_attempted:
        status = "ap_follow_up_requires_direct_ap_connection"
    else:
        status = "sta_service_not_observed_ap_not_testable"

    return {
        "status": status,
        "sta_service_observed": sta_open,
        "ap_probe_attempted": ap_attempted,
        "ap_reachability_confirmed": ap_reachable,
        "ap_service_observed": ap_open,
    }


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
    user_agent = f"TSUN-Local-Diagnostic/{getattr(tsun_dump_module, 'TOOL_VERSION', 'unknown')}"

    smartlink = _smartlinkfind_probe(host, min(timeout, 2.5))
    update_url = _query_upurl_read_only(host, min(timeout, 2.5))
    tcp_inventory = _scan_tcp_ports(host, full=full, timeout=tcp_timeout)
    open_ports = list(tcp_inventory["open_ports"])

    http_probes = [
        _http_probe(
            host,
            port,
            http_timeout,
            user_agent,
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

    web_settings = _extract_logger_web_transport_settings(logger_web)
    local_network = web_settings.get("local_network") or {}
    configured_port = local_network.get("port")
    watch_port = configured_port if isinstance(configured_port, int) else 8899
    service_watch = _watch_tcp_service(
        host,
        watch_port,
        full=full,
        timeout=tcp_timeout,
    )
    config_observation = _compare_configured_service(
        web_settings,
        tcp_inventory,
        service_watch,
    )
    status_runtime, ap_ip = _capture_logger_status_runtime(
        host,
        http_timeout,
        user_agent,
    )
    ap_interface_probe = _probe_ap_interface(
        ap_ip,
        watch_port,
        wireless_mode=status_runtime.get("wireless_mode"),
        timeout=tcp_timeout,
    )
    local_access = _classify_local_access(config_observation, ap_interface_probe)

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
                "structured_cloud_server_endpoint_in_output": False,
                "structured_local_network_address_in_output": False,
                "ap_interface_address_in_output": False,
            },
        },
        "discovery": _safe_discovery(discovery),
        "logger_web": logger_web,
        "transport_research": {
            "probe_revision": PROBE_REVISION,
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
            "logger_transport_settings": web_settings,
            "configured_tcp_service_watch": service_watch,
            "configuration_vs_runtime": config_observation,
            "logger_status_runtime": status_runtime,
            "ap_interface_probe": ap_interface_probe,
            "local_access_assessment": local_access,
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
                "service_watch_connection_only": True,
                "service_watch_application_data_sent": False,
                "status_snapshot_get_only": True,
                "ap_interface_probe_connection_only": True,
                "ap_interface_probe_application_data_sent": False,
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
