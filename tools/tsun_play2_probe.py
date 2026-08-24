#!/usr/bin/env python3
# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later
"""Sunology PLAY2 / TSUN read-only local super-probe.

Python >= 3.10, standard library only.

This tool is intentionally diagnostic and privacy-safe. It never sends inverter
configuration writes, BLE/Wi-Fi provisioning data, cloud requests, Modbus write
functions or WebSocket application messages.

Main goals:
- discover the actual local logger through iGEN UDP discovery (48899/49999);
- distinguish a real MAC address from an opaque 12-hex module identifier;
- inspect read-only local HTTP identity pages;
- probe TCP 8899 and decode Solarman V5 request/response envelopes;
- identify the protocol carried inside the V5 response payload;
- keep mDNS/WebSocket checks for Sunology CONNECT/Hub devices.
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

VER = "1.3.1"
SCHEMA = 6

UDP_PORTS = (48899, 49999)
TCP_PORTS = (8899, 48899, 49999)
SMARTLINK = b"smartlinkfind"
LEGACY_DISCOVERY = (
    b"WIFIKIT-214028-READ",
    b"HF-A11ASSISTHREAD",
    b"devicelinkfind",
)

MDNS_GROUP = "224.0.0.251"
MDNS_SERVICE = "_solarhome._tcp.local."
HUB_PREFIX = "sunology-hb-"
HTTP_PATHS = ("/index_cn.html", "/index.html", "/status.html", "/")
HTTP_BASIC = base64.b64encode(b"admin:admin").decode("ascii")

SN_RE = re.compile(r"(?<!\d)([1-9]\d{7,9})(?!\d)")
IP_RE = re.compile(
    r"(?<!\d)(?:25[0-5]|2[0-4]\d|1?\d?\d)"
    r"(?:\.(?:25[0-5]|2[0-4]\d|1?\d?\d)){3}(?!\d)"
)
MAC_SEP_RE = re.compile(r"(?i)(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}")
HEX12_RE = re.compile(r"(?i)(?<![0-9a-f])([0-9a-f]{12})(?![0-9a-f])")
MAX_EVIDENCE = 4096


class Log:
    def __init__(self, path: Path):
        self._file = path.open("w", encoding="utf-8", newline="\n")

    def write(self, text: str = "") -> None:
        print(text)
        self._file.write(text + "\n")
        self._file.flush()

    def close(self) -> None:
        self._file.close()


class Hosts:
    def __init__(self, supplied_host: str):
        self.data: dict[str, dict[str, Any]] = {
            supplied_host: {
                "alias": "host0",
                "reasons": ["supplied_host"],
                "strong": False,
                "confirmed_logger": False,
            }
        }

    def add(self, ip: str | None, reason: str, strong: bool = False) -> None:
        if not ip:
            return
        try:
            IPv4Address(ip)
        except ValueError:
            return
        if ip not in self.data and len(self.data) < 8:
            self.data[ip] = {
                "alias": f"candidate{len(self.data)}",
                "reasons": [],
                "strong": False,
                "confirmed_logger": False,
            }
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
        if not ip:
            return None
        return self.data.get(ip, {}).get("alias", "other-local-host")

    def public(self) -> list[dict[str, Any]]:
        return [
            {
                "alias": value["alias"],
                "reasons": value["reasons"],
                "strong": value["strong"],
                "confirmed_logger": value["confirmed_logger"],
            }
            for value in self.data.values()
        ]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def error(stage: str, exc: BaseException) -> dict[str, str]:
    return {
        "stage": stage,
        "type": type(exc).__name__,
        "detail": str(exc) or type(exc).__name__,
    }


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


def compact_module_identifier(value: str) -> str | None:
    text = value.strip()
    if HEX12_RE.fullmatch(text):
        return text.upper()
    return None


def mac_suffix(mac: str | None) -> str | None:
    if not mac:
        return None
    parts = mac.upper().replace("-", ":").split(":")
    if len(parts) != 6:
        return None
    return ":".join(parts[-2:])


def identifier_suffix(identifier: str | None) -> str | None:
    if not identifier:
        return None
    return identifier[-4:].upper()


def redact_bytes(data: bytes, supplied_sn: int | None, ips: list[str]) -> bytes:
    out = bytes(data)
    if supplied_sn:
        for value in (
            str(supplied_sn).encode(),
            supplied_sn.to_bytes(4, "little"),
            supplied_sn.to_bytes(4, "big"),
        ):
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
        "redacted_ascii": "".join(
            chr(value) if 32 <= value < 127 else f"\\x{value:02x}" for value in cap
        ),
        "complete": len(data) <= MAX_EVIDENCE,
    }


def classify_text_field(value: str) -> dict[str, Any]:
    text = value.strip()
    result: dict[str, Any] = {"length": len(text), "class": "text"}
    if IP_RE.fullmatch(text):
        result["class"] = "ipv4"
        return result

    explicit_mac = normalize_mac(text)
    if explicit_mac:
        result["class"] = "mac"
        result["suffix"] = mac_suffix(explicit_mac)
        return result

    module_identifier = compact_module_identifier(text)
    if module_identifier:
        result["class"] = "module_identifier_hex12"
        result["suffix"] = identifier_suffix(module_identifier)
        return result

    if text.isdigit() and 8 <= len(text) <= 10:
        result["class"] = "serial_like"
    return result


def parse_udp(data: bytes) -> dict[str, Any]:
    text = data.decode("utf-8", "replace").strip("\x00\r\n ")
    out: dict[str, Any] = {
        "text": text,
        "format": "text",
        "sn": None,
        "ip": None,
        "mac": None,
        "module_identifier": None,
    }

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

        ip_value = obj.get("ip")
        if isinstance(ip_value, str) and IP_RE.fullmatch(ip_value.strip()):
            out["ip"] = ip_value.strip()

        mac_value = obj.get("mac")
        if isinstance(mac_value, str):
            out["mac"] = normalize_mac(mac_value, allow_compact=True)

        for key in ("moduleId", "module_id", "deviceId", "device_id"):
            value = obj.get(key)
            if isinstance(value, str) and compact_module_identifier(value):
                out["module_identifier"] = compact_module_identifier(value)
                break
        return out

    lower = text.lower()
    if "smart_config" in lower or "smartconfig" in lower:
        out["format"] = "smart_config_text"
    elif "smartlink" in lower:
        out["format"] = "smartlink_text"

    sn_match = SN_RE.search(text)
    if sn_match:
        out["sn"] = int(sn_match.group(1))

    ip_match = IP_RE.search(text)
    if ip_match:
        out["ip"] = ip_match.group(0)

    mac_match = MAC_SEP_RE.search(text)
    if mac_match:
        out["mac"] = normalize_mac(mac_match.group(0))

    hex_match = HEX12_RE.search(text)
    if hex_match:
        candidate = compact_module_identifier(hex_match.group(1))
        out["module_identifier"] = candidate

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
            elif cls["class"] == "module_identifier_hex12" and not out["module_identifier"]:
                out["module_identifier"] = compact_module_identifier(part)
            elif cls["class"] == "serial_like" and out["sn"] is None:
                out["sn"] = int(part)
    return out


def smart_config_fields(text: str, supplied_sn: int | None) -> dict[str, Any] | None:
    lower = text.lower()
    pos = lower.find("smart_config")
    prefix = "smart_config"
    if pos < 0:
        pos = lower.find("smartconfig")
        prefix = "smartconfig"
    if pos < 0:
        return None

    tail = text[pos + len(prefix) :].strip("\x00\r\n #")
    fields = tail.split("##") if tail else []
    public_fields: list[dict[str, Any]] = []
    for index, field in enumerate(fields):
        classified = classify_text_field(field)
        public_fields.append(
            {
                "index": index,
                "length": len(field),
                "class": classified["class"],
                "suffix": classified.get("suffix"),
                "matches_supplied_sn": bool(supplied_sn and field == str(supplied_sn)),
            }
        )
    return {
        "prefix": prefix,
        "separator": "##",
        "field_count": len(fields),
        "fields": public_fields,
    }


def udp_variant(host: str, bind_port: int, send_port: int, messages: tuple[bytes, ...], timeout: float) -> dict[str, Any]:
    result: dict[str, Any] = {"bind_port": bind_port, "send_port": send_port, "messages": [message.decode("ascii") for message in messages], "bound": False, "replies": [], "error": None}
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
        if bind_port == 49999 and send_port == 48899:
            try:
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, socket.inet_aton("239.0.0.0") + socket.inet_aton("0.0.0.0"))
            except OSError:
                pass
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
    out: list[dict[str, Any]] = []
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
    labels: list[str] = []
    next_offset = None
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
    packets: list[tuple[bytes, str, int]] = []
    errors: list[dict[str, str]] = []
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
    srv: dict[str, tuple[int, str]] = {}
    addresses: dict[str, set[str]] = {}
    ptr: set[str] = set()
    txt: dict[str, list[str]] = {}
    for payload, _, _ in packets:
        try:
            _, _, qd, an, ns, ar = struct.unpack_from("!HHHHHH", payload, 0)
            offset = 12
            for _ in range(qd):
                _, offset = read_dns_name(payload, offset)
                offset += 4
            for _ in range(an + ns + ar):
                name, offset = read_dns_name(payload, offset)
                record_type, _, _, length = struct.unpack_from("!HHIH", payload, offset)
                offset += 10
                start, end = offset, offset + length
                if record_type == 12:
                    target, _ = read_dns_name(payload, start)
                    ptr.add(target)
                elif record_type == 33 and length >= 6:
                    _, _, port = struct.unpack_from("!HHH", payload, start)
                    target, _ = read_dns_name(payload, start + 6)
                    srv[name] = (port, target)
                elif record_type == 1 and length == 4:
                    addresses.setdefault(name, set()).add(socket.inet_ntoa(payload[start:end]))
                elif record_type == 16:
                    cursor = start
                    values: list[str] = []
                    while cursor < end:
                        item_len = payload[cursor]
                        cursor += 1
                        values.append(payload[cursor : cursor + item_len].decode("utf8", "replace"))
                        cursor += item_len
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
                def recv_exact(count: int) -> bytes:
                    data = b""
                    while len(data) < count:
                        chunk = sock.recv(count - len(data))
                        if not chunk:
                            raise EOFError
                        data += chunk
                    return data
                while len(result["events"]) < 24 and (left := deadline - time.monotonic()) > 0:
                    sock.settimeout(min(1.5, left))
                    try:
                        header = recv_exact(2)
                    except socket.timeout:
                        continue
                    except EOFError:
                        break
                    opcode = header[0] & 15
                    length = header[1] & 127
                    masked = bool(header[1] & 128)
                    if length == 126:
                        length = int.from_bytes(recv_exact(2), "big")
                    elif length == 127:
                        length = int.from_bytes(recv_exact(8), "big")
                    if length > 16384:
                        break
                    mask = recv_exact(4) if masked else b""
                    payload = recv_exact(length)
                    if masked:
                        payload = bytes(value ^ mask[i % 4] for i, value in enumerate(payload))
                    event: dict[str, Any] = {"opcode": opcode, "payload": evidence(payload, supplied_sn, ips)}
                    if opcode == 1:
                        try:
                            obj = json.loads(payload.decode("utf8", "replace"))
                        except Exception:
                            obj = None
                        if isinstance(obj, dict):
                            data = obj.get("data") if isinstance(obj.get("data"), dict) else obj
                            event["event"] = obj.get("event") or obj.get("type")
                            event["signals"] = {k: data[k] for k in ("pvP", "power", "production", "soc", "batteryPower", "gridPower", "state", "deviceState") if k in data and isinstance(data[k], (int, float, str, bool, type(None)))}
                    result["events"].append(event)
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


def http_get(host: str, port: int, tls: bool, path: str, timeout: float, use_basic_auth: bool) -> dict[str, Any]:
    headers = {"Connection": "close", "User-Agent": "TSUN-Local-PLAY2-Probe", "Cache-Control": "no-cache"}
    if use_basic_auth:
        headers["Authorization"] = f"Basic {HTTP_BASIC}"
    if tls:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        connection: http.client.HTTPConnection = http.client.HTTPSConnection(host, port, timeout=timeout, context=ctx)
    else:
        connection = http.client.HTTPConnection(host, port, timeout=timeout)
    try:
        connection.request("GET", path, headers=headers)
        response = connection.getresponse()
        body = response.read(524289)
        return {"status": response.status, "server": response.getheader("Server"), "content_type": response.getheader("Content-Type"), "www_authenticate": response.getheader("WWW-Authenticate"), "body": body}
    finally:
        connection.close()


def http_identity(host: str, timeout: float, supplied_sn: int | None, ips: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {"transports": []}
    for port, tls in ((80, False), (443, True)):
        transport: dict[str, Any] = {"scheme": "https" if tls else "http", "open": port_open(host, port, min(timeout, 1.2)), "pages": []}
        if transport["open"]:
            for path in HTTP_PATHS:
                page: dict[str, Any] = {"path": path}
                try:
                    initial = http_get(host, port, tls, path, timeout, False)
                    page.update({"status": initial["status"], "server": initial["server"], "content_type": initial["content_type"], "www_authenticate": initial["www_authenticate"], "body": evidence(initial["body"], supplied_sn, ips) if len(initial["body"]) <= 524288 else None})
                    challenge = initial.get("www_authenticate") or ""
                    if initial["status"] == 401 and (not challenge or "basic" in challenge.lower()):
                        try:
                            authenticated = http_get(host, port, tls, path, timeout, True)
                            page["basic_admin_admin"] = {"attempted_read_only": True, "status": authenticated["status"], "server": authenticated["server"], "content_type": authenticated["content_type"], "body": evidence(authenticated["body"], supplied_sn, ips) if len(authenticated["body"]) <= 524288 else None}
                        except Exception as exc:
                            page["basic_admin_admin"] = {"attempted_read_only": True, "error": error("http_basic", exc)}
                except Exception as exc:
                    page["error"] = error("http", exc)
                transport["pages"].append(page)
        result["transports"].append(transport)
    return result


def modbus_rtu_read(address: int, count: int = 1, function: int = 3) -> bytes:
    body = b"\x01" + bytes((function,)) + address.to_bytes(2, "big") + count.to_bytes(2, "big")
    return body + crc16_modbus(body).to_bytes(2, "little")


def modbus_tcp_read(address: int, count: int = 1, tx: int = 1) -> bytes:
    pdu = b"\x01\x03" + address.to_bytes(2, "big") + count.to_bytes(2, "big")
    return struct.pack("!HHH", tx, 0, len(pdu)) + pdu


def native_1511_read(tag: int, function: int, start: int, end: int) -> bytes:
    count = end - start + 1
    body = bytes((tag, function, 0)) + start.to_bytes(2, "big") + b"\x00\x02" + count.to_bytes(2, "big")
    return body + crc16_modbus(body).to_bytes(2, "big")


def v5_request(logger_sn: int, payload: bytes, sensor_list: int = 0, sequence: int = 0) -> bytes:
    data = b"\x02" + sensor_list.to_bytes(2, "little") + bytes(12) + payload
    core = len(data).to_bytes(2, "little") + b"\x10\x45" + sequence.to_bytes(2, "little") + logger_sn.to_bytes(4, "little") + data
    return b"\xA5" + core + bytes((sum(core) & 0xFF, 0x15))


def core_probe_matrix(sn: int | None) -> list[tuple[str, bytes, dict[str, Any]]]:
    probes: list[tuple[str, bytes, dict[str, Any]]] = []
    logger_sns = [0]
    if sn:
        logger_sns.append(sn)
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
        for index, (name, payload, sensor_list, inner_kind) in enumerate(tests):
            sequence = 0x40 + index
            probes.append((f"v5_{name}_{who}", v5_request(logger_sn, payload, sensor_list, sequence), {"kind": "solarman_v5_request", "inner_kind": inner_kind, "sensor_list": f"0x{sensor_list:04X}", "sn_zero": logger_sn == 0, "request_sequence_low": sequence & 0xFF}))
    probes.extend([
        ("crosscheck_direct_rtu_fc03_3000", modbus_rtu_read(0x3000, 1, 3), {"kind": "legacy_crosscheck", "inner_kind": "modbus_rtu"}),
        ("crosscheck_direct_rtu_fc04_3000", modbus_rtu_read(0x3000, 1, 4), {"kind": "legacy_crosscheck", "inner_kind": "modbus_rtu"}),
        ("crosscheck_direct_modbus_tcp_3000", modbus_tcp_read(0x3000), {"kind": "legacy_crosscheck", "inner_kind": "modbus_tcp"}),
        ("crosscheck_direct_native_1511", native_1511_read(0xA1, 0x01, 0x0BB8, 0x0BD0), {"kind": "legacy_crosscheck", "inner_kind": "native1511"}),
    ])
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
    out = []
    for index, (name, payload, sensor_list, inner_kind) in enumerate(tests):
        sequence = 0x70 + index
        out.append((name, v5_request(sn, payload, sensor_list, sequence), {"kind": "solarman_v5_same_connection", "inner_kind": inner_kind, "sensor_list": f"0x{sensor_list:04X}", "request_sequence_low": sequence}))
    return out


def control_name(control: int) -> str:
    return {0x4110: "HANDSHAKE", 0x4210: "DATA", 0x4310: "INFO", 0x4510: "REQUEST", 0x1510: "RESPONSE", 0x4710: "HEARTBEAT", 0x4810: "REPORT"}.get(control, "UNKNOWN")


def split_v5_frames(data: bytes) -> tuple[list[bytes], bytes]:
    frames: list[bytes] = []
    offset = 0
    while offset < len(data):
        start = data.find(b"\xA5", offset)
        if start < 0 or start + 3 > len(data):
            break
        declared = int.from_bytes(data[start + 1 : start + 3], "little")
        total = 13 + declared
        if start + total > len(data):
            break
        candidate = data[start : start + total]
        if candidate[-1] != 0x15:
            offset = start + 1
            continue
        frames.append(candidate)
        offset = start + total
    remainder = data[offset:] if offset < len(data) else b""
    return frames, remainder


def decode_embedded(payload: bytes, supplied_sn: int | None, ips: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {"length": len(payload), "evidence": evidence(payload, supplied_sn, ips)}
    if not payload:
        result["class"] = "empty"
        return result
    if len(payload) == 2:
        result.update({"class": "short_response_marker", "marker_hex": payload.hex(), "marker_le": int.from_bytes(payload, "little"), "note": "Valid V5 response payload, but too short to be normal Modbus RTU data."})
        return result
    if len(payload) >= 5:
        rtu_valid = crc16_modbus(payload[:-2]) == int.from_bytes(payload[-2:], "little")
        native_be_valid = crc16_modbus(payload[:-2]) == int.from_bytes(payload[-2:], "big")
        result["rtu_crc_candidate_valid"] = rtu_valid
        result["native_crc_be_candidate_valid"] = native_be_valid
        if rtu_valid:
            function = payload[1]
            result.update({"class": "modbus_rtu", "unit": payload[0], "function": function})
            if function & 0x80 and len(payload) >= 5:
                result["exception_code"] = payload[2]
            elif function in (3, 4) and len(payload) >= 5:
                byte_count = payload[2]
                data = payload[3:-2]
                result["byte_count"] = byte_count
                result["byte_count_valid"] = byte_count == len(data)
                if byte_count == len(data) and byte_count % 2 == 0:
                    result["registers"] = [int.from_bytes(data[i : i + 2], "big") for i in range(0, len(data), 2)]
            return result
        if native_be_valid or payload[0] in (0xA1, 0xA2, 0xA3, 0xA4):
            result["class"] = "native_tsunnative_candidate"
            result["tag"] = f"0x{payload[0]:02X}"
            if len(payload) > 1:
                result["function"] = payload[1]
            return result
    result["class"] = "unknown_protocol_payload"
    return result


def decode_v5(frame: bytes, supplied_sn: int | None, ips: list[str], request_meta: dict[str, Any] | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {"looks_like_v5": False, "valid_start": False, "valid_end": False, "length_valid": False, "checksum_valid": False}
    if len(frame) < 13:
        out["reason"] = "too_short"
        return out
    out["valid_start"] = frame[0] == 0xA5
    out["valid_end"] = frame[-1] == 0x15
    if not out["valid_start"]:
        out["reason"] = "missing_A5"
        return out
    declared = int.from_bytes(frame[1:3], "little")
    expected_total = 13 + declared
    out.update({"looks_like_v5": True, "declared_payload_length": declared, "actual_total_length": len(frame), "expected_total_length": expected_total, "length_valid": len(frame) == expected_total})
    control = int.from_bytes(frame[3:5], "little")
    sequence = int.from_bytes(frame[5:7], "little")
    logger_sn = int.from_bytes(frame[7:11], "little")
    out.update({"control": f"0x{control:04X}", "control_name": control_name(control), "sequence": sequence, "sequence_low": sequence & 0xFF, "response_counter_high": (sequence >> 8) & 0xFF, "logger_sn_present": logger_sn != 0, "logger_sn_matches_supplied": bool(supplied_sn and logger_sn == supplied_sn), "checksum_valid": (sum(frame[1:-2]) & 0xFF) == frame[-2], "checksum_byte": frame[-2]})
    if request_meta and isinstance(request_meta.get("request_sequence_low"), int):
        out["request_sequence_low"] = request_meta["request_sequence_low"]
        out["sequence_low_echo_matches"] = (sequence & 0xFF) == request_meta["request_sequence_low"]
    if not out["length_valid"] or declared < 1:
        return out
    payload = frame[11 : 11 + declared]
    out["payload_length"] = len(payload)
    if control == 0x1510 and len(payload) >= 14:
        frame_type = payload[0]
        status = payload[1]
        total_working = int.from_bytes(payload[2:6], "little")
        power_on = int.from_bytes(payload[6:10], "little")
        offset_time = int.from_bytes(payload[10:14], "little")
        acquisition = total_working + offset_time
        embedded = payload[14:]
        out["response"] = {"frame_type": frame_type, "frame_type_name": {0: "cloud_or_keepalive", 1: "logger", 2: "inverter"}.get(frame_type, "unknown"), "status": status, "total_working_time_s": total_working, "power_on_time_s": power_on, "device_total_operation_time_s": total_working - power_on, "offset_time_s": offset_time, "acquisition_timestamp_unix": acquisition, "acquisition_timestamp_utc": datetime.fromtimestamp(acquisition, timezone.utc).isoformat() if 946684800 <= acquisition <= 4102444800 else None, "embedded": decode_embedded(embedded, supplied_sn, ips)}
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


def decode_received(data: bytes, supplied_sn: int | None, ips: list[str], request_meta: dict[str, Any] | None) -> dict[str, Any]:
    frames, remainder = split_v5_frames(data)
    result: dict[str, Any] = {"response": evidence(data, supplied_sn, ips), "v5_frame_count": len(frames), "v5_frames": [decode_v5(frame, supplied_sn, ips, request_meta) for frame in frames]}
    if remainder:
        result["unparsed_remainder"] = evidence(remainder, supplied_sn, ips)
    return result


def tcp_exchange(host: str, port: int, name: str, request: bytes, meta: dict[str, Any], timeout: float, supplied_sn: int | None, ips: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {"name": name, "meta": meta, "connected": False, "sent": False, "response_length": 0}
    start = time.monotonic()
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            result["connected"] = True
            sock.sendall(request)
            result["sent"] = True
            response = recv_until_gap(sock, timeout)
            result["response_length"] = len(response)
            result["outcome"] = "bytes" if response else "no_bytes"
            if response:
                result.update(decode_received(response, supplied_sn, ips, meta))
    except Exception as exc:
        result["outcome"] = "error"
        result["error"] = error("tcp", exc)
    result["elapsed_ms"] = round((time.monotonic() - start) * 1000, 1)
    return result


def tcp_same_connection_session(host: str, port: int, timeout: float, supplied_sn: int | None, ips: list[str]) -> dict[str, Any]:
    session: dict[str, Any] = {"enabled": bool(supplied_sn), "connected": False, "steps": []}
    probes = session_probe_matrix(supplied_sn)
    if not probes:
        return session
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            session["connected"] = True
            for name, request, meta in probes:
                step: dict[str, Any] = {"name": name, "meta": meta, "sent": False}
                start = time.monotonic()
                try:
                    sock.sendall(request)
                    step["sent"] = True
                    response = recv_until_gap(sock, timeout)
                    step["response_length"] = len(response)
                    step["outcome"] = "bytes" if response else "no_bytes"
                    if response:
                        step.update(decode_received(response, supplied_sn, ips, meta))
                except Exception as exc:
                    step["outcome"] = "error"
                    step["error"] = error("tcp_session", exc)
                step["elapsed_ms"] = round((time.monotonic() - start) * 1000, 1)
                session["steps"].append(step)
                time.sleep(0.12)
    except Exception as exc:
        session["error"] = error("tcp_session_connect", exc)
    return session


def tcp_port(host: str, port: int, timeout: float, supplied_sn: int | None, ips: list[str], full: bool) -> dict[str, Any]:
    result: dict[str, Any] = {"port": port, "open": port_open(host, port, min(timeout, 1.2)), "passive": None, "probes": [], "same_connection_session": None}
    if not result["open"]:
        return result
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            passive = recv_until_gap(sock, min(timeout, 1.0), gap=0.2)
            result["passive"] = {"received": bool(passive), **(decode_received(passive, supplied_sn, ips, None) if passive else {})}
    except Exception as exc:
        result["passive"] = {"error": error("passive", exc)}
    probes = core_probe_matrix(supplied_sn)
    if not full:
        probes = probes[:4]
    for name, request, meta in probes:
        result["probes"].append(tcp_exchange(host, port, name, request, meta, timeout, supplied_sn, ips))
        time.sleep(0.08)
    if full and port == 8899:
        result["same_connection_session"] = tcp_same_connection_session(host, port, timeout, supplied_sn, ips)
    return result


def iter_decoded_frames(document: dict[str, Any]):
    for transport in document.get("tcp", []):
        host_alias = transport.get("host_alias")
        port = transport.get("port")
        for probe in transport.get("probes", []):
            for frame in probe.get("v5_frames", []):
                yield host_alias, port, probe.get("name"), frame
        session = transport.get("same_connection_session") or {}
        for step in session.get("steps", []):
            for frame in step.get("v5_frames", []):
                yield host_alias, port, step.get("name"), frame


def build_analysis(document: dict[str, Any], hosts: Hosts) -> dict[str, Any]:
    confirmed = [value["alias"] for value in hosts.data.values() if value["confirmed_logger"]]
    markers: dict[str, int] = {}
    markers_by_probe: dict[str, dict[str, int]] = {}
    valid_v5 = 0
    sequence_matches = 0
    sequence_mismatches = 0
    modbus_payloads = 0
    native_payloads = 0
    unknown_payloads = 0
    timestamps: list[str] = []
    for _, _, probe_name, frame in iter_decoded_frames(document):
        if frame.get("control") == "0x1510" and frame.get("checksum_valid") and frame.get("length_valid"):
            valid_v5 += 1
        if frame.get("sequence_low_echo_matches") is True:
            sequence_matches += 1
        elif frame.get("sequence_low_echo_matches") is False:
            sequence_mismatches += 1
        response = frame.get("response") or {}
        timestamp = response.get("acquisition_timestamp_utc")
        if timestamp:
            timestamps.append(timestamp)
        embedded = response.get("embedded") or {}
        cls = embedded.get("class")
        if cls == "short_response_marker":
            marker = embedded.get("marker_hex", "")
            markers[marker] = markers.get(marker, 0) + 1
            per_probe = markers_by_probe.setdefault(probe_name or "unknown", {})
            per_probe[marker] = per_probe.get(marker, 0) + 1
        elif cls == "modbus_rtu":
            modbus_payloads += 1
        elif cls == "native_tsunnative_candidate":
            native_payloads += 1
        elif cls == "unknown_protocol_payload":
            unknown_payloads += 1
    mac_suffixes: set[str] = set()
    module_suffixes: set[str] = set()
    for variant in document.get("udp", []):
        for reply in variant.get("replies", []):
            if reply.get("mac_suffix"):
                mac_suffixes.add(reply["mac_suffix"])
            if reply.get("module_identifier_suffix"):
                module_suffixes.add(reply["module_identifier_suffix"])
    http_auth_ok = []
    for host in document.get("http", []):
        ok = any(page.get("basic_admin_admin", {}).get("status") == 200 for transport in host.get("transports", []) for page in transport.get("pages", []))
        if ok:
            http_auth_ok.append(host.get("host_alias"))
    return {"confirmed_logger_aliases": confirmed, "valid_v5_response_count": valid_v5, "sequence_echo": {"matches": sequence_matches, "mismatches": sequence_mismatches}, "short_response_markers": markers, "short_markers_by_probe": markers_by_probe, "protocol_payloads": {"modbus_rtu": modbus_payloads, "native_tsunnative_candidate": native_payloads, "unknown": unknown_payloads}, "identity_observations": {"mac_suffixes": sorted(mac_suffixes), "module_identifier_suffixes": sorted(module_suffixes), "note": "A bare 12-hex smart_config/legacy token is kept as an opaque module identifier, not assumed to be the PLAY2-visible MAC address."}, "http_basic_admin_admin_success_aliases": [x for x in http_auth_ok if x], "v5_timestamp_first": timestamps[0] if timestamps else None, "v5_timestamp_last": timestamps[-1] if timestamps else None, "interpretation": {"transport": "0x4510 requests and 0x1510 responses are treated as Solarman V5 transport.", "short_markers": "Two-byte embedded payloads such as 05 00 / 06 00 are preserved as unknown response markers; they are not labelled as Modbus data or errors without evidence.", "next_success_condition": "At least one valid 0x1510 response containing an embedded payload longer than two bytes that decodes as Modbus RTU, TSUN native, or another repeatable protocol."}}


def main() -> int:
    if sys.version_info < (3, 10):
        print("Python 3.10+ required", file=sys.stderr)
        return 2
    parser = argparse.ArgumentParser(description="Sunology PLAY2 read-only super-probe v1.3.1")
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
    log = Log(log_path)
    hosts = Hosts(args.host)
    document: dict[str, Any] = {"format": "tsun-local-play2-superprobe", "schema_version": SCHEMA, "metadata": {"tool_version": VER, "timestamp_utc": now_iso(), "read_only": True, "writes": 0, "cloud_requests": 0, "read_only_probe_policy": {"modbus_read_functions_sent": [3, 4], "modbus_write_functions_sent": [], "configuration_commands_sent": 0, "same_connection_session_is_read_only": True}, "privacy": {"local_ips_redacted": True, "monitor_sn_redacted": True, "full_mac_redacted": True, "full_module_identifier_redacted": True, "identity_suffixes_only": True}, "v5_reference_model": {"request_control": "0x4510", "response_control": "0x1510", "response_payload_header_bytes": 14, "fields": ["frame_type", "status", "total_working_time", "power_on_time", "offset_time", "embedded_payload"]}}, "udp": [], "mdns": {}, "websocket": [], "http": [], "tcp": [], "candidates": [], "analysis": {}, "errors": []}
    log.write(f"TSUN Local PLAY2 Super-Probe v{VER} - READ-ONLY")
    log.write("Phase 1/5: UDP identity discovery")
    try:
        udp_results = udp_all(args.host, args.udp_timeout)
        for variant in udp_results:
            for raw_reply in variant["replies"]:
                parsed = raw_reply["_parsed"]
                sn_match = bool(args.sn and parsed.get("sn") == args.sn)
                hosts.add(raw_reply["_source"], f"udp:{variant['name']}", sn_match)
                if parsed.get("ip"):
                    hosts.add(parsed["ip"], f"udp-declared:{variant['name']}", sn_match)
        for variant in udp_results:
            public = {key: value for key, value in variant.items() if key != "replies"}
            public["replies"] = []
            for raw_reply in variant["replies"]:
                parsed = raw_reply["_parsed"]
                mac = parsed.get("mac")
                module_identifier = parsed.get("module_identifier")
                public["replies"].append({"source_alias": hosts.alias(raw_reply["_source"]), "source_port": raw_reply["source_port"], "format": parsed["format"], "sn_present": parsed.get("sn") is not None, "sn_matches": bool(args.sn and parsed.get("sn") == args.sn), "declared_ip_alias": hosts.alias(parsed.get("ip")) if parsed.get("ip") else None, "mac_present": bool(mac), "mac_suffix": mac_suffix(mac), "module_identifier_present": bool(module_identifier), "module_identifier_suffix": identifier_suffix(module_identifier), "csv_field_count": parsed.get("csv_field_count"), "csv_classes": parsed.get("csv_classes"), "smart_config": smart_config_fields(parsed["text"], args.sn), "payload": evidence(raw_reply["_raw"], args.sn, list(hosts.data))})
            document["udp"].append(public)
            log.write(f"  {variant['name']}: {len(public['replies'])} replies")
    except Exception as exc:
        document["errors"].append(error("udp", exc))
    log.write("Phase 2/5: mDNS / CONNECT WebSocket discovery")
    try:
        mdns_result = mdns(args.mdns_timeout)
        for service in mdns_result["services"]:
            for ip in service["addresses"]:
                hosts.add(ip, "mdns")
        document["mdns"] = {"mode": mdns_result["mode"], "packet_count": mdns_result["packet_count"], "errors": mdns_result["errors"], "services": [{"instance": "<sunology-hb>" if service["hub_name"] else "<service>", "port": service["port"], "address_aliases": [hosts.alias(ip) for ip in service["addresses"]], "hub_name": service["hub_name"], "txt": service["txt"]} for service in mdns_result["services"]]}
        log.write(f"  mDNS services: {len(mdns_result['services'])}")
        for service in mdns_result["services"]:
            if isinstance(service["port"], int):
                for ip in service["addresses"][:2]:
                    ws = websocket(ip, service["port"], args.timeout, args.ws_listen, args.sn, list(hosts.data))
                    ws["host_alias"] = hosts.alias(ip)
                    document["websocket"].append(ws)
    except Exception as exc:
        document["errors"].append(error("mdns/ws", exc))
    log.write("Phase 3/5: read-only HTTP identity checks")
    for ip, host_info in list(hosts.data.items()):
        try:
            http_result = http_identity(ip, args.http_timeout, args.sn, list(hosts.data))
            http_result["host_alias"] = host_info["alias"]
            document["http"].append(http_result)
            auth_ok = any(page.get("basic_admin_admin", {}).get("status") == 200 for transport in http_result["transports"] for page in transport["pages"])
            log.write(f"  HTTP {host_info['alias']}: basic-admin-read={'yes' if auth_ok else 'no'}")
        except Exception as exc:
            document["errors"].append(error("http", exc))
    log.write("Phase 4/5: TCP / Solarman V5 read probes")
    for ip, host_info in list(hosts.data.items()):
        for port in TCP_PORTS:
            try:
                full = port == 8899 and (bool(host_info["strong"]) or host_info["alias"] == "host0")
                result = tcp_port(ip, port, args.timeout, args.sn, list(hosts.data), full)
                result["host_alias"] = host_info["alias"]
                document["tcp"].append(result)
                good = []
                for _, _, _, frame in iter_decoded_frames({"tcp": [result]}):
                    if frame.get("control") == "0x1510" and frame.get("checksum_valid") and frame.get("length_valid") and frame.get("logger_sn_matches_supplied"):
                        good.append(frame)
                if good:
                    hosts.confirm(ip, f"valid_v5_response:{port}")
                log.write(f"  TCP {host_info['alias']}:{port}: open={result['open']} valid-v5={len(good)} full={'yes' if full else 'no'}")
            except Exception as exc:
                document["errors"].append(error(f"tcp:{port}", exc))
    log.write("Phase 5/5: correlation and protocol classification")
    document["candidates"] = hosts.public()
    document["analysis"] = build_analysis(document, hosts)
    document["summary"] = {"udp_variants": len(document["udp"]), "udp_replies": sum(len(item["replies"]) for item in document["udp"]), "candidates": len(document["candidates"]), "confirmed_loggers": len(document["analysis"]["confirmed_logger_aliases"]), "valid_v5_responses": document["analysis"]["valid_v5_response_count"], "modbus_payloads": document["analysis"]["protocol_payloads"]["modbus_rtu"], "native_payloads": document["analysis"]["protocol_payloads"]["native_tsunnative_candidate"], "mdns_services": len(document.get("mdns", {}).get("services", [])), "ws_connections": sum(1 for item in document["websocket"] if item["connected"]), "tcp_open": {str(port): sum(1 for item in document["tcp"] if item["port"] == port and item["open"]) for port in TCP_PORTS}}
    document["metadata"]["timestamp_utc"] = now_iso()
    json_path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    log.write(f"Confirmed logger(s): {document['analysis']['confirmed_logger_aliases'] or 'none'}")
    log.write(f"Valid V5 responses: {document['analysis']['valid_v5_response_count']}")
    log.write(f"Markers: {document['analysis']['short_response_markers']}")
    log.write(f"Protocol payloads: {document['analysis']['protocol_payloads']}")
    log.write(f"JSON: {json_path}")
    log.write(f"LOG : {log_path}")
    log.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
