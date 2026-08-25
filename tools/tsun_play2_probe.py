#!/usr/bin/env python3
# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later
"""Sunology PLAY2 / TSUN read-only local super-probe.

Python >= 3.10, standard library only.

The probe never sends inverter configuration writes, BLE/Wi-Fi provisioning,
cloud requests, Modbus write functions, or WebSocket application messages.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import http.client
from ipaddress import IPv4Address, ip_network
import json
from pathlib import Path
import re
import secrets
import socket
import ssl
import struct
import sys
import time
from typing import Any

VER = "1.3.2"
SCHEMA = 7
UDP_PORTS = (48899, 49999)
TCP_PORTS = (8899, 48899, 49999)
SMARTLINK = b"smartlinkfind"
LEGACY_DISCOVERY = (b"WIFIKIT-214028-READ", b"HF-A11ASSISTHREAD", b"devicelinkfind")
MDNS_GROUP = "224.0.0.251"
MDNS_SERVICE = "_solarhome._tcp.local."
HUB_PREFIX = "sunology-hb-"
HTTP_PATHS = ("/index_cn.html", "/index.html", "/status.html", "/")
HTTP_BASIC = base64.b64encode(b"admin:admin").decode("ascii")
SN_RE = re.compile(r"(?<!\d)([1-9]\d{7,9})(?!\d)")
IP_RE = re.compile(r"(?<!\d)(?:25[0-5]|2[0-4]\d|1?\d?\d)(?:\.(?:25[0-5]|2[0-4]\d|1?\d?\d)){3}(?!\d)")
MAC_SEP_RE = re.compile(r"(?i)(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}")
HEX12_RE = re.compile(r"(?i)(?<![0-9a-f])([0-9a-f]{12})(?![0-9a-f])")
HIGH_FLYING_OUI = "D42787"
MAX_EVIDENCE = 4096


class Log:
    def __init__(self, path: Path):
        self.f = path.open("w", encoding="utf-8", newline="\n")

    def write(self, text: str = "") -> None:
        print(text)
        self.f.write(text + "\n")
        self.f.flush()

    def close(self) -> None:
        self.f.close()


class Hosts:
    def __init__(self, supplied_host: str):
        self.data: dict[str, dict[str, Any]] = {
            supplied_host: {"alias": "host0", "reasons": ["supplied_host"], "strong": False, "confirmed_logger": False}
        }

    def add(self, ip: str | None, reason: str, strong: bool = False) -> None:
        if not ip:
            return
        try:
            IPv4Address(ip)
        except ValueError:
            return
        if ip not in self.data and len(self.data) < 8:
            self.data[ip] = {"alias": f"candidate{len(self.data)}", "reasons": [], "strong": False, "confirmed_logger": False}
        item = self.data.get(ip)
        if not item:
            return
        if reason not in item["reasons"]:
            item["reasons"].append(reason)
        item["strong"] = bool(item["strong"] or strong)

    def confirm(self, ip: str, reason: str) -> None:
        self.add(ip, reason, True)
        self.data[ip]["confirmed_logger"] = True

    def alias(self, ip: str | None) -> str | None:
        return self.data.get(ip or "", {}).get("alias", "other-local-host") if ip else None

    def public(self) -> list[dict[str, Any]]:
        return [
            {"alias": v["alias"], "reasons": v["reasons"], "strong": v["strong"], "confirmed_logger": v["confirmed_logger"]}
            for v in self.data.values()
        ]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def error(stage: str, exc: BaseException) -> dict[str, str]:
    return {"stage": stage, "type": type(exc).__name__, "detail": str(exc) or type(exc).__name__}


def crc16_modbus(data: bytes) -> int:
    crc = 0xFFFF
    for value in data:
        crc ^= value
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc & 0xFFFF


def normalize_mac(value: str, *, allow_compact: bool = False) -> str | None:
    text = value.strip()
    if not allow_compact and not MAC_SEP_RE.fullmatch(text):
        return None
    compact = re.sub(r"[^0-9A-Fa-f]", "", text)
    if len(compact) != 12 or not re.fullmatch(r"[0-9A-Fa-f]{12}", compact):
        return None
    compact = compact.upper()
    return ":".join(compact[i : i + 2] for i in range(0, 12, 2))


def compact_mac_candidate(value: str) -> str | None:
    text = value.strip().upper()
    return text if HEX12_RE.fullmatch(text) else None


def mac_suffix(mac: str | None) -> str | None:
    if not mac:
        return None
    compact = re.sub(r"[^0-9A-Fa-f]", "", mac).upper()
    return f"{compact[-4:-2]}:{compact[-2:]}" if len(compact) == 12 else None


def vendor_hint(compact: str | None) -> str | None:
    return "High-Flying (OUI D4:27:87)" if compact and compact.upper().startswith(HIGH_FLYING_OUI) else None


def redact_bytes(data: bytes, supplied_sn: int | None, ips: list[str]) -> bytes:
    out = bytes(data)
    if supplied_sn:
        for value in (str(supplied_sn).encode(), supplied_sn.to_bytes(4, "little"), supplied_sn.to_bytes(4, "big")):
            out = out.replace(value, b"*" * len(value))
    for ip in ips:
        out = out.replace(ip.encode(), b"*" * len(ip))
        try:
            out = out.replace(socket.inet_aton(ip), b"****")
        except OSError:
            pass
    text = out.decode("latin1", "ignore")
    for regex in (MAC_SEP_RE, HEX12_RE):
        for match in list(regex.finditer(text)):
            raw = match.group(0).encode("latin1")
            out = out.replace(raw, b"*" * len(raw))
    return out


def evidence(data: bytes, supplied_sn: int | None, ips: list[str]) -> dict[str, Any]:
    redacted = redact_bytes(data, supplied_sn, ips)
    cap = redacted[:MAX_EVIDENCE]
    return {
        "length": len(data),
        "sha256": sha256(data),
        "redacted_hex": cap.hex(),
        "redacted_ascii": "".join(chr(v) if 32 <= v < 127 else f"\\x{v:02x}" for v in cap),
        "complete": len(data) <= MAX_EVIDENCE,
    }


def classify_text_field(value: str) -> dict[str, Any]:
    text = value.strip()
    result: dict[str, Any] = {"length": len(text), "class": "text"}
    if IP_RE.fullmatch(text):
        result["class"] = "ipv4"
    elif (mac := normalize_mac(text)):
        result.update({"class": "mac", "suffix": mac_suffix(mac)})
    elif (candidate := compact_mac_candidate(text)):
        result.update({"class": "logger_module_mac_candidate_hex12", "suffix": mac_suffix(candidate), "vendor_hint": vendor_hint(candidate)})
    elif text.isdigit() and 8 <= len(text) <= 10:
        result["class"] = "serial_like"
    return result


def parse_udp(data: bytes) -> dict[str, Any]:
    text = data.decode("utf-8", "replace").strip("\x00\r\n ")
    out: dict[str, Any] = {"text": text, "format": "text", "sn": None, "ip": None, "mac": None, "logger_module_mac_candidate": None}
    try:
        obj = json.loads(text)
    except Exception:
        obj = None
    if isinstance(obj, dict):
        out["format"] = "json"
        for key in ("mid", "sn", "serial", "loggerSn", "monitorSn"):
            try:
                value = int(str(obj.get(key, "")))
            except Exception:
                continue
            if 0 < value <= 0xFFFFFFFF:
                out["sn"] = value
                break
        if isinstance(obj.get("ip"), str) and IP_RE.fullmatch(obj["ip"].strip()):
            out["ip"] = obj["ip"].strip()
        if isinstance(obj.get("mac"), str):
            out["mac"] = normalize_mac(obj["mac"], allow_compact=True)
        return out
    lower = text.lower()
    if "smart_config" in lower or "smartconfig" in lower:
        out["format"] = "smart_config_text"
    elif "smartlink" in lower:
        out["format"] = "smartlink_text"
    if m := SN_RE.search(text):
        out["sn"] = int(m.group(1))
    if m := IP_RE.search(text):
        out["ip"] = m.group(0)
    if m := MAC_SEP_RE.search(text):
        out["mac"] = normalize_mac(m.group(0))
    if m := HEX12_RE.search(text):
        out["logger_module_mac_candidate"] = compact_mac_candidate(m.group(1))
    fields = [part.strip() for part in text.split(",")]
    if len(fields) >= 2:
        classes = [classify_text_field(part) for part in fields]
        out["csv_field_count"] = len(fields)
        out["csv_classes"] = classes
        for part, cls in zip(fields, classes):
            if cls["class"] == "ipv4" and not out["ip"]:
                out["ip"] = part
            elif cls["class"] == "mac" and not out["mac"]:
                out["mac"] = normalize_mac(part)
            elif cls["class"] == "logger_module_mac_candidate_hex12" and not out["logger_module_mac_candidate"]:
                out["logger_module_mac_candidate"] = compact_mac_candidate(part)
            elif cls["class"] == "serial_like" and out["sn"] is None:
                out["sn"] = int(part)
    return out


def smart_config_fields(text: str, supplied_sn: int | None) -> dict[str, Any] | None:
    lower = text.lower()
    pos, prefix = lower.find("smart_config"), "smart_config"
    if pos < 0:
        pos, prefix = lower.find("smartconfig"), "smartconfig"
    if pos < 0:
        return None
    tail = text[pos + len(prefix) :].strip("\x00\r\n #")
    fields = tail.split("##") if tail else []
    return {
        "prefix": prefix,
        "separator": "##",
        "field_count": len(fields),
        "fields": [
            {"index": i, **classify_text_field(field), "matches_supplied_sn": bool(supplied_sn and field == str(supplied_sn))}
            for i, field in enumerate(fields)
        ],
    }


def udp_variant(host: str, bind_port: int, send_port: int, messages: tuple[bytes, ...], timeout: float) -> dict[str, Any]:
    result: dict[str, Any] = {"bind_port": bind_port, "send_port": send_port, "messages": [m.decode("ascii") for m in messages], "bound": False, "replies": [], "error": None}
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    try:
        try:
            sock.bind(("", bind_port))
            result["bound"] = True
        except OSError as exc:
            result["error"] = error("bind", exc)
            return result
        destinations = (host, str(ip_network(f"{host}/24", strict=False).broadcast_address), "255.255.255.255")
        for destination in destinations:
            for message in messages:
                try:
                    sock.sendto(message, (destination, send_port))
                except OSError:
                    pass
        deadline = time.monotonic() + timeout
        seen: set[tuple[str, int, str]] = set()
        while (left := deadline - time.monotonic()) > 0:
            sock.settimeout(left)
            try:
                payload, (source, source_port) = sock.recvfrom(8192)
            except socket.timeout:
                break
            except OSError as exc:
                result["error"] = error("recv", exc)
                break
            if payload in messages:
                continue
            key = (source, source_port, sha256(payload))
            if key in seen:
                continue
            seen.add(key)
            result["replies"].append({"_source": source, "source_port": source_port, "_raw": payload, "_parsed": parse_udp(payload)})
    finally:
        sock.close()
    return result


def udp_all(host: str, timeout: float) -> list[dict[str, Any]]:
    out = []
    for bind_port in UDP_PORTS:
        for send_port in UDP_PORTS:
            for name, messages in (("smartlink", (SMARTLINK,)), ("legacy", LEGACY_DISCOVERY)):
                item = udp_variant(host, bind_port, send_port, messages, timeout)
                item["name"] = f"udp_{bind_port}_to_{send_port}_{name}"
                out.append(item)
    return out


def dns_name(name: str) -> bytes:
    return b"".join(bytes((len(label),)) + label.encode() for label in name.rstrip(".").split(".")) + b"\0"


def read_dns_name(data: bytes, offset: int, seen: set[int] | None = None) -> tuple[str, int]:
    seen = set() if seen is None else seen
    labels, next_offset = [], None
    while True:
        length = data[offset]
        if length == 0:
            return ".".join(labels) + ".", next_offset if next_offset is not None else offset + 1
        if length & 0xC0 == 0xC0:
            pointer = ((length & 0x3F) << 8) | data[offset + 1]
            if pointer in seen:
                raise ValueError("dns pointer loop")
            seen.add(pointer)
            next_offset = offset + 2 if next_offset is None else next_offset
            offset = pointer
            continue
        offset += 1
        labels.append(data[offset : offset + length].decode("utf8", "replace"))
        offset += length


def mdns(timeout: float) -> dict[str, Any]:
    query = struct.pack("!HHHHHH", 0, 0, 1, 0, 0, 0) + dns_name(MDNS_SERVICE) + struct.pack("!HH", 12, 1)
    packets, errors = [], []
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        try:
            sock.bind(("", 5353))
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, socket.inet_aton(MDNS_GROUP) + socket.inet_aton("0.0.0.0"))
            mode = "5353_multicast"
        except OSError as exc:
            errors.append(error("mdns_bind", exc))
            sock.close()
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind(("", 0))
            mode = "ephemeral"
        sock.sendto(query, (MDNS_GROUP, 5353))
        deadline = time.monotonic() + timeout
        while (left := deadline - time.monotonic()) > 0:
            sock.settimeout(left)
            try:
                payload, (source, source_port) = sock.recvfrom(9000)
            except socket.timeout:
                break
            packets.append((payload, source, source_port))
    finally:
        sock.close()
    srv, addresses, ptr, txt = {}, {}, set(), {}
    for payload, _, _ in packets:
        try:
            _, _, qd, an, ns, ar = struct.unpack_from("!HHHHHH", payload, 0)
            offset = 12
            for _ in range(qd):
                _, offset = read_dns_name(payload, offset)
                offset += 4
            for _ in range(an + ns + ar):
                name, offset = read_dns_name(payload, offset)
                typ, _, _, length = struct.unpack_from("!HHIH", payload, offset)
                offset += 10
                start, end = offset, offset + length
                if typ == 12:
                    target, _ = read_dns_name(payload, start)
                    ptr.add(target)
                elif typ == 33 and length >= 6:
                    _, _, port = struct.unpack_from("!HHH", payload, start)
                    target, _ = read_dns_name(payload, start + 6)
                    srv[name] = (port, target)
                elif typ == 1 and length == 4:
                    addresses.setdefault(name, set()).add(socket.inet_ntoa(payload[start:end]))
                elif typ == 16:
                    cursor, values = start, []
                    while cursor < end:
                        n = payload[cursor]
                        cursor += 1
                        values.append(payload[cursor : cursor + n].decode("utf8", "replace"))
                        cursor += n
                    txt[name] = values
                offset = end
        except Exception:
            continue
    services = []
    for instance in sorted(ptr | set(srv)):
        port, target = srv.get(instance, (None, None))
        services.append({"instance": instance, "port": port, "addresses": sorted(addresses.get(target, set())) if target else [], "txt": txt.get(instance, []), "hub_name": instance.lower().startswith(HUB_PREFIX)})
    return {"mode": mode, "packet_count": len(packets), "services": services[:8], "errors": errors}


def websocket(host: str, port: int, timeout: float, listen: float, supplied_sn: int | None, ips: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {"port": port, "connected": False, "events": [], "errors": []}
    for origin in (None, "http://localhost", "capacitor://localhost"):
        key = base64.b64encode(secrets.token_bytes(16)).decode()
        headers = ["GET /ws HTTP/1.1", f"Host: {host}:{port}", "Upgrade: websocket", "Connection: Upgrade", f"Sec-WebSocket-Key: {key}", "Sec-WebSocket-Version: 13"]
        if origin:
            headers.append(f"Origin: {origin}")
        try:
            with socket.create_connection((host, port), timeout=timeout) as sock:
                sock.settimeout(timeout)
                sock.sendall(("\r\n".join(headers) + "\r\n\r\n").encode())
                response = b""
                while b"\r\n\r\n" not in response and len(response) < 16384:
                    response += sock.recv(2048)
                status = response.decode("latin1", "replace").split("\r\n", 1)[0]
                if " 101 " not in f" {status} ":
                    result["errors"].append({"origin": origin, "status": status})
                    continue
                result.update({"connected": True, "origin": origin, "status": status})
                deadline = time.monotonic() + listen
                while (left := deadline - time.monotonic()) > 0 and len(result["events"]) < 16:
                    sock.settimeout(min(1.0, left))
                    try:
                        head = sock.recv(2)
                    except socket.timeout:
                        continue
                    if len(head) < 2:
                        break
                    opcode, length = head[0] & 15, head[1] & 127
                    if length == 126:
                        length = int.from_bytes(sock.recv(2), "big")
                    elif length == 127:
                        length = int.from_bytes(sock.recv(8), "big")
                    if length > 16384:
                        break
                    mask = sock.recv(4) if head[1] & 128 else b""
                    payload = b""
                    while len(payload) < length:
                        chunk = sock.recv(length - len(payload))
                        if not chunk:
                            break
                        payload += chunk
                    if mask:
                        payload = bytes(v ^ mask[i % 4] for i, v in enumerate(payload))
                    result["events"].append({"opcode": opcode, "payload": evidence(payload, supplied_sn, ips)})
                    if opcode == 8:
                        break
                return result
        except Exception as exc:
            result["errors"].append(error("websocket", exc))
    return result


def port_open(host: str, port: int, timeout: float) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def http_get(host: str, port: int, tls: bool, path: str, timeout: float, auth: bool) -> dict[str, Any]:
    headers = {"Connection": "close", "User-Agent": "TSUN-Local-PLAY2-Probe", "Cache-Control": "no-cache"}
    if auth:
        headers["Authorization"] = f"Basic {HTTP_BASIC}"
    if tls:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        conn: http.client.HTTPConnection = http.client.HTTPSConnection(host, port, timeout=timeout, context=ctx)
    else:
        conn = http.client.HTTPConnection(host, port, timeout=timeout)
    try:
        conn.request("GET", path, headers=headers)
        rsp = conn.getresponse()
        body = rsp.read(524289)
        return {"status": rsp.status, "server": rsp.getheader("Server"), "content_type": rsp.getheader("Content-Type"), "www_authenticate": rsp.getheader("WWW-Authenticate"), "body": body}
    finally:
        conn.close()


def http_identity(host: str, timeout: float, supplied_sn: int | None, ips: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {"transports": []}
    for port, tls in ((80, False), (443, True)):
        transport = {"scheme": "https" if tls else "http", "open": port_open(host, port, min(timeout, 1.2)), "pages": []}
        if transport["open"]:
            for path in HTTP_PATHS:
                page: dict[str, Any] = {"path": path}
                try:
                    initial = http_get(host, port, tls, path, timeout, False)
                    page.update({"status": initial["status"], "server": initial["server"], "content_type": initial["content_type"], "www_authenticate": initial["www_authenticate"], "body": evidence(initial["body"], supplied_sn, ips)})
                    challenge = initial.get("www_authenticate") or ""
                    if initial["status"] == 401 and (not challenge or "basic" in challenge.lower()):
                        auth = http_get(host, port, tls, path, timeout, True)
                        page["basic_admin_admin"] = {"attempted_read_only": True, "status": auth["status"], "server": auth["server"], "content_type": auth["content_type"], "body": evidence(auth["body"], supplied_sn, ips)}
                except Exception as exc:
                    page["error"] = error("http", exc)
                transport["pages"].append(page)
        result["transports"].append(transport)
    return result


def modbus_rtu_read(address: int, count: int = 1, function: int = 3) -> bytes:
    body = b"\x01" + bytes((function,)) + address.to_bytes(2, "big") + count.to_bytes(2, "big")
    return body + crc16_modbus(body).to_bytes(2, "little")


def native_1511_read(tag: int, function: int, start: int, end: int) -> bytes:
    count = end - start + 1
    body = bytes((tag, function, 0)) + start.to_bytes(2, "big") + b"\x00\x02" + count.to_bytes(2, "big")
    return body + crc16_modbus(body).to_bytes(2, "big")


def v5_request(logger_sn: int, payload: bytes, sensor_list: int = 0, sequence: int = 0) -> bytes:
    data = b"\x02" + sensor_list.to_bytes(2, "little") + bytes(12) + payload
    core = len(data).to_bytes(2, "little") + b"\x10\x45" + sequence.to_bytes(2, "little") + logger_sn.to_bytes(4, "little") + data
    return b"\xA5" + core + bytes((sum(core) & 0xFF, 0x15))


def v4_historical_read_request(logger_sn: int) -> bytes:
    """Historical iGEN/Solarman V4 command 0x0001: read inverter data."""
    sn = logger_sn.to_bytes(4, "little")
    body = b"\x02\x41\xB1" + sn + sn + b"\x01\x00"
    return b"\x68" + body + bytes((sum(body) & 0xFF, 0x16))


def core_probe_matrix(sn: int | None) -> list[tuple[str, bytes, dict[str, Any]]]:
    probes = []
    logger_sns = [0] + ([sn] if sn else [])
    tests = (
        ("native1511_sl0000", native_1511_read(0xA1, 0x01, 0x0BB8, 0x0BD0), 0x0000, "native1511"),
        ("native1511_sl1511", native_1511_read(0xA1, 0x01, 0x0BB8, 0x0BD0), 0x1511, "native1511"),
        ("native1511_sl02b0", native_1511_read(0xA1, 0x01, 0x0BB8, 0x0BD0), 0x02B0, "native1511"),
        ("modbus03_3000_sl02b0", modbus_rtu_read(0x3000, 1, 3), 0x02B0, "modbus_rtu"),
        ("modbus04_3000_sl02b0", modbus_rtu_read(0x3000, 1, 4), 0x02B0, "modbus_rtu"),
        ("modbus03_1100_sl1097", modbus_rtu_read(0x1100, 1, 3), 0x1097, "modbus_rtu"),
        ("modbus04_1100_sl1097", modbus_rtu_read(0x1100, 1, 4), 0x1097, "modbus_rtu"),
        ("modbus03_0000_sl3026", modbus_rtu_read(0x0000, 1, 3), 0x3026, "modbus_rtu"),
    )
    for logger_sn in logger_sns:
        who = "sn0" if logger_sn == 0 else "snsupplied"
        for i, (name, payload, sensor_list, inner_kind) in enumerate(tests):
            seq = 0x40 + i
            probes.append((f"v5_{name}_{who}", v5_request(int(logger_sn), payload, sensor_list, seq), {"kind": "solarman_v5_request", "inner_kind": inner_kind, "sensor_list": f"0x{sensor_list:04X}", "sn_zero": logger_sn == 0, "request_sequence_low": seq}))
    return probes


def session_probe_matrix(sn: int | None) -> list[tuple[str, bytes, dict[str, Any]]]:
    if not sn:
        return []
    tests = (
        ("session_native1511_sl1511", native_1511_read(0xA1, 0x01, 0x0BB8, 0x0BD0), 0x1511, "native1511"),
        ("session_modbus03_3000_sl02b0", modbus_rtu_read(0x3000, 1, 3), 0x02B0, "modbus_rtu"),
        ("session_modbus03_1100_sl1097", modbus_rtu_read(0x1100, 1, 3), 0x1097, "modbus_rtu"),
        ("session_modbus03_0000_sl3026", modbus_rtu_read(0x0000, 1, 3), 0x3026, "modbus_rtu"),
    )
    return [
        (name, v5_request(sn, payload, sensor_list, 0x70 + i), {"kind": "solarman_v5_same_connection", "inner_kind": kind, "sensor_list": f"0x{sensor_list:04X}", "request_sequence_low": 0x70 + i})
        for i, (name, payload, sensor_list, kind) in enumerate(tests)
    ]


def split_v5_frames(data: bytes) -> tuple[list[bytes], bytes]:
    frames, offset = [], 0
    while offset < len(data):
        if data[offset : offset + 1] != b"\xA5" or offset + 3 > len(data):
            return frames, data[offset:]
        declared = int.from_bytes(data[offset + 1 : offset + 3], "little")
        total = 13 + declared
        if offset + total > len(data):
            return frames, data[offset:]
        frame = data[offset : offset + total]
        if frame[-1] != 0x15:
            return frames, data[offset:]
        frames.append(frame)
        offset += total
    return frames, b""


def decode_embedded(payload: bytes, supplied_sn: int | None, ips: list[str]) -> dict[str, Any]:
    out: dict[str, Any] = {"length": len(payload), "evidence": evidence(payload, supplied_sn, ips)}
    if not payload:
        out["class"] = "empty"
    elif len(payload) == 2:
        out.update({"class": "short_response_marker", "marker_hex": payload.hex(), "marker_le": int.from_bytes(payload, "little"), "note": "Too short to be normal Modbus RTU data; kept as an unknown Solarman/logger marker."})
    elif len(payload) >= 5:
        rtu_valid = crc16_modbus(payload[:-2]) == int.from_bytes(payload[-2:], "little")
        native_valid = crc16_modbus(payload[:-2]) == int.from_bytes(payload[-2:], "big")
        out.update({"rtu_crc_candidate_valid": rtu_valid, "native_crc_be_candidate_valid": native_valid})
        if rtu_valid:
            fn = payload[1]
            out.update({"class": "modbus_rtu", "unit": payload[0], "function": fn})
            if fn & 0x80:
                out["exception_code"] = payload[2]
            elif fn in (3, 4):
                data = payload[3:-2]
                out["byte_count"] = payload[2]
                out["byte_count_valid"] = payload[2] == len(data)
                if out["byte_count_valid"] and len(data) % 2 == 0:
                    out["registers"] = [int.from_bytes(data[i:i+2], "big") for i in range(0, len(data), 2)]
        elif native_valid or payload[0] in (0xA1, 0xA2, 0xA3, 0xA4):
            out.update({"class": "native_tsunnative_candidate", "tag": f"0x{payload[0]:02X}", "function": payload[1] if len(payload) > 1 else None})
        else:
            out["class"] = "unknown_protocol_payload"
    else:
        out["class"] = "unknown_protocol_payload"
    return out


def decode_v5(frame: bytes, supplied_sn: int | None, ips: list[str], meta: dict[str, Any] | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {"looks_like_v5": False, "valid_start": False, "valid_end": False, "length_valid": False, "checksum_valid": False}
    if len(frame) < 13:
        out["reason"] = "too_short"
        return out
    declared = int.from_bytes(frame[1:3], "little")
    control = int.from_bytes(frame[3:5], "little")
    seq = int.from_bytes(frame[5:7], "little")
    logger_sn = int.from_bytes(frame[7:11], "little")
    out.update({
        "looks_like_v5": frame[0] == 0xA5,
        "valid_start": frame[0] == 0xA5,
        "valid_end": frame[-1] == 0x15,
        "declared_payload_length": declared,
        "actual_total_length": len(frame),
        "expected_total_length": 13 + declared,
        "length_valid": len(frame) == 13 + declared,
        "control": f"0x{control:04X}",
        "control_name": {0x4510: "REQUEST", 0x1510: "RESPONSE", 0x4710: "HEARTBEAT", 0x4810: "REPORT"}.get(control, "UNKNOWN"),
        "sequence": seq,
        "sequence_low": seq & 0xFF,
        "logger_sn_present": logger_sn != 0,
        "logger_sn_matches_supplied": bool(supplied_sn and logger_sn == supplied_sn),
        "checksum_valid": (sum(frame[1:-2]) & 0xFF) == frame[-2],
    })
    if meta and isinstance(meta.get("request_sequence_low"), int):
        out["request_sequence_low"] = meta["request_sequence_low"]
        out["sequence_low_echo_matches"] = (seq & 0xFF) == meta["request_sequence_low"]
    if out["length_valid"] and control == 0x1510 and declared >= 14:
        payload = frame[11 : 11 + declared]
        total_working = int.from_bytes(payload[2:6], "little")
        offset_time = int.from_bytes(payload[10:14], "little")
        acq = total_working + offset_time
        out["response"] = {
            "frame_type": payload[0],
            "status": payload[1],
            "total_working_time_s": total_working,
            "power_on_time_s": int.from_bytes(payload[6:10], "little"),
            "offset_time_s": offset_time,
            "acquisition_timestamp_utc": datetime.fromtimestamp(acq, timezone.utc).isoformat() if 946684800 <= acq <= 4102444800 else None,
            "embedded": decode_embedded(payload[14:], supplied_sn, ips),
        }
    return out


def split_v4_frames(data: bytes) -> tuple[list[bytes], bytes]:
    frames, offset = [], 0
    while offset < len(data):
        if data[offset : offset + 1] != b"\x68" or offset + 2 > len(data):
            return frames, data[offset:]
        total = data[offset + 1] + 14
        if offset + total > len(data):
            return frames, data[offset:]
        frame = data[offset : offset + total]
        if frame[-1] != 0x16:
            return frames, data[offset:]
        frames.append(frame)
        offset += total
    return frames, b""


def decode_v4(frame: bytes, supplied_sn: int | None, ips: list[str]) -> dict[str, Any]:
    out: dict[str, Any] = {"looks_like_v4": False}
    if len(frame) < 14 or frame[0] != 0x68:
        return out
    dfl = frame[1]
    logger_sn = int.from_bytes(frame[4:8], "little")
    payload = frame[12 : 12 + dfl]
    out.update({
        "looks_like_v4": True,
        "data_field_length": dfl,
        "length_valid": len(frame) == dfl + 14,
        "control_hex": frame[2:4].hex(),
        "logger_sn_matches_supplied": bool(supplied_sn and logger_sn == supplied_sn),
        "checksum_valid": (sum(frame[1:-2]) & 0xFF) == frame[-2],
        "payload": evidence(payload, supplied_sn, ips),
        "payload_class": "unknown",
    })
    if payload.startswith(b"NO INVERTER DATA"):
        out["payload_class"] = "no_inverter_data"
    elif payload.startswith(b"DATA SEND IS OK"):
        out["payload_class"] = "data_send_ok"
    elif len(payload) >= 69 and payload[:3] == b"\x81\x02\x01":
        u16 = lambda o: int.from_bytes(payload[o:o+2], "big")
        u32 = lambda o: int.from_bytes(payload[o:o+4], "big")
        out["payload_class"] = "historical_v4_inverter_telemetry_candidate"
        out["telemetry_candidate"] = {
            "temperature_c": u16(19) / 10,
            "pv_voltage_v": [u16(21) / 10, u16(23) / 10, u16(25) / 10],
            "pv_current_a": [u16(27) / 10, u16(29) / 10, u16(31) / 10],
            "ac_current_a": [u16(33) / 10, u16(35) / 10, u16(37) / 10],
            "ac_voltage_v": [u16(39) / 10, u16(41) / 10, u16(43) / 10],
            "ac_frequency_hz": [u16(45) / 100, u16(49) / 100, u16(53) / 100],
            "ac_power_w": [u16(47), u16(51), u16(55)],
            "energy_today_kwh": u16(57) / 10,
            "energy_total_kwh": u32(59) / 10,
            "hours_total": u32(63),
            "mode": u16(67),
            "note": "Decoded only because the response matches the documented historical V4 0x81 0x02 0x01 layout.",
        }
    return out


def recv_until_gap(sock: socket.socket, timeout: float, gap: float = 0.35) -> bytes:
    data = b""
    sock.settimeout(timeout)
    try:
        while len(data) < 65536:
            chunk = sock.recv(min(4096, 65536 - len(data)))
            if not chunk:
                break
            data += chunk
            sock.settimeout(gap)
    except socket.timeout:
        pass
    return data


def decode_received(data: bytes, supplied_sn: int | None, ips: list[str], meta: dict[str, Any] | None) -> dict[str, Any]:
    v5, v5_rem = split_v5_frames(data)
    v4, v4_rem = split_v4_frames(data)
    return {
        "response": evidence(data, supplied_sn, ips),
        "v5_frame_count": len(v5),
        "v5_frames": [decode_v5(frame, supplied_sn, ips, meta) for frame in v5],
        "v4_frame_count": len(v4),
        "v4_frames": [decode_v4(frame, supplied_sn, ips) for frame in v4],
        "unparsed_remainder": evidence(v5_rem, supplied_sn, ips) if v5_rem and not v4 else (evidence(v4_rem, supplied_sn, ips) if v4_rem and not v5 else None),
    }


def tcp_exchange(host: str, port: int, name: str, request: bytes, meta: dict[str, Any], timeout: float, supplied_sn: int | None, ips: list[str]) -> dict[str, Any]:
    out: dict[str, Any] = {"name": name, "meta": meta, "connected": False, "sent": False, "response_length": 0}
    start = time.monotonic()
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            out["connected"] = True
            sock.sendall(request)
            out["sent"] = True
            rsp = recv_until_gap(sock, timeout)
            out["response_length"] = len(rsp)
            out["outcome"] = "bytes" if rsp else "no_bytes"
            if rsp:
                out.update(decode_received(rsp, supplied_sn, ips, meta))
    except Exception as exc:
        out["outcome"] = "error"
        out["error"] = error("tcp", exc)
    out["elapsed_ms"] = round((time.monotonic() - start) * 1000, 1)
    return out


def tcp_same_connection_session(host: str, timeout: float, supplied_sn: int | None, ips: list[str]) -> dict[str, Any]:
    session: dict[str, Any] = {"enabled": bool(supplied_sn), "connected": False, "steps": []}
    if not supplied_sn:
        return session
    try:
        with socket.create_connection((host, 8899), timeout=timeout) as sock:
            session["connected"] = True
            for name, request, meta in session_probe_matrix(supplied_sn):
                step = {"name": name, "meta": meta, "sent": False}
                try:
                    sock.sendall(request)
                    step["sent"] = True
                    rsp = recv_until_gap(sock, timeout)
                    step["response_length"] = len(rsp)
                    step["outcome"] = "bytes" if rsp else "no_bytes"
                    if rsp:
                        step.update(decode_received(rsp, supplied_sn, ips, meta))
                except Exception as exc:
                    step["outcome"] = "error"
                    step["error"] = error("tcp_session", exc)
                session["steps"].append(step)
                time.sleep(0.12)
    except Exception as exc:
        session["error"] = error("tcp_session_connect", exc)
    return session


def tcp_port(host: str, port: int, timeout: float, supplied_sn: int | None, ips: list[str], full: bool, v4_allowed: bool) -> dict[str, Any]:
    out: dict[str, Any] = {"port": port, "open": port_open(host, port, min(timeout, 1.2)), "passive": None, "probes": [], "same_connection_session": None, "historical_v4_read": None}
    if not out["open"]:
        return out
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            passive = recv_until_gap(sock, min(timeout, 1.0), 0.2)
            out["passive"] = {"received": bool(passive), **(decode_received(passive, supplied_sn, ips, None) if passive else {})}
    except Exception as exc:
        out["passive"] = {"error": error("passive", exc)}
    probes = core_probe_matrix(supplied_sn)
    if not full:
        probes = probes[:4]
    for name, request, meta in probes:
        out["probes"].append(tcp_exchange(host, port, name, request, meta, timeout, supplied_sn, ips))
        time.sleep(0.08)
    if full and port == 8899:
        out["same_connection_session"] = tcp_same_connection_session(host, timeout, supplied_sn, ips)
    if port == 8899 and v4_allowed and supplied_sn:
        out["historical_v4_read"] = tcp_exchange(host, port, "historical_solarman_v4_read_0001", v4_historical_read_request(supplied_sn), {"kind": "historical_solarman_v4_read", "command": "0x0001", "read_only": True}, timeout, supplied_sn, ips)
    return out


def iter_v5(document: dict[str, Any]):
    for transport in document.get("tcp", []):
        for probe in transport.get("probes", []):
            for frame in probe.get("v5_frames", []):
                yield probe.get("name"), frame
        for step in (transport.get("same_connection_session") or {}).get("steps", []):
            for frame in step.get("v5_frames", []):
                yield step.get("name"), frame


def build_analysis(document: dict[str, Any], hosts: Hosts) -> dict[str, Any]:
    markers, markers_by_probe = {}, {}
    valid_v5 = modbus_payloads = native_payloads = unknown_payloads = 0
    seq_match = seq_mismatch = 0
    for probe_name, frame in iter_v5(document):
        if frame.get("control") == "0x1510" and frame.get("checksum_valid") and frame.get("length_valid"):
            valid_v5 += 1
        if frame.get("sequence_low_echo_matches") is True:
            seq_match += 1
        elif frame.get("sequence_low_echo_matches") is False:
            seq_mismatch += 1
        cls = ((frame.get("response") or {}).get("embedded") or {}).get("class")
        if cls == "short_response_marker":
            marker = frame["response"]["embedded"].get("marker_hex", "")
            markers[marker] = markers.get(marker, 0) + 1
            pb = markers_by_probe.setdefault(probe_name or "unknown", {})
            pb[marker] = pb.get(marker, 0) + 1
        elif cls == "modbus_rtu":
            modbus_payloads += 1
        elif cls == "native_tsunnative_candidate":
            native_payloads += 1
        elif cls == "unknown_protocol_payload":
            unknown_payloads += 1
    mac_suffixes, module_mac_suffixes, vendor_hints = set(), set(), set()
    for variant in document.get("udp", []):
        for reply in variant.get("replies", []):
            if reply.get("mac_suffix"):
                mac_suffixes.add(reply["mac_suffix"])
            if reply.get("logger_module_mac_candidate_suffix"):
                module_mac_suffixes.add(reply["logger_module_mac_candidate_suffix"])
            if reply.get("logger_module_vendor_hint"):
                vendor_hints.add(reply["logger_module_vendor_hint"])
    v4_frames = []
    for transport in document.get("tcp", []):
        probe = transport.get("historical_v4_read") or {}
        for frame in probe.get("v4_frames", []):
            v4_frames.append(frame)
    return {
        "confirmed_logger_aliases": [v["alias"] for v in hosts.data.values() if v["confirmed_logger"]],
        "valid_v5_response_count": valid_v5,
        "sequence_echo": {"matches": seq_match, "mismatches": seq_mismatch},
        "short_response_markers": markers,
        "short_markers_by_probe": markers_by_probe,
        "protocol_payloads": {"modbus_rtu": modbus_payloads, "native_tsunnative_candidate": native_payloads, "unknown": unknown_payloads},
        "identity_observations": {
            "explicit_mac_suffixes": sorted(mac_suffixes),
            "logger_module_mac_candidate_suffixes": sorted(module_mac_suffixes),
            "logger_module_vendor_hints": sorted(vendor_hints),
            "note": "A bare 12-hex discovery token is a logger/module MAC candidate (especially in legacy WIFIKIT replies), but is not equated with the PLAY2-visible MAC without independent confirmation.",
        },
        "historical_v4": {
            "response_frames": len(v4_frames),
            "telemetry_candidates": sum(1 for f in v4_frames if f.get("payload_class") == "historical_v4_inverter_telemetry_candidate"),
            "classes": [f.get("payload_class") for f in v4_frames],
        },
        "interpretation": {
            "v5_transport": "0x4510 requests / 0x1510 responses are Solarman V5 transport.",
            "short_markers": "05 00 / 06 00 remain unknown short logger response markers, not assigned an error meaning without evidence.",
            "v4_probe": "Exactly one historical Solarman/iGEN V4 command 0x0001 is sent only to a strong/confirmed 8899 logger candidate and is read-only.",
            "success": "A valid long V5 inner payload or a historical V4 telemetry frame would expose the inverter-side protocol/data path.",
        },
    }


def main() -> int:
    if sys.version_info < (3, 10):
        print("Python 3.10+ required", file=sys.stderr)
        return 2
    parser = argparse.ArgumentParser(description=f"Sunology PLAY2 read-only super-probe v{VER}")
    parser.add_argument("--host", required=True)
    parser.add_argument("--monitor-sn", "--serial", dest="sn", type=int)
    parser.add_argument("--udp-timeout", type=float, default=3.0)
    parser.add_argument("--mdns-timeout", type=float, default=6.0)
    parser.add_argument("--ws-listen", type=float, default=6.0)
    parser.add_argument("--timeout", type=float, default=2.2)
    parser.add_argument("--http-timeout", type=float, default=2.0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        IPv4Address(args.host)
    except ValueError:
        print("Invalid --host", file=sys.stderr)
        return 2
    if args.sn is not None and not (0 < args.sn <= 0xFFFFFFFF):
        print("Invalid --monitor-sn", file=sys.stderr)
        return 2

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = args.output or Path(f"tsun_play2_superprobe_{stamp}.json")
    log_path = json_path.with_suffix(".log")
    log, hosts = Log(log_path), Hosts(args.host)
    document: dict[str, Any] = {
        "format": "tsun-local-play2-superprobe",
        "schema_version": SCHEMA,
        "metadata": {
            "tool_version": VER,
            "timestamp_utc": now_iso(),
            "read_only": True,
            "writes": 0,
            "cloud_requests": 0,
            "read_only_probe_policy": {
                "modbus_read_functions_sent": [3, 4],
                "modbus_write_functions_sent": [],
                "configuration_commands_sent": 0,
                "historical_v4_commands_sent": ["0x0001 read inverter data"],
                "historical_v4_probe_count_per_candidate": 1,
            },
            "privacy": {"local_ips_redacted": True, "monitor_sn_redacted": True, "full_mac_redacted": True, "full_logger_module_mac_candidate_redacted": True, "identity_suffixes_only": True},
            "v5_reference_model": {"request_control": "0x4510", "response_control": "0x1510", "response_payload_header_bytes": 14},
            "v4_reference_model": {"head": "0x68", "request_control": "0x41B1", "command": "0x0001", "end": "0x16", "purpose": "historical read inverter data"},
        },
        "udp": [], "mdns": {}, "websocket": [], "http": [], "tcp": [], "candidates": [], "analysis": {}, "errors": [],
    }

    log.write(f"TSUN Local PLAY2 Super-Probe v{VER} - READ-ONLY")
    log.write("Phase 1/5: UDP identity discovery")
    try:
        udp_results = udp_all(args.host, args.udp_timeout)
        for variant in udp_results:
            for raw in variant["replies"]:
                parsed = raw["_parsed"]
                match = bool(args.sn and parsed.get("sn") == args.sn)
                hosts.add(raw["_source"], f"udp:{variant['name']}", match)
                if parsed.get("ip"):
                    hosts.add(parsed["ip"], f"udp-declared:{variant['name']}", match)
        for variant in udp_results:
            public = {k: v for k, v in variant.items() if k != "replies"}
            public["replies"] = []
            for raw in variant["replies"]:
                parsed = raw["_parsed"]
                candidate = parsed.get("logger_module_mac_candidate")
                public["replies"].append({
                    "source_alias": hosts.alias(raw["_source"]),
                    "source_port": raw["source_port"],
                    "format": parsed["format"],
                    "sn_present": parsed.get("sn") is not None,
                    "sn_matches": bool(args.sn and parsed.get("sn") == args.sn),
                    "declared_ip_alias": hosts.alias(parsed.get("ip")) if parsed.get("ip") else None,
                    "mac_present": bool(parsed.get("mac")),
                    "mac_suffix": mac_suffix(parsed.get("mac")),
                    "logger_module_mac_candidate_present": bool(candidate),
                    "logger_module_mac_candidate_suffix": mac_suffix(candidate),
                    "logger_module_vendor_hint": vendor_hint(candidate),
                    "csv_field_count": parsed.get("csv_field_count"),
                    "csv_classes": parsed.get("csv_classes"),
                    "smart_config": smart_config_fields(parsed["text"], args.sn),
                    "payload": evidence(raw["_raw"], args.sn, list(hosts.data)),
                })
            document["udp"].append(public)
            log.write(f"  {variant['name']}: {len(public['replies'])} replies")
    except Exception as exc:
        document["errors"].append(error("udp", exc))

    log.write("Phase 2/5: mDNS / CONNECT WebSocket discovery")
    try:
        m = mdns(args.mdns_timeout)
        for service in m["services"]:
            for ip in service["addresses"]:
                hosts.add(ip, "mdns")
        document["mdns"] = {"mode": m["mode"], "packet_count": m["packet_count"], "errors": m["errors"], "services": [{"instance": "<sunology-hb>" if s["hub_name"] else "<service>", "port": s["port"], "address_aliases": [hosts.alias(ip) for ip in s["addresses"]], "hub_name": s["hub_name"], "txt": s["txt"]} for s in m["services"]]}
        for service in m["services"]:
            if isinstance(service["port"], int):
                for ip in service["addresses"][:2]:
                    ws = websocket(ip, service["port"], args.timeout, args.ws_listen, args.sn, list(hosts.data))
                    ws["host_alias"] = hosts.alias(ip)
                    document["websocket"].append(ws)
    except Exception as exc:
        document["errors"].append(error("mdns/ws", exc))

    log.write("Phase 3/5: read-only HTTP identity checks")
    for ip, info in list(hosts.data.items()):
        try:
            h = http_identity(ip, args.http_timeout, args.sn, list(hosts.data))
            h["host_alias"] = info["alias"]
            document["http"].append(h)
        except Exception as exc:
            document["errors"].append(error("http", exc))

    log.write("Phase 4/5: TCP 8899 / Solarman V5 + one historical V4 read")
    for ip, info in list(hosts.data.items()):
        for port in TCP_PORTS:
            try:
                full = port == 8899 and (bool(info["strong"]) or info["alias"] == "host0")
                v4_allowed = port == 8899 and bool(info["strong"])
                result = tcp_port(ip, port, args.timeout, args.sn, list(hosts.data), full, v4_allowed)
                result["host_alias"] = info["alias"]
                document["tcp"].append(result)
                good = [frame for _, frame in iter_v5({"tcp": [result]}) if frame.get("control") == "0x1510" and frame.get("checksum_valid") and frame.get("length_valid") and frame.get("logger_sn_matches_supplied")]
                if good:
                    hosts.confirm(ip, f"valid_v5_response:{port}")
                log.write(f"  TCP {info['alias']}:{port}: open={result['open']} valid-v5={len(good)} v4={'yes' if result.get('historical_v4_read') else 'no'}")
            except Exception as exc:
                document["errors"].append(error(f"tcp:{port}", exc))

    log.write("Phase 5/5: correlation and protocol classification")
    document["candidates"] = hosts.public()
    document["analysis"] = build_analysis(document, hosts)
    document["summary"] = {
        "udp_variants": len(document["udp"]),
        "udp_replies": sum(len(x["replies"]) for x in document["udp"]),
        "candidates": len(document["candidates"]),
        "confirmed_loggers": len(document["analysis"]["confirmed_logger_aliases"]),
        "valid_v5_responses": document["analysis"]["valid_v5_response_count"],
        "historical_v4_frames": document["analysis"]["historical_v4"]["response_frames"],
        "historical_v4_telemetry_candidates": document["analysis"]["historical_v4"]["telemetry_candidates"],
        "tcp_open": {str(port): sum(1 for x in document["tcp"] if x["port"] == port and x["open"]) for port in TCP_PORTS},
    }
    document["metadata"]["timestamp_utc"] = now_iso()
    json_path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    log.write(f"Confirmed logger(s): {document['analysis']['confirmed_logger_aliases'] or 'none'}")
    log.write(f"Valid V5 responses: {document['analysis']['valid_v5_response_count']}")
    log.write(f"V4 frames: {document['analysis']['historical_v4']['response_frames']}; telemetry candidates: {document['analysis']['historical_v4']['telemetry_candidates']}")
    log.write(f"JSON: {json_path}")
    log.write(f"LOG : {log_path}")
    log.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
