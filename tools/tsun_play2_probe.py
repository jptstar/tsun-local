#!/usr/bin/env python3
# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later
"""Read-only Sunology PLAY2 local diagnostic probe.

Mirrors the iGEN/Solarman discovery found in Sunology STREAM 3.2.2:
`smartlinkfind` -> UDP/48899, reply <- UDP/49999. It also checks known local
HTTP pages for firmware strings and records detailed behavior of the existing
TSUN Local 1511 / 02B0 / 1097 TCP/8899 read-only probes.

The JSON output excludes IP, Monitor SN, MAC and raw network payloads.
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
import sys
import time
from typing import Any

TOOL_VERSION = "1.0.0"
TCP_PORT = 8899
IGEN_SEND_PORT = 48899
IGEN_RECV_PORT = 49999
IGEN_MESSAGE = b"smartlinkfind"
HTTP_PATHS = ("/index_cn.html", "/index.html", "/status.html", "/")
HTTP_AUTH = base64.b64encode(b"admin:admin").decode("ascii")
RETRIES = 3
RETRY_DELAY = 0.4

SERIAL_RE = re.compile(r"(?<!\d)([1-9]\d{7,9})(?!\d)")
IP_RE = re.compile(r"(?<!\d)(?:25[0-5]|2[0-4]\d|1?\d?\d)(?:\.(?:25[0-5]|2[0-4]\d|1?\d?\d)){3}(?!\d)")
MAC_RE = re.compile(r"(?i)(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}")
FW_PATTERNS = (
    re.compile(r"\b(?:webdata|cover)[_-]ver\s*[:=]\s*[\"']?([A-Za-z0-9][A-Za-z0-9._-]{0,79})", re.I),
    re.compile(r"\bfirmware(?:\s*version|Version)?[^A-Za-z0-9._-]+([A-Za-z0-9][A-Za-z0-9._-]{0,79})", re.I),
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


def parse_igen(payload: bytes) -> dict[str, Any]:
    text = payload.decode("utf-8", errors="replace").strip("\x00\r\n ")
    result: dict[str, Any] = {"format": "text", "sn": None, "ip": None, "mac": None, "length": len(payload)}
    try:
        obj = json.loads(text)
    except (TypeError, ValueError):
        obj = None
    if isinstance(obj, dict):
        result["format"] = "json"
        try:
            candidate = int(str(obj.get("mid", "")).strip())
        except ValueError:
            candidate = 0
        if valid_sn(candidate):
            result["sn"] = candidate
        ip = obj.get("ip")
        mac = obj.get("mac")
        if isinstance(ip, str) and IP_RE.fullmatch(ip.strip()):
            result["ip"] = ip.strip()
        if isinstance(mac, str) and MAC_RE.fullmatch(mac.strip()):
            result["mac"] = mac.strip()
        return result
    if "smart_config" in text.lower() or "smartconfig" in text.lower():
        result["format"] = "smart_config_text"
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


def igen_discovery(host: str, timeout: float) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    broadcast = str(ip_network(f"{IPv4Address(host)}/24", strict=False).broadcast_address)
    destinations = (host, broadcast, "255.255.255.255")
    replies: list[dict[str, Any]] = []
    seen: set[tuple[str, int | None]] = set()
    meta: dict[str, Any] = {"bound_49999": False, "reply_count": 0, "error": None}
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    try:
        try:
            sock.bind(("", IGEN_RECV_PORT))
        except OSError as err:
            meta["error"] = {"stage": "bind_udp_49999", "type": type(err).__name__, "detail": "could not bind UDP/49999"}
            return replies, meta
        meta["bound_49999"] = True
        for cycle in range(2):
            for target in destinations:
                try:
                    sock.sendto(IGEN_MESSAGE, (target, IGEN_SEND_PORT))
                except OSError:
                    pass
            if cycle == 0:
                time.sleep(0.15)
        deadline = time.monotonic() + timeout
        while (left := deadline - time.monotonic()) > 0:
            sock.settimeout(left)
            try:
                payload, (source, _port) = sock.recvfrom(4096)
            except socket.timeout:
                break
            except OSError as err:
                meta["error"] = {"stage": "recv_udp_49999", "type": type(err).__name__, "detail": "UDP receive failed"}
                break
            parsed = parse_igen(payload)
            parsed["source"] = source
            key = (source, parsed["sn"])
            if key not in seen:
                seen.add(key)
                replies.append(parsed)
    finally:
        sock.close()
    meta["reply_count"] = len(replies)
    return replies, meta


def http_get(host: str, path: str, timeout: float, auth: bool) -> str | None:
    conn = http.client.HTTPConnection(host, 80, timeout=timeout)
    headers = {"User-Agent": "TSUN-Local-PLAY2-Probe", "Connection": "close"}
    if auth:
        headers["Authorization"] = f"Basic {HTTP_AUTH}"
    try:
        conn.request("GET", path, headers=headers)
        response = conn.getresponse()
        if response.status != 200:
            response.read()
            return None
        body = response.read(512 * 1024 + 1)
        if len(body) > 512 * 1024:
            return None
        return body.decode("utf-8", errors="replace")
    except (OSError, http.client.HTTPException):
        return None
    finally:
        conn.close()


def http_identity(host: str, timeout: float) -> dict[str, Any]:
    result: dict[str, Any] = {"reachable": False, "authenticated_page_seen": False, "paths": [], "firmware_versions": []}
    for path in HTTP_PATHS:
        for auth in (False, True):
            doc = http_get(host, path, timeout, auth)
            if doc is None:
                continue
            result["reachable"] = True
            result["authenticated_page_seen"] |= auth
            if path not in result["paths"]:
                result["paths"].append(path)
            for pattern in FW_PATTERNS:
                for match in pattern.finditer(doc):
                    version = match.group(1).strip().strip("\"'")
                    if version and version not in result["firmware_versions"]:
                        result["firmware_versions"].append(version)
    return result


def checksum_ap(data: bytes) -> int:
    return sum(data) & 0xFF


def build_ap(sn: int, payload: bytes, sensor_list: int = 0) -> bytes:
    data = b"\x02" + sensor_list.to_bytes(2, "little") + bytes(12) + payload
    scope = len(data).to_bytes(2, "little") + b"\x10\x45\x00\x00" + sn.to_bytes(4, "little") + data
    return b"\xA5" + scope + bytes((checksum_ap(scope), 0x15))


def crc_modbus(data: bytes) -> bytes:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc.to_bytes(2, "little")


def modbus(start: int, end: int) -> bytes:
    body = b"\x01\x03" + start.to_bytes(2, "big") + (end - start + 1).to_bytes(2, "big")
    return body + crc_modbus(body)


def crc_1511(data: bytes) -> bytes:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc.to_bytes(2, "big")


def req_1511(tag: int, function: int, start: int, end: int) -> bytes:
    body = bytes((tag, function, 0)) + start.to_bytes(2, "big") + b"\x00\x02" + (end - start + 1).to_bytes(2, "big")
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


def probe(host: str, sn: int, payload: bytes, sensor_list: int, timeout: float) -> dict[str, Any]:
    result: dict[str, Any] = {"connected": False, "request_sent": False, "error": None}
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
                result["error"] = {"stage": "receive_header", "type": "UnexpectedEnvelope", "detail": "response does not start with 0xA5"}
                return result
            remaining = int.from_bytes(header[1:3], "little") + 10
            if remaining > 65545:
                result["error"] = {"stage": "receive_frame", "type": "InvalidLength", "detail": "implausible AP frame length"}
                return result
            frame = header + recv_exact(sock, remaining, "receive_frame")
            result.update({
                "response_length": len(frame),
                "ap_length_valid": len(frame) == int.from_bytes(frame[1:3], "little") + 13,
                "ap_checksum_valid": len(frame) >= 2 and checksum_ap(frame[1:-2]) == frame[-2],
                "ap_end_marker": bool(frame and frame[-1] == 0x15),
                "ap_frame_type": frame[11] if len(frame) > 11 else None,
                "ap_status": frame[12] if len(frame) > 12 else None,
                "inner_length": len(frame[25:-2]) if len(frame) >= 27 else None,
                "inner_first_byte": frame[25] if len(frame) > 27 else None,
            })
            return result
    except (socket.timeout, ConnectionRefusedError, ConnectionResetError, OSError, RuntimeError) as err:
        text = str(err)
        stage, detail = (text.split("|", 1) + [text])[:2] if "|" in text else ("connect_or_send", type(err).__name__)
        result["error"] = {"stage": stage, "type": type(err).__name__, "detail": detail}
        return result


def tcp_open(host: str, timeout: float) -> bool:
    try:
        with socket.create_connection((host, TCP_PORT), timeout=timeout):
            return True
    except OSError:
        return False


def main() -> int:
    if sys.version_info < (3, 10):
        print("ERROR: Python 3.10 or newer is required.", file=sys.stderr)
        return 2
    parser = argparse.ArgumentParser(description="Read-only Sunology PLAY2 local diagnostic")
    parser.add_argument("--host", required=True, help="PLAY2 IPv4 address")
    parser.add_argument("--monitor-sn", "--serial", dest="sn", type=arg_sn, help="Monitor SN; optional if smartlinkfind resolves it")
    parser.add_argument("--udp-timeout", type=arg_float, default=20.0)
    parser.add_argument("--timeout", type=arg_float, default=6.0)
    parser.add_argument("--http-timeout", type=arg_float, default=2.0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        IPv4Address(args.host)
    except ValueError:
        print("ERROR: --host must be an IPv4 address.", file=sys.stderr)
        return 2

    print(f"TSUN Local PLAY2 Diagnostic v{TOOL_VERSION} · READ-ONLY")
    print(f"iGEN: '{IGEN_MESSAGE.decode()}' -> UDP/{IGEN_SEND_PORT}, replies <- UDP/{IGEN_RECV_PORT}")
    replies, igen_meta = igen_discovery(args.host, args.udp_timeout)
    target = next((r for r in replies if r["source"] == args.host or r.get("ip") == args.host), None)
    sn = args.sn or (target.get("sn") if target else None)
    print(f"iGEN replies : {len(replies)}")
    print(f"Target reply : {'yes' if target else 'no'}")
    if target and target.get("sn"):
        if args.sn:
            print(f"Monitor SN   : discovered ({'matches' if target['sn'] == args.sn else 'DIFFERS from'} supplied)")
        else:
            print("Monitor SN   : discovered automatically")
    if target and target.get("mac"):
        print("MAC          : present (redacted from JSON)")

    http = http_identity(args.host, args.http_timeout)
    print(f"HTTP local   : {'reachable' if http['reachable'] else 'not identified'}")
    print("Firmware     : " + (", ".join(http["firmware_versions"]) if http["firmware_versions"] else "not found"))
    is_open = tcp_open(args.host, min(args.timeout, 2.0))
    print(f"TCP/8899     : {'open' if is_open else 'not reachable'}")

    identity_results: list[dict[str, Any]] = []
    protocol_results: list[dict[str, Any]] = []
    if is_open:
        identities = (
            ("1511_identity", req_1511(0xA1, 0x01, 0x0BB8, 0x0BD0), 0),
            ("02b0_identity", modbus(0x3009, 0x301E), 0),
            ("1097_identity", modbus(0x1100, 0x1100), 0x1097),
        )
        print("Identity probes (SN=0):")
        for name, payload, sensor_list in identities:
            result = probe(args.host, 0, payload, sensor_list, args.timeout)
            identity_results.append({"probe": name, **result})
            err = result.get("error")
            print(f"  {name}: {err['stage']} - {err['detail']}" if err else f"  {name}: response {result.get('response_length')} bytes, status={result.get('ap_status')}")

        if sn:
            probes = {
                "1511": (req_1511(0xA1, 0x01, 0x0BB8, 0x0BB8), 0),
                "02b0": (modbus(0x3000, 0x3000), 0),
                "1097": (modbus(0x1100, 0x1100), 0x1097),
            }
            print("Protocol probes:")
            for protocol, (payload, sensor_list) in probes.items():
                for attempt in range(1, RETRIES + 1):
                    result = probe(args.host, sn, payload, sensor_list, args.timeout)
                    protocol_results.append({"protocol": protocol, "attempt": attempt, **result})
                    err = result.get("error")
                    print(f"  {protocol} #{attempt}: {err['stage']} - {err['detail']}" if err else f"  {protocol} #{attempt}: response {result.get('response_length')} bytes, checksum={result.get('ap_checksum_valid')}, status={result.get('ap_status')}")
                    if attempt < RETRIES:
                        time.sleep(RETRY_DELAY)
        else:
            print("Protocol probes skipped: Monitor SN not resolved.")

    public_replies = [{
        "source_matches_target": r["source"] == args.host,
        "declared_ip_matches_target": r.get("ip") == args.host,
        "monitor_sn_present": r.get("sn") is not None,
        "monitor_sn_matches_supplied": args.sn is not None and r.get("sn") == args.sn,
        "mac_present": r.get("mac") is not None,
        "payload_format": r["format"],
        "payload_length": r["length"],
    } for r in replies]
    document = {
        "format": "tsun-local-play2-diagnostic",
        "schema_version": 1,
        "metadata": {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "tool_version": TOOL_VERSION,
            "read_only": True,
            "research_basis": "Sunology STREAM 3.2.2 iGEN/Solarman discovery behavior",
            "privacy": {"ip": False, "monitor_sn": False, "mac": False, "raw_udp": False, "raw_tcp": False},
        },
        "igen_discovery": {**igen_meta, "target_reply_found": target is not None, "monitor_sn_resolved": sn is not None, "replies": public_replies},
        "http_identity": http,
        "tcp_8899": {"open": is_open, "identity_probes": identity_results, "protocol_probes": protocol_results},
    }
    output = args.output or Path(f"tsun_play2_diagnostic_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Diagnostic complete · writes=0 · identifiers/raw payloads excluded from JSON")
    print(f"Output: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
