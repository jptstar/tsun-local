#!/usr/bin/env python3
# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later
"""Read-only Sunology PLAY2 local diagnostic probe.

The probe tests multiple known local discovery and GEN3/GEN3+ read variants in
one run. It never sends configuration/write commands. A privacy-safe JSON file
is written even when no supported inverter protocol is detected.

Python standard library only. Python >= 3.10.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import http.client
from ipaddress import IPv4Address, ip_network
import json
import math
from pathlib import Path
import re
import socket
import ssl
import sys
import time
from typing import Any, Iterable

TOOL_VERSION = "1.1.0"
TCP_PORT = 8899
IGEN_SEND_PORT = 48899
IGEN_RECV_PORT = 49999
IGEN_MULTICAST = "239.0.0.0"
IGEN_MESSAGE = b"smartlinkfind"
LEGACY_DISCOVERY_MESSAGES = (
    b"WIFIKIT-214028-READ",
    b"HF-A11ASSISTHREAD",
    b"devicelinkfind",
)
HTTP_PATHS = ("/index_cn.html", "/index.html", "/status.html", "/")
HTTP_AUTH = base64.b64encode(b"admin:admin").decode("ascii")
BASELINE_RETRIES = 3
ALT_RETRIES = 1
RETRY_DELAY = 0.35
MAX_UDP_PACKET = 4096
MAX_HTTP_PAGE = 512 * 1024
MAX_AP_REMAINING = 65545

SERIAL_RE = re.compile(r"(?<!\d)([1-9]\d{7,9})(?!\d)")
IP_RE = re.compile(
    r"(?<!\d)(?:25[0-5]|2[0-4]\d|1?\d?\d)"
    r"(?:\.(?:25[0-5]|2[0-4]\d|1?\d?\d)){3}(?!\d)"
)
MAC_RE = re.compile(r"(?i)(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}")
FW_PATTERNS = (
    re.compile(
        r"\b(?:webdata|cover)[_-]ver\s*[:=]\s*[\"']?"
        r"([A-Za-z0-9][A-Za-z0-9._-]{0,79})",
        re.I,
    ),
    re.compile(
        r"\bfirmware(?:\s*version|Version)?[^A-Za-z0-9._-]+"
        r"([A-Za-z0-9][A-Za-z0-9._-]{0,79})",
        re.I,
    ),
)


def valid_sn(value: int) -> bool:
    return 0 < value <= 0xFFFFFFFF


def arg_sn(value: str) -> int:
    try:
        number = int(value)
    except ValueError as err:
        raise argparse.ArgumentTypeError("Monitor SN must be numeric") from err
    if not valid_sn(number):
        raise argparse.ArgumentTypeError("Monitor SN must be 1..4294967295")
    return number


def arg_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("value must be a finite number > 0")
    return number


def error_record(stage: str, err: BaseException, detail: str | None = None) -> dict[str, str]:
    return {
        "stage": stage,
        "type": type(err).__name__,
        "detail": detail or type(err).__name__,
    }


def parse_discovery_payload(payload: bytes) -> dict[str, Any]:
    text = payload.decode("utf-8", errors="replace").strip("\x00\r\n ")
    result: dict[str, Any] = {
        "format": "text",
        "sn": None,
        "ip": None,
        "mac": None,
        "length": len(payload),
    }
    try:
        obj = json.loads(text)
    except (TypeError, ValueError):
        obj = None

    if isinstance(obj, dict):
        result["format"] = "json"
        for key in ("mid", "sn", "serial", "loggerSn", "monitorSn"):
            try:
                candidate = int(str(obj.get(key, "")).strip())
            except (TypeError, ValueError):
                continue
            if valid_sn(candidate):
                result["sn"] = candidate
                break
        ip = obj.get("ip")
        mac = obj.get("mac")
        if isinstance(ip, str) and IP_RE.fullmatch(ip.strip()):
            result["ip"] = ip.strip()
        if isinstance(mac, str) and MAC_RE.fullmatch(mac.strip()):
            result["mac"] = mac.strip()
        return result

    lowered = text.lower()
    if "smart_config" in lowered or "smartconfig" in lowered:
        result["format"] = "smart_config_text"
    elif "smartlink" in lowered:
        result["format"] = "smartlink_text"
    elif "wifikit" in lowered or "hf-a11" in lowered or "devicelink" in lowered:
        result["format"] = "legacy_discovery_text"

    match = SERIAL_RE.search(text)
    if match:
        result["sn"] = int(match.group(1))
    match = IP_RE.search(text)
    if match:
        result["ip"] = match.group(0)
    match = MAC_RE.search(text)
    if match:
        result["mac"] = match.group(0)
    return result


def _broadcast_for_host(host: str) -> str:
    # PLAY2 tests are normally on a home /24. The directed host probe remains
    # present, so a different subnet mask does not prevent the targeted test.
    return str(ip_network(f"{IPv4Address(host)}/24", strict=False).broadcast_address)


def udp_discovery_variant(
    *,
    name: str,
    host: str,
    bind_port: int,
    send_port: int,
    messages: Iterable[bytes],
    timeout: float,
    join_multicast: bool = False,
) -> dict[str, Any]:
    messages = tuple(messages)
    destinations = (host, _broadcast_for_host(host), "255.255.255.255")
    replies: list[dict[str, Any]] = []
    seen: set[tuple[str, int | None, int]] = set()
    result: dict[str, Any] = {
        "name": name,
        "bind_port": bind_port,
        "send_port": send_port,
        "bound": False,
        "multicast_joined": False,
        "messages_sent": [message.decode("ascii", errors="replace") for message in messages],
        "reply_count": 0,
        "target_reply_found": False,
        "error": None,
        "replies": [],
    }

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    try:
        try:
            sock.bind(("", bind_port))
        except OSError as err:
            result["error"] = error_record(
                f"bind_udp_{bind_port}", err, f"could not bind UDP/{bind_port}"
            )
            return result
        result["bound"] = True

        if join_multicast:
            try:
                membership = socket.inet_aton(IGEN_MULTICAST) + socket.inet_aton("0.0.0.0")
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membership)
                result["multicast_joined"] = True
            except OSError as err:
                result["multicast_error"] = error_record(
                    "join_multicast", err, "could not join iGEN multicast group"
                )

        for cycle in range(2):
            for destination in destinations:
                for message in messages:
                    try:
                        sock.sendto(message, (destination, send_port))
                    except OSError:
                        # A directed or global broadcast can fail on some Windows
                        # interfaces while the other destinations still work.
                        continue
            if cycle == 0:
                time.sleep(0.15)

        deadline = time.monotonic() + timeout
        settle_deadline: float | None = None
        while (left := deadline - time.monotonic()) > 0:
            if settle_deadline is not None:
                left = min(left, settle_deadline - time.monotonic())
                if left <= 0:
                    break
            sock.settimeout(left)
            try:
                payload, (source, source_port) = sock.recvfrom(MAX_UDP_PACKET)
            except socket.timeout:
                break
            except OSError as err:
                result["error"] = error_record(
                    f"recv_udp_{bind_port}", err, "UDP receive failed"
                )
                break

            if payload in messages:
                continue
            parsed = parse_discovery_payload(payload)
            parsed["source"] = source
            parsed["source_port"] = source_port
            key = (source, parsed.get("sn"), len(payload))
            if key in seen:
                continue
            seen.add(key)
            replies.append(parsed)
            if source == host or parsed.get("ip") == host:
                result["target_reply_found"] = True
                if settle_deadline is None:
                    settle_deadline = time.monotonic() + 0.6
    finally:
        sock.close()

    result["reply_count"] = len(replies)
    # Keep identifiers available only in memory. Public JSON stores booleans.
    result["_private_replies"] = replies
    return result


def run_udp_discovery(host: str, timeout: float) -> list[dict[str, Any]]:
    variants = [
        udp_discovery_variant(
            name="igen_smartlink_49999",
            host=host,
            bind_port=IGEN_RECV_PORT,
            send_port=IGEN_SEND_PORT,
            messages=(IGEN_MESSAGE,),
            timeout=timeout,
            join_multicast=True,
        ),
        udp_discovery_variant(
            name="igen_smartlink_same_port_48899",
            host=host,
            bind_port=IGEN_SEND_PORT,
            send_port=IGEN_SEND_PORT,
            messages=(IGEN_MESSAGE,),
            timeout=timeout,
        ),
        udp_discovery_variant(
            name="legacy_discovery_48899",
            host=host,
            bind_port=IGEN_SEND_PORT,
            send_port=IGEN_SEND_PORT,
            messages=LEGACY_DISCOVERY_MESSAGES,
            timeout=timeout,
        ),
    ]
    return variants


def public_udp_variant(
    variant: dict[str, Any], host: str, supplied_sn: int | None
) -> dict[str, Any]:
    replies = variant.get("_private_replies", [])
    public_replies = [
        {
            "source_matches_target": reply.get("source") == host,
            "declared_ip_matches_target": reply.get("ip") == host,
            "source_port": reply.get("source_port"),
            "monitor_sn_present": reply.get("sn") is not None,
            "monitor_sn_matches_supplied": supplied_sn is not None
            and reply.get("sn") == supplied_sn,
            "mac_present": reply.get("mac") is not None,
            "payload_format": reply.get("format"),
            "payload_length": reply.get("length"),
        }
        for reply in replies
    ]
    return {
        key: value
        for key, value in variant.items()
        if key != "_private_replies" and key != "replies"
    } | {"replies": public_replies}


def resolve_sn_from_udp(variants: Iterable[dict[str, Any]], host: str) -> int | None:
    candidates: set[int] = set()
    for variant in variants:
        for reply in variant.get("_private_replies", []):
            if reply.get("source") == host or reply.get("ip") == host:
                sn = reply.get("sn")
                if isinstance(sn, int) and valid_sn(sn):
                    candidates.add(sn)
    return next(iter(candidates)) if len(candidates) == 1 else None


def port_open(host: str, port: int, timeout: float) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def http_get(
    host: str,
    port: int,
    path: str,
    timeout: float,
    *,
    tls: bool,
    auth: bool,
) -> tuple[int | None, str | None, str | None]:
    headers = {"User-Agent": "TSUN-Local-PLAY2-Probe", "Connection": "close"}
    if auth:
        headers["Authorization"] = f"Basic {HTTP_AUTH}"

    if tls:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        connection: http.client.HTTPConnection = http.client.HTTPSConnection(
            host, port, timeout=timeout, context=context
        )
    else:
        connection = http.client.HTTPConnection(host, port, timeout=timeout)

    try:
        connection.request("GET", path, headers=headers)
        response = connection.getresponse()
        status = response.status
        content_type = response.getheader("Content-Type")
        body = response.read(MAX_HTTP_PAGE + 1)
        if len(body) > MAX_HTTP_PAGE:
            return status, content_type, None
        return status, content_type, body.decode("utf-8", errors="replace")
    except (OSError, ssl.SSLError, http.client.HTTPException):
        return None, None, None
    finally:
        connection.close()


def _firmware_versions(document: str) -> list[str]:
    versions: list[str] = []
    for pattern in FW_PATTERNS:
        for match in pattern.finditer(document):
            version = match.group(1).strip().strip("\"'")
            if version and version not in versions:
                versions.append(version)
    return versions


def web_identity(host: str, timeout: float) -> dict[str, Any]:
    result: dict[str, Any] = {"firmware_versions": [], "transports": []}
    for port, tls, scheme in ((80, False, "http"), (443, True, "https")):
        reachable = port_open(host, port, min(timeout, 1.5))
        transport: dict[str, Any] = {
            "scheme": scheme,
            "port": port,
            "tcp_open": reachable,
            "pages": [],
        }
        if not reachable:
            result["transports"].append(transport)
            continue

        for path in HTTP_PATHS:
            status, content_type, document = http_get(
                host, port, path, timeout, tls=tls, auth=False
            )
            page: dict[str, Any] = {
                "path": path,
                "unauthenticated_status": status,
                "content_type": content_type,
            }
            if document is not None:
                versions = _firmware_versions(document)
                page["firmware_found"] = bool(versions)
                for version in versions:
                    if version not in result["firmware_versions"]:
                        result["firmware_versions"].append(version)

            if status in (401, 403):
                auth_status, auth_type, auth_document = http_get(
                    host, port, path, timeout, tls=tls, auth=True
                )
                page["authenticated_status"] = auth_status
                page["authenticated_content_type"] = auth_type
                if auth_document is not None:
                    versions = _firmware_versions(auth_document)
                    page["authenticated_firmware_found"] = bool(versions)
                    for version in versions:
                        if version not in result["firmware_versions"]:
                            result["firmware_versions"].append(version)
            transport["pages"].append(page)
        result["transports"].append(transport)
    return result


def checksum_ap(data: bytes) -> int:
    return sum(data) & 0xFF


def build_ap(sn: int, payload: bytes, sensor_list: int = 0) -> bytes:
    if not 0 <= sn <= 0xFFFFFFFF:
        raise ValueError("Monitor SN must fit four bytes")
    if not 0 <= sensor_list <= 0xFFFF:
        raise ValueError("sensor_list must fit two bytes")
    data = b"\x02" + sensor_list.to_bytes(2, "little") + bytes(12) + payload
    scope = (
        len(data).to_bytes(2, "little")
        + b"\x10\x45\x00\x00"
        + sn.to_bytes(4, "little")
        + data
    )
    return b"\xA5" + scope + bytes((checksum_ap(scope), 0x15))


def crc_modbus(data: bytes) -> bytes:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc.to_bytes(2, "little")


def modbus(start: int, end: int) -> bytes:
    count = end - start + 1
    if not 1 <= count <= 125:
        raise ValueError("Modbus FC03 register count must be 1..125")
    body = b"\x01\x03" + start.to_bytes(2, "big") + count.to_bytes(2, "big")
    return body + crc_modbus(body)


def crc_1511(data: bytes) -> bytes:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc.to_bytes(2, "big")


def req_1511(tag: int, function: int, start: int, end: int) -> bytes:
    count = end - start + 1
    body = (
        bytes((tag, function, 0))
        + start.to_bytes(2, "big")
        + b"\x00\x02"
        + count.to_bytes(2, "big")
    )
    return body + crc_1511(body)


def recv_exact(sock: socket.socket, count: int, stage: str) -> bytes:
    data = bytearray()
    while len(data) < count:
        try:
            chunk = sock.recv(count - len(data))
        except socket.timeout as err:
            raise RuntimeError(f"{stage}|timeout waiting for device response") from err
        except ConnectionResetError as err:
            raise RuntimeError(f"{stage}|connection reset by device") from err
        if not chunk:
            raise RuntimeError(f"{stage}|device closed the TCP stream")
        data.extend(chunk)
    return bytes(data)


def passive_tcp_probe(host: str, timeout: float) -> dict[str, Any]:
    result: dict[str, Any] = {
        "connected": False,
        "unsolicited_data_received": False,
        "error": None,
    }
    try:
        with socket.create_connection((host, TCP_PORT), timeout=timeout) as sock:
            result["connected"] = True
            sock.settimeout(min(timeout, 1.0))
            try:
                data = sock.recv(256)
            except socket.timeout:
                return result
            if data:
                result["unsolicited_data_received"] = True
                result["length"] = len(data)
                result["first_byte"] = data[0]
            else:
                result["peer_closed_without_data"] = True
    except OSError as err:
        result["error"] = error_record("passive_tcp_connect", err)
    return result


def probe_ap(
    host: str,
    sn: int,
    payload: bytes,
    sensor_list: int,
    timeout: float,
    supplied_sn: int | None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "connected": False,
        "request_sent": False,
        "response_received": False,
        "sensor_list": f"0x{sensor_list:04X}",
        "request_monitor_sn_zero": sn == 0,
        "error": None,
    }
    try:
        with socket.create_connection((host, TCP_PORT), timeout=timeout) as sock:
            result["connected"] = True
            sock.settimeout(timeout)
            sock.sendall(build_ap(sn, payload, sensor_list))
            result["request_sent"] = True
            header = recv_exact(sock, 3, "receive_header")
            result["response_received"] = True
            result["first_byte"] = header[0]
            if header[0] != 0xA5:
                result["error"] = {
                    "stage": "receive_header",
                    "type": "UnexpectedEnvelope",
                    "detail": "response does not start with 0xA5",
                }
                return result

            remaining = int.from_bytes(header[1:3], "little") + 10
            if remaining > MAX_AP_REMAINING:
                result["error"] = {
                    "stage": "receive_frame",
                    "type": "InvalidLength",
                    "detail": "implausible AP frame length",
                }
                return result
            frame = header + recv_exact(sock, remaining, "receive_frame")
            response_sn = int.from_bytes(frame[7:11], "little") if len(frame) >= 11 else 0
            result.update(
                {
                    "response_length": len(frame),
                    "ap_length_valid": len(frame)
                    == int.from_bytes(frame[1:3], "little") + 13,
                    "ap_checksum_valid": len(frame) >= 2
                    and checksum_ap(frame[1:-2]) == frame[-2],
                    "ap_end_marker": bool(frame and frame[-1] == 0x15),
                    "ap_control": int.from_bytes(frame[3:5], "little")
                    if len(frame) >= 5
                    else None,
                    "response_monitor_sn_present": valid_sn(response_sn),
                    "response_monitor_sn_matches_supplied": supplied_sn is not None
                    and response_sn == supplied_sn,
                    "ap_frame_type": frame[11] if len(frame) > 11 else None,
                    "ap_status": frame[12] if len(frame) > 12 else None,
                    "inner_length": len(frame[25:-2]) if len(frame) >= 27 else None,
                    "inner_first_byte": frame[25] if len(frame) > 27 else None,
                }
            )
            return result
    except (socket.timeout, ConnectionRefusedError, ConnectionResetError, OSError, RuntimeError) as err:
        text = str(err)
        if "|" in text:
            stage, detail = text.split("|", 1)
        else:
            stage, detail = "connect_or_send", type(err).__name__
        result["error"] = error_record(stage, err, detail)
        return result


def identity_probe_definitions() -> list[dict[str, Any]]:
    return [
        {
            "name": "1511_identity_sl0000",
            "payload": req_1511(0xA1, 0x01, 0x0BB8, 0x0BD0),
            "sensor_list": 0x0000,
        },
        {
            "name": "1511_identity_sl1511",
            "payload": req_1511(0xA1, 0x01, 0x0BB8, 0x0BD0),
            "sensor_list": 0x1511,
        },
        {
            "name": "02b0_identity_sl0000",
            "payload": modbus(0x3009, 0x301E),
            "sensor_list": 0x0000,
        },
        {
            "name": "02b0_identity_sl02b0",
            "payload": modbus(0x3009, 0x301E),
            "sensor_list": 0x02B0,
        },
        {
            "name": "1097_identity_sl1097",
            "payload": modbus(0x1100, 0x1100),
            "sensor_list": 0x1097,
        },
        {
            "name": "1097_identity_sl0000",
            "payload": modbus(0x1100, 0x1100),
            "sensor_list": 0x0000,
        },
        {
            "name": "3026_identity_sl3026",
            "payload": modbus(0x0000, 0x002C),
            "sensor_list": 0x3026,
        },
    ]


def protocol_probe_definitions() -> list[dict[str, Any]]:
    return [
        {
            "protocol": "1511",
            "variant": "sl0000_status",
            "payload": req_1511(0xA1, 0x01, 0x0BB8, 0x0BB8),
            "sensor_list": 0x0000,
            "retries": BASELINE_RETRIES,
        },
        {
            "protocol": "1511",
            "variant": "sl1511_status",
            "payload": req_1511(0xA1, 0x01, 0x0BB8, 0x0BB8),
            "sensor_list": 0x1511,
            "retries": ALT_RETRIES,
        },
        {
            "protocol": "1511",
            "variant": "sl0000_a1_21_profile",
            "payload": req_1511(0xA1, 0x21, 0x07D0, 0x07D0),
            "sensor_list": 0x0000,
            "retries": ALT_RETRIES,
        },
        {
            "protocol": "02b0",
            "variant": "sl0000_status",
            "payload": modbus(0x3000, 0x3000),
            "sensor_list": 0x0000,
            "retries": BASELINE_RETRIES,
        },
        {
            "protocol": "02b0",
            "variant": "sl02b0_status",
            "payload": modbus(0x3000, 0x3000),
            "sensor_list": 0x02B0,
            "retries": ALT_RETRIES,
        },
        {
            "protocol": "1097",
            "variant": "sl1097_status",
            "payload": modbus(0x1100, 0x1100),
            "sensor_list": 0x1097,
            "retries": BASELINE_RETRIES,
        },
        {
            "protocol": "1097",
            "variant": "sl0000_status",
            "payload": modbus(0x1100, 0x1100),
            "sensor_list": 0x0000,
            "retries": ALT_RETRIES,
        },
        {
            "protocol": "1097",
            "variant": "sl1097_info",
            "payload": modbus(0x1008, 0x100F),
            "sensor_list": 0x1097,
            "retries": ALT_RETRIES,
        },
        {
            "protocol": "3026",
            "variant": "sl3026_detection_range",
            "payload": modbus(0x0000, 0x002C),
            "sensor_list": 0x3026,
            "retries": BASELINE_RETRIES,
        },
        {
            "protocol": "3026",
            "variant": "sl0000_detection_range",
            "payload": modbus(0x0000, 0x002C),
            "sensor_list": 0x0000,
            "retries": ALT_RETRIES,
        },
    ]


def run_ap_probes(host: str, sn: int | None, timeout: float) -> dict[str, Any]:
    is_open = port_open(host, TCP_PORT, min(timeout, 1.5))
    result: dict[str, Any] = {
        "open": is_open,
        "passive": None,
        "identity_probes": [],
        "protocol_probes": [],
    }
    if not is_open:
        return result

    result["passive"] = passive_tcp_probe(host, timeout)
    print("Identity probes (Monitor SN=0):")
    for definition in identity_probe_definitions():
        probe_result = probe_ap(
            host,
            0,
            definition["payload"],
            definition["sensor_list"],
            timeout,
            sn,
        )
        record = {"probe": definition["name"], **probe_result}
        result["identity_probes"].append(record)
        err = probe_result.get("error")
        if err:
            print(f"  {definition['name']}: {err['stage']} - {err['detail']}")
        else:
            print(
                f"  {definition['name']}: response {probe_result.get('response_length')} bytes, "
                f"status={probe_result.get('ap_status')}"
            )

    if sn is None:
        print("Protocol probes skipped: Monitor SN not resolved or supplied.")
        return result

    print("Protocol variants:")
    for definition in protocol_probe_definitions():
        for attempt in range(1, int(definition["retries"]) + 1):
            probe_result = probe_ap(
                host,
                sn,
                definition["payload"],
                definition["sensor_list"],
                timeout,
                sn,
            )
            record = {
                "protocol": definition["protocol"],
                "variant": definition["variant"],
                "attempt": attempt,
                **probe_result,
            }
            result["protocol_probes"].append(record)
            err = probe_result.get("error")
            label = f"{definition['protocol']}/{definition['variant']} #{attempt}"
            if err:
                print(f"  {label}: {err['stage']} - {err['detail']}")
            else:
                print(
                    f"  {label}: response {probe_result.get('response_length')} bytes, "
                    f"checksum={probe_result.get('ap_checksum_valid')}, "
                    f"status={probe_result.get('ap_status')}"
                )
            if attempt < int(definition["retries"]):
                time.sleep(RETRY_DELAY)
    return result


def empty_document() -> dict[str, Any]:
    return {
        "format": "tsun-local-play2-diagnostic",
        "schema_version": 2,
        "metadata": {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "tool_version": TOOL_VERSION,
            "python_required": ">=3.10",
            "read_only": True,
            "writes_performed": 0,
            "privacy": {
                "ip": False,
                "monitor_sn": False,
                "mac": False,
                "raw_udp": False,
                "raw_tcp": False,
            },
        },
        "udp_discovery": {"variants": []},
        "web_identity": {"firmware_versions": [], "transports": []},
        "tcp_8899": {
            "open": False,
            "passive": None,
            "identity_probes": [],
            "protocol_probes": [],
        },
        "phase_errors": [],
    }


def write_document(document: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(document, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    if sys.version_info < (3, 10):
        print("ERROR: Python 3.10 or newer is required.", file=sys.stderr)
        return 2

    parser = argparse.ArgumentParser(
        description="Read-only Sunology PLAY2 local diagnostic (multi-variant)"
    )
    parser.add_argument("--host", required=True, help="PLAY2 IPv4 address")
    parser.add_argument(
        "--monitor-sn",
        "--serial",
        dest="sn",
        type=arg_sn,
        help="Monitor SN; optional if local discovery resolves it",
    )
    parser.add_argument(
        "--udp-timeout",
        type=arg_float,
        default=10.0,
        help="maximum wait per UDP discovery variant",
    )
    parser.add_argument(
        "--timeout", type=arg_float, default=2.5, help="TCP probe timeout"
    )
    parser.add_argument(
        "--http-timeout", type=arg_float, default=2.0, help="local web request timeout"
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        IPv4Address(args.host)
    except ValueError:
        print("ERROR: --host must be an IPv4 address.", file=sys.stderr)
        return 2

    output = args.output or Path(
        f"tsun_play2_diagnostic_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    )
    document = empty_document()

    print(f"TSUN Local PLAY2 Diagnostic v{TOOL_VERSION} · READ-ONLY")
    print("Testing local discovery variants...")

    udp_variants: list[dict[str, Any]] = []
    try:
        udp_variants = run_udp_discovery(args.host, args.udp_timeout)
        for variant in udp_variants:
            print(
                f"  {variant['name']}: replies={variant['reply_count']}, "
                f"target={'yes' if variant['target_reply_found'] else 'no'}"
            )
        document["udp_discovery"]["variants"] = [
            public_udp_variant(variant, args.host, args.sn) for variant in udp_variants
        ]
    except Exception as err:
        document["phase_errors"].append(error_record("udp_discovery", err))
        print(f"UDP discovery error: {type(err).__name__}")

    discovered_sn = resolve_sn_from_udp(udp_variants, args.host) if udp_variants else None
    sn = args.sn or discovered_sn
    document["udp_discovery"]["monitor_sn_resolved"] = sn is not None
    document["udp_discovery"]["monitor_sn_discovered"] = (
        args.sn is None and discovered_sn is not None
    )
    document["udp_discovery"]["monitor_sn_matches_supplied"] = (
        args.sn is not None and discovered_sn is not None and args.sn == discovered_sn
    )
    if discovered_sn is not None:
        if args.sn is None:
            print("Monitor SN: discovered automatically")
        else:
            print(
                "Monitor SN: local discovery "
                + ("matches supplied" if args.sn == discovered_sn else "DIFFERS from supplied")
            )

    print("Checking local web interfaces...")
    try:
        web = web_identity(args.host, args.http_timeout)
        document["web_identity"] = web
        open_web = [item["scheme"] for item in web["transports"] if item["tcp_open"]]
        print("  Web ports: " + (", ".join(open_web) if open_web else "none reachable"))
        print(
            "  Firmware: "
            + (", ".join(web["firmware_versions"]) if web["firmware_versions"] else "not found")
        )
    except Exception as err:
        document["phase_errors"].append(error_record("web_identity", err))
        print(f"Web diagnostic error: {type(err).__name__}")

    print("Checking TCP/8899 and protocol variants...")
    try:
        document["tcp_8899"] = run_ap_probes(args.host, sn, args.timeout)
        print(f"TCP/8899: {'open' if document['tcp_8899']['open'] else 'not reachable'}")
    except Exception as err:
        document["phase_errors"].append(error_record("tcp_8899", err))
        print(f"TCP diagnostic error: {type(err).__name__}")

    document["metadata"]["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
    try:
        write_document(document, output)
    except OSError as err:
        print(f"ERROR: could not write diagnostic JSON: {err}", file=sys.stderr)
        return 1

    print("Diagnostic complete · writes=0 · identifiers/raw payloads excluded from JSON")
    print(f"Output: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
