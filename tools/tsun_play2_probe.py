#!/usr/bin/env python3
# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later
"""TSUN Local / Sunology PLAY2 read-only super-probe.

One standalone Python 3.10+ script that combines the evidence-driven local
paths found while analysing Sunology STREAM 3.2.2 with the known TSUN local
protocol families used by TSUN Local.

The probe is intentionally READ-ONLY:
- no inverter/logger configuration writes;
- no Wi-Fi/BLE provisioning;
- no cloud login or authenticated Sunology API calls;
- no Modbus write functions;
- no WebSocket application messages are sent after the HTTP Upgrade request.

It produces both a detailed text log and a rich JSON report. Local identifiers
(IP addresses, Monitor SN, MAC addresses and serial-looking strings) are
redacted from both files while preserving packet structure, lengths, hashes,
field boundaries and protocol behaviour useful for reverse engineering.

Evidence-driven paths covered in one run:
1. iGEN/Solarman UDP discovery used by the Sunology provisioning SDK:
   smartlinkfind -> UDP/48899, response <- UDP/49999, plus legacy variants.
2. Detailed smart_config / ## parsing and candidate-IP correlation.
3. DNS-SD/mDNS _solarhome._tcp.local discovery used by Sunology Hub.
4. Read-only WebSocket handshake/listen on ws://<resolved-ip>:<port>/ws and
   JSON event inspection (solarEvent/pvP, batteryEvent, gridEvent, productInfo).
5. HTTP/HTTPS local identity checks on supplied/discovered candidates.
6. TCP/8899 passive observation plus bounded AP/Solarman envelope variants,
   sequence variants, 1511/02B0/1097/3026 reads, direct Modbus-RTU-over-TCP
   and Modbus-TCP read hypotheses.

No third-party Python packages are required.
"""
from __future__ import annotations

import argparse
import base64
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import http.client
from ipaddress import IPv4Address, ip_network
import json
import math
import os
from pathlib import Path
import platform
import re
import secrets
import socket
import ssl
import struct
import sys
import time
from typing import Any, Iterable

TOOL_VERSION = "1.2.0"
SCHEMA_VERSION = 3

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

MDNS_ADDR = "224.0.0.251"
MDNS_PORT = 5353
SOLARHOME_SERVICE = "_solarhome._tcp.local."
SUNOLOGY_HUB_PREFIX = "sunology-hb-"
WEBSOCKET_PATH = "/ws"
WEBSOCKET_ORIGINS: tuple[str | None, ...] = (None, "http://localhost", "capacitor://localhost")

HTTP_PATHS = ("/index_cn.html", "/index.html", "/status.html", "/")
HTTP_AUTH = base64.b64encode(b"admin:admin").decode("ascii")

MAX_UDP_PACKET = 8192
MAX_HTTP_PAGE = 512 * 1024
MAX_TCP_CAPTURE = 65536
MAX_CAPTURE_JSON_BYTES = 4096
MAX_MDNS_PACKET = 9000
MAX_MDNS_SERVICES = 8
MAX_CANDIDATES = 6
MAX_WS_EVENTS = 24
MAX_WS_TEXT = 16384

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
    re.compile(
        r"\b(?:software|sw|fw)[_-]?version[^A-Za-z0-9._-]+"
        r"([A-Za-z0-9][A-Za-z0-9._-]{0,79})",
        re.I,
    ),
)


class TeeLog:
    """Console + UTF-8 log file writer."""

    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = path.open("w", encoding="utf-8", newline="\n")

    def line(self, text: str = "") -> None:
        print(text)
        self._fh.write(text + "\n")
        self._fh.flush()

    def close(self) -> None:
        self._fh.close()


@dataclass
class Candidate:
    ip: str
    alias: str
    reasons: list[str] = field(default_factory=list)
    strong: bool = False


class CandidateBook:
    """Keep private IPs in memory and expose stable aliases in output."""

    def __init__(self, supplied_host: str):
        self._items: dict[str, Candidate] = {}
        self.add(supplied_host, "supplied_host", strong=True, preferred_alias="host0")

    def add(
        self,
        ip: str | None,
        reason: str,
        *,
        strong: bool = False,
        preferred_alias: str | None = None,
    ) -> Candidate | None:
        if not ip:
            return None
        try:
            IPv4Address(ip)
        except ValueError:
            return None
        if ip in self._items:
            item = self._items[ip]
            if reason not in item.reasons:
                item.reasons.append(reason)
            item.strong = item.strong or strong
            return item
        if len(self._items) >= MAX_CANDIDATES:
            return None
        alias = preferred_alias or f"candidate{len(self._items)}"
        item = Candidate(ip=ip, alias=alias, reasons=[reason], strong=strong)
        self._items[ip] = item
        return item

    def alias(self, ip: str | None) -> str | None:
        if not ip:
            return None
        item = self._items.get(ip)
        if item:
            return item.alias
        return "other-local-host"

    def get(self, ip: str) -> Candidate | None:
        return self._items.get(ip)

    def items(self) -> list[Candidate]:
        return list(self._items.values())

    def secrets(self) -> list[str]:
        return list(self._items.keys())


@dataclass
class DiscoveryReply:
    source: str
    source_port: int
    payload: bytes
    parsed: dict[str, Any]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


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
    try:
        number = float(value)
    except ValueError as err:
        raise argparse.ArgumentTypeError("value must be numeric") from err
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("value must be a finite number > 0")
    return number


def error_record(stage: str, err: BaseException, detail: str | None = None) -> dict[str, str]:
    return {
        "stage": stage,
        "type": type(err).__name__,
        "detail": detail or str(err) or type(err).__name__,
    }


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _replace_bytes_same_length(data: bytes, needle: bytes) -> bytes:
    if not needle:
        return data
    return data.replace(needle, b"*" * len(needle))


def redact_payload(payload: bytes, supplied_sn: int | None, ips: Iterable[str]) -> bytes:
    """Redact common textual/binary identifiers while preserving byte lengths."""
    data = bytes(payload)
    if supplied_sn is not None:
        sn_ascii = str(supplied_sn).encode("ascii")
        data = _replace_bytes_same_length(data, sn_ascii)
        data = _replace_bytes_same_length(data, supplied_sn.to_bytes(4, "little"))
        data = _replace_bytes_same_length(data, supplied_sn.to_bytes(4, "big"))
    for ip in ips:
        try:
            packed = socket.inet_aton(ip)
        except OSError:
            packed = b""
        data = _replace_bytes_same_length(data, ip.encode("ascii", errors="ignore"))
        if packed:
            data = _replace_bytes_same_length(data, packed)
    text = data.decode("latin-1", errors="ignore")
    for match in list(MAC_RE.finditer(text)):
        value = match.group(0).encode("latin-1", errors="ignore")
        data = _replace_bytes_same_length(data, value)
    return data


def redact_text(text: str, supplied_sn: int | None, ips: Iterable[str]) -> str:
    result = text
    if supplied_sn is not None:
        result = result.replace(str(supplied_sn), "<MONITOR_SN>")
    for ip in ips:
        result = result.replace(ip, "<LOCAL_IP>")
    result = MAC_RE.sub("<MAC>", result)
    result = SERIAL_RE.sub("<SERIAL>", result)
    return result


def visible_ascii(data: bytes, limit: int = MAX_CAPTURE_JSON_BYTES) -> str:
    chunk = data[:limit]
    out: list[str] = []
    for byte in chunk:
        if 32 <= byte <= 126:
            out.append(chr(byte))
        elif byte in (9, 10, 13):
            out.append({9: "\\t", 10: "\\n", 13: "\\r"}[byte])
        else:
            out.append(f"\\x{byte:02x}")
    if len(data) > limit:
        out.append(f"...<{len(data)-limit} bytes omitted>")
    return "".join(out)


def payload_evidence(payload: bytes, supplied_sn: int | None, ips: Iterable[str]) -> dict[str, Any]:
    redacted = redact_payload(payload, supplied_sn, ips)
    cap = redacted[:MAX_CAPTURE_JSON_BYTES]
    return {
        "length": len(payload),
        "sha256": sha256_hex(payload),
        "capture_complete": len(payload) <= MAX_CAPTURE_JSON_BYTES,
        "redacted_hex": cap.hex(),
        "redacted_ascii": visible_ascii(redacted),
        "printable_ratio": round(sum(32 <= b <= 126 for b in payload) / max(1, len(payload)), 3),
    }


def classify_field(field_text: str) -> str:
    value = field_text.strip()
    if not value:
        return "empty"
    if IP_RE.fullmatch(value):
        return "ipv4"
    if MAC_RE.fullmatch(value):
        return "mac"
    if value.isdigit():
        if 8 <= len(value) <= 10:
            return "serial_like_integer"
        return "integer"
    if all(32 <= ord(ch) <= 126 for ch in value):
        return "ascii"
    return "text"


def parse_smart_config(text: str, supplied_sn: int | None, ips: Iterable[str]) -> dict[str, Any] | None:
    lowered = text.lower()
    pos = lowered.find("smart_config")
    prefix = "smart_config"
    if pos < 0:
        pos = lowered.find("smartconfig")
        prefix = "smartconfig"
    if pos < 0:
        return None
    tail = text[pos + len(prefix):].strip("\x00\r\n ")
    while tail.startswith("#"):
        tail = tail[1:]
    fields = tail.split("##") if tail else []
    return {
        "prefix": prefix,
        "separator": "##",
        "field_count": len(fields),
        "fields": [
            {
                "index": index,
                "length": len(field),
                "class": classify_field(field),
                "value_redacted": redact_text(field, supplied_sn, ips),
            }
            for index, field in enumerate(fields)
        ],
    }


def parse_discovery_payload(payload: bytes) -> dict[str, Any]:
    text = payload.decode("utf-8", errors="replace").strip("\x00\r\n ")
    result: dict[str, Any] = {
        "format": "text",
        "sn": None,
        "ip": None,
        "mac": None,
        "length": len(payload),
        "text": text,
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
    return str(ip_network(f"{IPv4Address(host)}/24", strict=False).broadcast_address)


def udp_discovery_variant(
    *,
    name: str,
    host: str,
    bind_port: int,
    send_port: int,
    messages: Iterable[bytes],
    timeout: float,
    join_igen_multicast: bool = False,
) -> dict[str, Any]:
    messages = tuple(messages)
    destinations = (host, _broadcast_for_host(host), "255.255.255.255")
    replies: list[DiscoveryReply] = []
    seen: set[tuple[str, int, str]] = set()
    result: dict[str, Any] = {
        "name": name,
        "bind_port": bind_port,
        "send_port": send_port,
        "bound": False,
        "multicast_joined": False,
        "messages_sent": [message.decode("ascii", errors="replace") for message in messages],
        "send_attempts": 0,
        "send_errors": 0,
        "reply_count": 0,
        "error": None,
        "_private_replies": replies,
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

        if join_igen_multicast:
            try:
                membership = socket.inet_aton(IGEN_MULTICAST) + socket.inet_aton("0.0.0.0")
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membership)
                result["multicast_joined"] = True
            except OSError as err:
                result["multicast_error"] = error_record("join_igen_multicast", err)

        for cycle in range(2):
            for destination in destinations:
                for message in messages:
                    result["send_attempts"] += 1
                    try:
                        sock.sendto(message, (destination, send_port))
                    except OSError:
                        result["send_errors"] += 1
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
                result["error"] = error_record(f"recv_udp_{bind_port}", err)
                break
            if payload in messages:
                continue
            parsed = parse_discovery_payload(payload)
            key = (source, source_port, sha256_hex(payload))
            if key in seen:
                continue
            seen.add(key)
            replies.append(DiscoveryReply(source, source_port, payload, parsed))
            if settle_deadline is None:
                settle_deadline = time.monotonic() + 0.8
    finally:
        sock.close()

    result["reply_count"] = len(replies)
    return result


def run_udp_discovery(host: str, timeout: float) -> list[dict[str, Any]]:
    return [
        udp_discovery_variant(
            name="igen_smartlink_49999",
            host=host,
            bind_port=IGEN_RECV_PORT,
            send_port=IGEN_SEND_PORT,
            messages=(IGEN_MESSAGE,),
            timeout=timeout,
            join_igen_multicast=True,
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


def correlate_udp_candidates(
    variants: Iterable[dict[str, Any]],
    supplied_sn: int | None,
    book: CandidateBook,
) -> None:
    for variant in variants:
        for reply in variant.get("_private_replies", []):
            parsed = reply.parsed
            sn_match = supplied_sn is not None and parsed.get("sn") == supplied_sn
            if sn_match:
                book.add(reply.source, "udp_source_matches_monitor_sn", strong=True)
                book.add(parsed.get("ip"), "udp_declared_ip_matches_monitor_sn", strong=True)
            if parsed.get("format") == "smart_config_text":
                book.add(reply.source, "smart_config_source", strong=False)
                book.add(parsed.get("ip"), "smart_config_declared_ip", strong=False)


def public_udp_variant(
    variant: dict[str, Any],
    supplied_sn: int | None,
    book: CandidateBook,
) -> dict[str, Any]:
    public_replies: list[dict[str, Any]] = []
    secrets_list = book.secrets()
    for reply in variant.get("_private_replies", []):
        parsed = reply.parsed
        text = parsed.get("text", "")
        public_replies.append(
            {
                "source_alias": book.alias(reply.source),
                "source_port": reply.source_port,
                "declared_ip_alias": book.alias(parsed.get("ip")),
                "monitor_sn_present": parsed.get("sn") is not None,
                "monitor_sn_matches_supplied": supplied_sn is not None
                and parsed.get("sn") == supplied_sn,
                "mac_present": parsed.get("mac") is not None,
                "payload_format": parsed.get("format"),
                "payload": payload_evidence(reply.payload, supplied_sn, secrets_list),
                "smart_config": parse_smart_config(text, supplied_sn, secrets_list),
            }
        )
    return {
        key: value
        for key, value in variant.items()
        if key != "_private_replies"
    } | {"replies": public_replies}


# ---------------------------- mDNS / DNS-SD ----------------------------


def dns_encode_name(name: str) -> bytes:
    labels = name.rstrip(".").split(".")
    out = bytearray()
    for label in labels:
        encoded = label.encode("utf-8")
        if len(encoded) > 63:
            raise ValueError("DNS label too long")
        out.append(len(encoded))
        out.extend(encoded)
    out.append(0)
    return bytes(out)


def dns_query(name: str, qtype: int, *, unicast_response: bool = False) -> bytes:
    txid = 0
    flags = 0
    qdcount = 1
    header = struct.pack("!HHHHHH", txid, flags, qdcount, 0, 0, 0)
    qclass = 0x8001 if unicast_response else 1
    return header + dns_encode_name(name) + struct.pack("!HH", qtype, qclass)


def dns_read_name(data: bytes, offset: int, _depth: int = 0) -> tuple[str, int]:
    if _depth > 16:
        raise ValueError("DNS compression loop")
    labels: list[str] = []
    original_next: int | None = None
    while True:
        if offset >= len(data):
            raise ValueError("DNS name exceeds packet")
        length = data[offset]
        if length == 0:
            offset += 1
            break
        if length & 0xC0 == 0xC0:
            if offset + 1 >= len(data):
                raise ValueError("truncated DNS compression pointer")
            pointer = ((length & 0x3F) << 8) | data[offset + 1]
            if original_next is None:
                original_next = offset + 2
            pointed, _ = dns_read_name(data, pointer, _depth + 1)
            labels.append(pointed.rstrip("."))
            offset += 2
            break
        if length & 0xC0:
            raise ValueError("unsupported DNS label encoding")
        offset += 1
        if offset + length > len(data):
            raise ValueError("truncated DNS label")
        labels.append(data[offset : offset + length].decode("utf-8", errors="replace"))
        offset += length
    next_offset = original_next if original_next is not None else offset
    return ".".join(label for label in labels if label) + ".", next_offset


def parse_dns_packet(data: bytes) -> dict[str, Any]:
    if len(data) < 12:
        raise ValueError("DNS packet too short")
    txid, flags, qd, an, ns, ar = struct.unpack_from("!HHHHHH", data, 0)
    offset = 12
    questions: list[dict[str, Any]] = []
    for _ in range(qd):
        name, offset = dns_read_name(data, offset)
        if offset + 4 > len(data):
            raise ValueError("truncated DNS question")
        qtype, qclass = struct.unpack_from("!HH", data, offset)
        offset += 4
        questions.append({"name": name, "type": qtype, "class": qclass})

    records: list[dict[str, Any]] = []
    for section, count in (("answer", an), ("authority", ns), ("additional", ar)):
        for _ in range(count):
            name, offset = dns_read_name(data, offset)
            if offset + 10 > len(data):
                raise ValueError("truncated DNS RR")
            rtype, rclass, ttl, rdlength = struct.unpack_from("!HHIH", data, offset)
            offset += 10
            rstart = offset
            rend = offset + rdlength
            if rend > len(data):
                raise ValueError("truncated DNS RDATA")
            record: dict[str, Any] = {
                "section": section,
                "name": name,
                "type": rtype,
                "class": rclass & 0x7FFF,
                "cache_flush": bool(rclass & 0x8000),
                "ttl": ttl,
                "rdlength": rdlength,
            }
            try:
                if rtype == 12:
                    target, _ = dns_read_name(data, rstart)
                    record["ptr"] = target
                elif rtype == 33 and rdlength >= 6:
                    priority, weight, port = struct.unpack_from("!HHH", data, rstart)
                    target, _ = dns_read_name(data, rstart + 6)
                    record.update(
                        {"priority": priority, "weight": weight, "port": port, "target": target}
                    )
                elif rtype == 16:
                    cursor = rstart
                    txt: list[str] = []
                    while cursor < rend:
                        ln = data[cursor]
                        cursor += 1
                        txt.append(data[cursor : cursor + ln].decode("utf-8", errors="replace"))
                        cursor += ln
                    record["txt"] = txt
                elif rtype == 1 and rdlength == 4:
                    record["address"] = socket.inet_ntoa(data[rstart:rend])
                elif rtype == 28 and rdlength == 16:
                    record["address_v6"] = socket.inet_ntop(socket.AF_INET6, data[rstart:rend])
            except (ValueError, OSError, struct.error):
                record["decode_error"] = True
            records.append(record)
            offset = rend
    return {
        "id": txid,
        "flags": flags,
        "question_count": qd,
        "answer_count": an,
        "authority_count": ns,
        "additional_count": ar,
        "questions": questions,
        "records": records,
    }


def _mdns_socket(bind_5353: bool) -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if hasattr(socket, "SO_REUSEPORT"):
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except OSError:
            pass
    sock.bind(("", MDNS_PORT if bind_5353 else 0))
    if bind_5353:
        membership = socket.inet_aton(MDNS_ADDR) + socket.inet_aton("0.0.0.0")
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membership)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
    return sock


def mdns_discovery(timeout: float) -> dict[str, Any]:
    result: dict[str, Any] = {
        "service_type": SOLARHOME_SERVICE,
        "app_service_prefix": SUNOLOGY_HUB_PREFIX,
        "listen_mode": None,
        "bound_5353": False,
        "multicast_joined": False,
        "packets": [],
        "services": [],
        "errors": [],
    }
    sock: socket.socket | None = None
    try:
        try:
            sock = _mdns_socket(True)
            result["listen_mode"] = "multicast_5353"
            result["bound_5353"] = True
            result["multicast_joined"] = True
            query = dns_query(SOLARHOME_SERVICE, 12, unicast_response=False)
        except OSError as err:
            result["errors"].append(error_record("mdns_bind_5353", err))
            if sock is not None:
                sock.close()
            sock = _mdns_socket(False)
            result["listen_mode"] = "ephemeral_unicast_requested"
            query = dns_query(SOLARHOME_SERVICE, 12, unicast_response=True)

        sock.sendto(query, (MDNS_ADDR, MDNS_PORT))
        deadline = time.monotonic() + timeout
        raw_packets: list[tuple[bytes, str, int]] = []
        seen_hashes: set[str] = set()
        while (left := deadline - time.monotonic()) > 0:
            sock.settimeout(left)
            try:
                packet, (source, source_port) = sock.recvfrom(MAX_MDNS_PACKET)
            except socket.timeout:
                break
            except OSError as err:
                result["errors"].append(error_record("mdns_recv", err))
                break
            digest = sha256_hex(packet)
            if digest in seen_hashes:
                continue
            seen_hashes.add(digest)
            raw_packets.append((packet, source, source_port))
            if len(raw_packets) >= 32:
                break

        parsed_packets: list[dict[str, Any]] = []
        all_records: list[dict[str, Any]] = []
        for packet, source, source_port in raw_packets:
            try:
                parsed = parse_dns_packet(packet)
            except Exception as err:
                parsed_packets.append(
                    {
                        "source": source,
                        "source_port": source_port,
                        "length": len(packet),
                        "sha256": sha256_hex(packet),
                        "parse_error": error_record("parse_dns_packet", err),
                    }
                )
                continue
            parsed_packets.append(
                {
                    "source": source,
                    "source_port": source_port,
                    "length": len(packet),
                    "sha256": sha256_hex(packet),
                    "record_count": len(parsed["records"]),
                }
            )
            for record in parsed["records"]:
                record = dict(record)
                record["_source"] = source
                all_records.append(record)

        ptr_instances: list[str] = []
        for record in all_records:
            if record.get("type") == 12 and record.get("name", "").lower() == SOLARHOME_SERVICE.lower():
                ptr = record.get("ptr")
                if isinstance(ptr, str) and ptr not in ptr_instances:
                    ptr_instances.append(ptr)

        services: list[dict[str, Any]] = []
        for instance in ptr_instances[:MAX_MDNS_SERVICES]:
            srv = next(
                (
                    r
                    for r in all_records
                    if r.get("type") == 33 and r.get("name", "").lower() == instance.lower()
                ),
                None,
            )
            txt_records = [
                r
                for r in all_records
                if r.get("type") == 16 and r.get("name", "").lower() == instance.lower()
            ]
            target = srv.get("target") if srv else None
            port = srv.get("port") if srv else None
            addresses = [
                r.get("address")
                for r in all_records
                if r.get("type") == 1
                and target
                and r.get("name", "").lower() == str(target).lower()
                and r.get("address")
            ]
            if not addresses and target:
                try:
                    resolved = socket.gethostbyname(target.rstrip("."))
                    addresses.append(resolved)
                except OSError:
                    pass
            services.append(
                {
                    "instance": instance,
                    "is_sunology_hub_name": instance.lower().startswith(SUNOLOGY_HUB_PREFIX),
                    "target": target,
                    "port": port,
                    "addresses": list(dict.fromkeys(addresses)),
                    "txt": [item for record in txt_records for item in record.get("txt", [])],
                }
            )
        result["_private_packets"] = parsed_packets
        result["_private_services"] = services
        return result
    except Exception as err:
        result["errors"].append(error_record("mdns_discovery", err))
        result["_private_packets"] = []
        result["_private_services"] = []
        return result
    finally:
        if sock is not None:
            sock.close()


def public_mdns(result: dict[str, Any], supplied_sn: int | None, book: CandidateBook) -> dict[str, Any]:
    ips = book.secrets()
    services: list[dict[str, Any]] = []
    for service in result.get("_private_services", []):
        service_name = redact_text(service.get("instance") or "", supplied_sn, ips)
        target = redact_text(service.get("target") or "", supplied_sn, ips) or None
        aliases = [book.alias(ip) for ip in service.get("addresses", [])]
        services.append(
            {
                "instance_redacted": service_name,
                "instance_sha256": sha256_hex((service.get("instance") or "").encode()),
                "is_sunology_hub_name": service.get("is_sunology_hub_name"),
                "target_redacted": target,
                "port": service.get("port"),
                "address_aliases": aliases,
                "txt_redacted": [redact_text(v, supplied_sn, ips) for v in service.get("txt", [])],
            }
        )
    packets = []
    for packet in result.get("_private_packets", []):
        packets.append(
            {
                "source_alias": book.alias(packet.get("source")),
                "source_port": packet.get("source_port"),
                "length": packet.get("length"),
                "sha256": packet.get("sha256"),
                "record_count": packet.get("record_count"),
                "parse_error": packet.get("parse_error"),
            }
        )
    return {
        key: value
        for key, value in result.items()
        if not key.startswith("_private_")
    } | {"packets": packets, "services": services}


# ---------------------------- WebSocket ----------------------------


def recv_http_headers(sock: socket.socket, timeout: float, max_bytes: int = 16384) -> bytes:
    sock.settimeout(timeout)
    data = bytearray()
    while b"\r\n\r\n" not in data and len(data) < max_bytes:
        chunk = sock.recv(2048)
        if not chunk:
            break
        data.extend(chunk)
    return bytes(data)


def websocket_handshake(host: str, port: int, timeout: float, origin: str | None) -> tuple[socket.socket | None, dict[str, Any]]:
    result: dict[str, Any] = {
        "origin_variant": origin or "none",
        "tcp_connected": False,
        "request_sent": False,
        "http_status": None,
        "upgrade_websocket": False,
        "accept_valid": False,
        "headers": {},
        "error": None,
    }
    sock: socket.socket | None = None
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        result["tcp_connected"] = True
        key = base64.b64encode(secrets.token_bytes(16)).decode("ascii")
        lines = [
            f"GET {WEBSOCKET_PATH} HTTP/1.1",
            f"Host: {host}:{port}",
            "Upgrade: websocket",
            "Connection: Upgrade",
            f"Sec-WebSocket-Key: {key}",
            "Sec-WebSocket-Version: 13",
            "User-Agent: TSUN-Local-PLAY2-Probe",
        ]
        if origin:
            lines.append(f"Origin: {origin}")
        request = ("\r\n".join(lines) + "\r\n\r\n").encode("ascii")
        sock.sendall(request)
        result["request_sent"] = True
        response = recv_http_headers(sock, timeout)
        head = response.decode("iso-8859-1", errors="replace")
        header_text, _, extra = head.partition("\r\n\r\n")
        lines_in = header_text.split("\r\n")
        if lines_in:
            parts = lines_in[0].split(" ", 2)
            if len(parts) >= 2 and parts[1].isdigit():
                result["http_status"] = int(parts[1])
        headers: dict[str, str] = {}
        for line in lines_in[1:]:
            if ":" not in line:
                continue
            name, value = line.split(":", 1)
            headers[name.strip().lower()] = value.strip()
        safe_header_names = ("upgrade", "connection", "server", "sec-websocket-protocol")
        result["headers"] = {name: headers[name] for name in safe_header_names if name in headers}
        result["upgrade_websocket"] = result["http_status"] == 101 and headers.get("upgrade", "").lower() == "websocket"
        expected_accept = base64.b64encode(
            hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode("ascii")).digest()
        ).decode("ascii")
        result["accept_valid"] = headers.get("sec-websocket-accept") == expected_accept
        if extra:
            result["extra_after_headers_length"] = len(extra.encode("iso-8859-1", errors="replace"))
        if result["upgrade_websocket"]:
            return sock, result
        sock.close()
        return None, result
    except (OSError, ValueError) as err:
        result["error"] = error_record("websocket_handshake", err)
        if sock is not None:
            sock.close()
        return None, result


def recv_exact_optional(sock: socket.socket, count: int) -> bytes | None:
    data = bytearray()
    while len(data) < count:
        chunk = sock.recv(count - len(data))
        if not chunk:
            return None
        data.extend(chunk)
    return bytes(data)


def read_ws_frame(sock: socket.socket, timeout: float) -> dict[str, Any] | None:
    sock.settimeout(timeout)
    try:
        head = recv_exact_optional(sock, 2)
    except socket.timeout:
        return None
    if not head:
        return None
    b0, b1 = head
    fin = bool(b0 & 0x80)
    opcode = b0 & 0x0F
    masked = bool(b1 & 0x80)
    length = b1 & 0x7F
    if length == 126:
        ext = recv_exact_optional(sock, 2)
        if not ext:
            return None
        length = int.from_bytes(ext, "big")
    elif length == 127:
        ext = recv_exact_optional(sock, 8)
        if not ext:
            return None
        length = int.from_bytes(ext, "big")
    if length > MAX_TCP_CAPTURE:
        raise ValueError("WebSocket frame too large for diagnostic")
    mask = recv_exact_optional(sock, 4) if masked else None
    payload = recv_exact_optional(sock, length) if length else b""
    if payload is None:
        return None
    if masked and mask:
        payload = bytes(value ^ mask[index % 4] for index, value in enumerate(payload))
    return {"fin": fin, "opcode": opcode, "masked": masked, "payload": payload}


def extract_json_signals(value: Any) -> dict[str, Any]:
    signals: dict[str, Any] = {"keys": [], "interesting": {}}
    interesting_names = {
        "event",
        "pvP",
        "power",
        "production",
        "deviceState",
        "batteryPower",
        "gridPower",
        "soc",
        "serialNumber",
        "id",
    }

    def walk(obj: Any, prefix: str = "", depth: int = 0) -> None:
        if depth > 5:
            return
        if isinstance(obj, dict):
            for key, item in obj.items():
                path = f"{prefix}.{key}" if prefix else str(key)
                if len(signals["keys"]) < 80:
                    signals["keys"].append(path)
                if key in interesting_names and isinstance(item, (str, int, float, bool, type(None))):
                    signals["interesting"][path] = item
                walk(item, path, depth + 1)
        elif isinstance(obj, list):
            for index, item in enumerate(obj[:8]):
                walk(item, f"{prefix}[{index}]", depth + 1)

    walk(value)
    return signals


def websocket_listen(
    host: str,
    port: int,
    timeout: float,
    listen_seconds: float,
    supplied_sn: int | None,
    book: CandidateBook,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "address_alias": book.alias(host),
        "port": port,
        "path": WEBSOCKET_PATH,
        "handshake_attempts": [],
        "connected": False,
        "events": [],
        "close_or_timeout": None,
    }
    sock: socket.socket | None = None
    try:
        for origin in WEBSOCKET_ORIGINS:
            candidate_sock, handshake = websocket_handshake(host, port, timeout, origin)
            result["handshake_attempts"].append(handshake)
            if candidate_sock is not None:
                sock = candidate_sock
                result["connected"] = True
                break
        if sock is None:
            return result

        deadline = time.monotonic() + listen_seconds
        while len(result["events"]) < MAX_WS_EVENTS and (left := deadline - time.monotonic()) > 0:
            try:
                frame = read_ws_frame(sock, min(left, 2.0))
            except socket.timeout:
                continue
            except (OSError, ValueError) as err:
                result["close_or_timeout"] = error_record("websocket_receive", err)
                break
            if frame is None:
                continue
            payload = frame.pop("payload")
            record: dict[str, Any] = {
                **frame,
                "payload": payload_evidence(payload, supplied_sn, book.secrets()),
            }
            if frame["opcode"] == 1:
                text = payload[:MAX_WS_TEXT].decode("utf-8", errors="replace")
                record["text_redacted"] = redact_text(text, supplied_sn, book.secrets())
                try:
                    obj = json.loads(text)
                except (TypeError, ValueError):
                    obj = None
                if obj is not None:
                    signals = extract_json_signals(obj)
                    for key, value in list(signals["interesting"].items()):
                        if isinstance(value, str):
                            signals["interesting"][key] = redact_text(value, supplied_sn, book.secrets())
                    record["json_valid"] = True
                    record["json_signals"] = signals
                else:
                    record["json_valid"] = False
            elif frame["opcode"] == 8:
                result["close_or_timeout"] = "server_close_frame"
            elif frame["opcode"] == 9:
                record["note"] = "ping observed; no pong sent by read-only probe"
            result["events"].append(record)
            if frame["opcode"] == 8:
                break
        if result["close_or_timeout"] is None:
            result["close_or_timeout"] = "listen_window_complete"
        return result
    finally:
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass


# ---------------------------- HTTP identity ----------------------------


def port_open(host: str, port: int, timeout: float) -> tuple[bool, float, str | None]:
    started = time.monotonic()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True, round((time.monotonic() - started) * 1000, 1), None
    except OSError as err:
        return False, round((time.monotonic() - started) * 1000, 1), type(err).__name__


def http_get(
    host: str,
    port: int,
    path: str,
    timeout: float,
    *,
    tls: bool,
    auth: bool,
) -> dict[str, Any]:
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
    started = time.monotonic()
    try:
        connection.request("GET", path, headers=headers)
        response = connection.getresponse()
        body = response.read(MAX_HTTP_PAGE + 1)
        too_large = len(body) > MAX_HTTP_PAGE
        if too_large:
            body = body[:MAX_HTTP_PAGE]
        return {
            "status": response.status,
            "reason": response.reason,
            "elapsed_ms": round((time.monotonic() - started) * 1000, 1),
            "content_type": response.getheader("Content-Type"),
            "content_length_header": response.getheader("Content-Length"),
            "server": response.getheader("Server"),
            "www_authenticate_present": response.getheader("WWW-Authenticate") is not None,
            "body": body,
            "body_too_large": too_large,
            "error": None,
        }
    except (OSError, ssl.SSLError, http.client.HTTPException) as err:
        return {
            "status": None,
            "elapsed_ms": round((time.monotonic() - started) * 1000, 1),
            "body": b"",
            "error": error_record("http_get", err),
        }
    finally:
        connection.close()


def firmware_versions(document: str) -> list[str]:
    versions: list[str] = []
    for pattern in FW_PATTERNS:
        for match in pattern.finditer(document):
            version = match.group(1).strip().strip("\"'")
            if version and version not in versions:
                versions.append(version)
    return versions


def html_title(document: str) -> str | None:
    match = re.search(r"<title[^>]*>(.*?)</title>", document, re.I | re.S)
    if not match:
        return None
    title = re.sub(r"\s+", " ", match.group(1)).strip()
    return title[:200] or None


def web_identity(host: str, timeout: float, supplied_sn: int | None, book: CandidateBook) -> dict[str, Any]:
    result: dict[str, Any] = {"address_alias": book.alias(host), "firmware_versions": [], "transports": []}
    for port, tls, scheme in ((80, False, "http"), (443, True, "https")):
        reachable, elapsed_ms, connect_error = port_open(host, port, min(timeout, 1.5))
        transport: dict[str, Any] = {
            "scheme": scheme,
            "port": port,
            "tcp_open": reachable,
            "connect_elapsed_ms": elapsed_ms,
            "connect_error": connect_error,
            "pages": [],
        }
        if not reachable:
            result["transports"].append(transport)
            continue
        for path in HTTP_PATHS:
            attempts = []
            for auth in (False, True):
                if auth and attempts and attempts[0].get("status") not in (401, 403):
                    break
                response = http_get(host, port, path, timeout, tls=tls, auth=auth)
                body = response.pop("body", b"")
                text = body.decode("utf-8", errors="replace") if body else ""
                versions = firmware_versions(text)
                for version in versions:
                    if version not in result["firmware_versions"]:
                        result["firmware_versions"].append(version)
                response.update(
                    {
                        "authenticated": auth,
                        "body_length": len(body),
                        "body_sha256": sha256_hex(body) if body else None,
                        "title_redacted": redact_text(html_title(text) or "", supplied_sn, book.secrets()) or None,
                        "firmware_versions": versions,
                        "body_prefix_redacted": redact_text(text[:800], supplied_sn, book.secrets()) if text else None,
                    }
                )
                attempts.append(response)
            transport["pages"].append({"path": path, "attempts": attempts})
        result["transports"].append(transport)
    return result


# ---------------------------- TCP 8899 ----------------------------


def checksum_ap(data: bytes) -> int:
    return sum(data) & 0xFF


def build_ap(
    sn: int,
    payload: bytes,
    sensor_list: int = 0,
    *,
    control: int = 0x4510,
    sequence: int = 0,
    frame_type: int = 0x02,
) -> bytes:
    if not 0 <= sn <= 0xFFFFFFFF:
        raise ValueError("Monitor SN must fit four bytes")
    if not 0 <= sensor_list <= 0xFFFF:
        raise ValueError("sensor_list must fit two bytes")
    if not 0 <= control <= 0xFFFF or not 0 <= sequence <= 0xFFFF:
        raise ValueError("control/sequence must fit two bytes")
    data = bytes((frame_type,)) + sensor_list.to_bytes(2, "little") + bytes(12) + payload
    scope = (
        len(data).to_bytes(2, "little")
        + control.to_bytes(2, "little")
        + sequence.to_bytes(2, "little")
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


def modbus_rtu(start: int, end: int, unit: int = 1) -> bytes:
    count = end - start + 1
    if not 1 <= count <= 125:
        raise ValueError("Modbus FC03 register count must be 1..125")
    body = bytes((unit, 0x03)) + start.to_bytes(2, "big") + count.to_bytes(2, "big")
    return body + crc_modbus(body)


def modbus_tcp(start: int, end: int, transaction: int = 1, unit: int = 1) -> bytes:
    count = end - start + 1
    pdu = bytes((0x03,)) + start.to_bytes(2, "big") + count.to_bytes(2, "big")
    return struct.pack("!HHHB", transaction, 0, len(pdu) + 1, unit) + pdu


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


def recv_until_quiet(sock: socket.socket, timeout: float) -> tuple[bytes, str, float]:
    started = time.monotonic()
    deadline = started + timeout
    data = bytearray()
    outcome = "timeout_no_data"
    while len(data) < MAX_TCP_CAPTURE:
        left = deadline - time.monotonic()
        if left <= 0:
            outcome = "timeout_after_data" if data else "timeout_no_data"
            break
        sock.settimeout(min(left, 0.5 if data else left))
        try:
            chunk = sock.recv(min(4096, MAX_TCP_CAPTURE - len(data)))
        except socket.timeout:
            if data:
                outcome = "quiet_after_data"
                break
            continue
        except ConnectionResetError:
            outcome = "connection_reset_after_data" if data else "connection_reset"
            break
        except OSError:
            outcome = "socket_error_after_data" if data else "socket_error"
            break
        if not chunk:
            outcome = "peer_closed_after_data" if data else "peer_closed"
            break
        data.extend(chunk)
    if len(data) >= MAX_TCP_CAPTURE:
        outcome = "capture_limit_reached"
    return bytes(data), outcome, round((time.monotonic() - started) * 1000, 1)


def analyze_ap_response(data: bytes, supplied_sn: int | None) -> dict[str, Any]:
    result: dict[str, Any] = {"starts_a5": bool(data and data[0] == 0xA5)}
    if len(data) < 3 or data[0] != 0xA5:
        return result
    declared = int.from_bytes(data[1:3], "little")
    expected_total = declared + 13
    result.update(
        {
            "declared_data_length": declared,
            "expected_total_length": expected_total,
            "length_valid": len(data) == expected_total,
        }
    )
    if len(data) >= 11:
        control = int.from_bytes(data[3:5], "little")
        sequence = int.from_bytes(data[5:7], "little")
        response_sn = int.from_bytes(data[7:11], "little")
        result.update(
            {
                "control": f"0x{control:04X}",
                "sequence": f"0x{sequence:04X}",
                "monitor_sn_present": valid_sn(response_sn),
                "monitor_sn_matches_supplied": supplied_sn is not None and response_sn == supplied_sn,
            }
        )
    if len(data) >= 13:
        result["frame_type"] = data[11]
        result["status"] = data[12]
    if len(data) >= 2:
        result["end_marker_valid"] = data[-1] == 0x15
        result["checksum_valid"] = checksum_ap(data[1:-2]) == data[-2] if len(data) >= 3 else False
    return result


def tcp_probe(
    host: str,
    request: bytes | None,
    timeout: float,
    *,
    supplied_sn: int | None,
    book: CandidateBook,
    name: str,
    request_meta: dict[str, Any] | None = None,
    passive_wait: float | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "name": name,
        "address_alias": book.alias(host),
        "connected": False,
        "request_sent": False,
        "request_length": len(request) if request is not None else 0,
        "request_meta": request_meta or {},
        "response_length": 0,
        "outcome": None,
        "error": None,
    }
    started = time.monotonic()
    try:
        with socket.create_connection((host, TCP_PORT), timeout=timeout) as sock:
            result["connected"] = True
            result["connect_elapsed_ms"] = round((time.monotonic() - started) * 1000, 1)
            if request is not None:
                sock.sendall(request)
                result["request_sent"] = True
            wait = passive_wait if passive_wait is not None else timeout
            response, outcome, elapsed = recv_until_quiet(sock, wait)
            result["receive_elapsed_ms"] = elapsed
            result["outcome"] = outcome
            result["response_length"] = len(response)
            if response:
                result["response"] = payload_evidence(response, supplied_sn, book.secrets())
                result["ap_analysis"] = analyze_ap_response(response, supplied_sn)
            return result
    except OSError as err:
        result["connect_elapsed_ms"] = round((time.monotonic() - started) * 1000, 1)
        result["error"] = error_record("tcp_8899", err)
        result["outcome"] = "connect_error"
        return result


def ap_probe_matrix(sn: int) -> list[tuple[str, bytes, dict[str, Any]]]:
    reads = [
        ("1511_status", req_1511(0xA1, 0x01, 0x0BB8, 0x0BB8), 0x0000, "1511"),
        ("1511_status_sl1511", req_1511(0xA1, 0x01, 0x0BB8, 0x0BB8), 0x1511, "1511"),
        ("1511_profile_a1_21", req_1511(0xA1, 0x21, 0x07D0, 0x07D0), 0x0000, "1511"),
        ("02b0_status", modbus_rtu(0x3000, 0x3000), 0x0000, "02b0"),
        ("02b0_status_sl02b0", modbus_rtu(0x3000, 0x3000), 0x02B0, "02b0"),
        ("1097_status", modbus_rtu(0x1100, 0x1100), 0x1097, "1097"),
        ("1097_status_sl0000", modbus_rtu(0x1100, 0x1100), 0x0000, "1097"),
        ("1097_info", modbus_rtu(0x1008, 0x100F), 0x1097, "1097"),
        ("3026_detection", modbus_rtu(0x0000, 0x002C), 0x3026, "3026"),
        ("3026_detection_sl0000", modbus_rtu(0x0000, 0x002C), 0x0000, "3026"),
    ]
    matrix: list[tuple[str, bytes, dict[str, Any]]] = []
    for label, payload, sensor_list, family in reads:
        meta = {
            "family": family,
            "sensor_list": f"0x{sensor_list:04X}",
            "control": "0x4510",
            "sequence": "0x0000",
            "monitor_sn_zero": sn == 0,
        }
        matrix.append((f"ap_{label}_seq0000", build_ap(sn, payload, sensor_list, sequence=0x0000), meta))
    sequence_reads = [reads[0], reads[3], reads[5], reads[8]]
    for label, payload, sensor_list, family in sequence_reads:
        for sequence in (0x0100, 0x0001):
            meta = {
                "family": family,
                "sensor_list": f"0x{sensor_list:04X}",
                "control": "0x4510",
                "sequence": f"0x{sequence:04X}",
                "monitor_sn_zero": sn == 0,
            }
            matrix.append(
                (
                    f"ap_{label}_seq{sequence:04x}",
                    build_ap(sn, payload, sensor_list, sequence=sequence),
                    meta,
                )
            )
    return matrix


def direct_8899_matrix() -> list[tuple[str, bytes, dict[str, Any]]]:
    return [
        (
            "direct_modbus_rtu_02b0_3000",
            modbus_rtu(0x3000, 0x3000),
            {"hypothesis": "raw_modbus_rtu_over_tcp", "family_hint": "02b0"},
        ),
        (
            "direct_modbus_rtu_1097_1100",
            modbus_rtu(0x1100, 0x1100),
            {"hypothesis": "raw_modbus_rtu_over_tcp", "family_hint": "1097"},
        ),
        (
            "direct_modbus_tcp_3000",
            modbus_tcp(0x3000, 0x3000),
            {"hypothesis": "modbus_tcp_mbap", "family_hint": "02b0"},
        ),
        (
            "direct_modbus_tcp_1100",
            modbus_tcp(0x1100, 0x1100),
            {"hypothesis": "modbus_tcp_mbap", "family_hint": "1097"},
        ),
        (
            "direct_1511_native",
            req_1511(0xA1, 0x01, 0x0BB8, 0x0BB8),
            {"hypothesis": "1511_native_without_ap_envelope", "family_hint": "1511"},
        ),
    ]


def run_8899(host: str, sn: int | None, timeout: float, book: CandidateBook, full: bool) -> dict[str, Any]:
    open_, elapsed, connect_error = port_open(host, TCP_PORT, min(timeout, 1.5))
    result: dict[str, Any] = {
        "address_alias": book.alias(host),
        "open": open_,
        "connect_elapsed_ms": elapsed,
        "connect_error": connect_error,
        "probes": [],
    }
    if not open_:
        return result

    result["probes"].append(
        tcp_probe(
            host,
            None,
            timeout,
            supplied_sn=sn,
            book=book,
            name="passive_listen",
            passive_wait=min(2.0, timeout),
        )
    )

    zero_reads = [
        ("zero_sn_1511", req_1511(0xA1, 0x01, 0x0BB8, 0x0BD0), 0x0000),
        ("zero_sn_02b0", modbus_rtu(0x3009, 0x301E), 0x02B0),
        ("zero_sn_1097", modbus_rtu(0x1100, 0x1100), 0x1097),
        ("zero_sn_3026", modbus_rtu(0x0000, 0x002C), 0x3026),
    ]
    for label, payload, sensor_list in zero_reads:
        for sequence in ((0x0000, 0x0100) if full else (0x0100,)):
            request = build_ap(0, payload, sensor_list, sequence=sequence)
            result["probes"].append(
                tcp_probe(
                    host,
                    request,
                    timeout,
                    supplied_sn=sn,
                    book=book,
                    name=f"{label}_seq{sequence:04x}",
                    request_meta={
                        "monitor_sn_zero": True,
                        "sensor_list": f"0x{sensor_list:04X}",
                        "control": "0x4510",
                        "sequence": f"0x{sequence:04X}",
                    },
                )
            )

    if sn is not None:
        matrix = ap_probe_matrix(sn)
        if not full:
            keep = {"ap_1511_status_seq0100", "ap_02b0_status_seq0100", "ap_1097_status_seq0100", "ap_3026_detection_seq0100"}
            matrix = [item for item in matrix if item[0] in keep]
        for name, request, meta in matrix:
            result["probes"].append(
                tcp_probe(
                    host,
                    request,
                    timeout,
                    supplied_sn=sn,
                    book=book,
                    name=name,
                    request_meta=meta,
                )
            )

    for name, request, meta in direct_8899_matrix():
        if not full and name not in ("direct_modbus_rtu_02b0_3000", "direct_modbus_tcp_3000"):
            continue
        result["probes"].append(
            tcp_probe(
                host,
                request,
                timeout,
                supplied_sn=sn,
                book=book,
                name=name,
                request_meta=meta,
            )
        )
    return result


# ---------------------------- report ----------------------------


def empty_document() -> dict[str, Any]:
    return {
        "format": "tsun-local-play2-superprobe",
        "schema_version": SCHEMA_VERSION,
        "metadata": {
            "timestamp_utc": utc_now(),
            "tool_version": TOOL_VERSION,
            "python_required": ">=3.10",
            "python_runtime": platform.python_version(),
            "platform": platform.system(),
            "read_only": True,
            "configuration_writes": 0,
            "modbus_write_functions": 0,
            "cloud_requests_performed": 0,
            "privacy": {
                "local_ips": "aliased",
                "monitor_sn": "redacted",
                "mac": "redacted",
                "packet_payloads": "structure-preserving redacted + SHA-256",
            },
            "apk_evidence": {
                "version": "Sunology STREAM 3.2.2",
                "provisioning_sdk_check": "https://pro.solarmanpv.com/deviceConfig-s/sdk/check",
                "provisioning_sdk_id": "SDK_Config_Ble",
                "smartlink_request": "smartlinkfind",
                "smartlink_send_udp": 48899,
                "smart_config_receive_udp": 49999,
                "smart_config_prefix": "smart_config",
                "smart_config_separator": "##",
                "hub_mdns_type": "_solarhome._tcp.",
                "hub_mdns_domain": "local.",
                "hub_service_prefix": "sunology-hb-",
                "hub_websocket_path": "/ws",
                "hub_websocket_payload": "JSON text",
                "ui_backend_path": "/api/overview",
                "ui_backend_note": "normal Overview telemetry is cloud-backed; Hub can provide local real-time events",
                "local_mock_only": "ws://127.0.0.1:20199",
            },
        },
        "candidates": [],
        "udp_discovery": {"variants": []},
        "mdns_solarhome": {},
        "websocket": [],
        "web_identity": [],
        "tcp_8899": [],
        "phase_errors": [],
        "summary": {},
    }


def write_json(document: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def summarize(document: dict[str, Any]) -> dict[str, Any]:
    udp_replies = sum(v.get("reply_count", 0) for v in document["udp_discovery"].get("variants", []))
    smart_config = sum(
        1
        for variant in document["udp_discovery"].get("variants", [])
        for reply in variant.get("replies", [])
        if reply.get("payload_format") == "smart_config_text"
    )
    mdns_services = len(document.get("mdns_solarhome", {}).get("services", []))
    ws_connected = sum(1 for item in document.get("websocket", []) if item.get("connected"))
    ws_events = sum(len(item.get("events", [])) for item in document.get("websocket", []))
    open_8899 = sum(1 for item in document.get("tcp_8899", []) if item.get("open"))
    replies_8899 = sum(
        1
        for item in document.get("tcp_8899", [])
        for probe in item.get("probes", [])
        if probe.get("response_length", 0) > 0
    )
    return {
        "udp_reply_count": udp_replies,
        "smart_config_reply_count": smart_config,
        "mdns_solarhome_services": mdns_services,
        "websocket_connections": ws_connected,
        "websocket_frames": ws_events,
        "tcp_8899_open_candidates": open_8899,
        "tcp_8899_probes_with_bytes": replies_8899,
        "candidate_count": len(document.get("candidates", [])),
        "phase_error_count": len(document.get("phase_errors", [])),
    }


def main() -> int:
    if sys.version_info < (3, 10):
        print("ERROR: Python 3.10 or newer is required.", file=sys.stderr)
        return 2

    parser = argparse.ArgumentParser(
        description="TSUN Local Sunology PLAY2 read-only all-in-one diagnostic super-probe"
    )
    parser.add_argument("--host", required=True, help="known/candidate PLAY2 IPv4 address")
    parser.add_argument(
        "--monitor-sn",
        "--serial",
        dest="sn",
        type=arg_sn,
        help="Monitor SN; strongly recommended for candidate correlation",
    )
    parser.add_argument("--udp-timeout", type=arg_float, default=4.0)
    parser.add_argument("--mdns-timeout", type=arg_float, default=10.0)
    parser.add_argument("--ws-listen", type=arg_float, default=10.0)
    parser.add_argument("--timeout", type=arg_float, default=2.0, help="TCP/8899 per-probe timeout")
    parser.add_argument("--http-timeout", type=arg_float, default=2.0)
    parser.add_argument("--output", type=Path, help="JSON output path; .log is written beside it")
    args = parser.parse_args()

    try:
        IPv4Address(args.host)
    except ValueError:
        print("ERROR: --host must be an IPv4 address.", file=sys.stderr)
        return 2

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = args.output or Path(f"tsun_play2_superprobe_{stamp}.json")
    log_path = json_path.with_suffix(".log")
    log = TeeLog(log_path)
    document = empty_document()
    book = CandidateBook(args.host)

    log.line(f"TSUN Local PLAY2 Super-Probe v{TOOL_VERSION} · READ-ONLY")
    log.line("One run: UDP/iGEN + smart_config + mDNS/DNS-SD + WebSocket + HTTP(S) + TCP/8899")
    log.line("No cloud request, no BLE provisioning, no configuration write, no Modbus write.")
    log.line("APK note: ws://127.0.0.1:20199 is a development mock only; it is not probed.")
    log.line()

    log.line("[1/5] Sunology/iGEN UDP discovery")
    udp_variants: list[dict[str, Any]] = []
    try:
        udp_variants = run_udp_discovery(args.host, args.udp_timeout)
        correlate_udp_candidates(udp_variants, args.sn, book)
        document["udp_discovery"]["variants"] = [
            public_udp_variant(variant, args.sn, book) for variant in udp_variants
        ]
        for variant, public in zip(udp_variants, document["udp_discovery"]["variants"]):
            log.line(f"  {variant['name']}: replies={variant['reply_count']} bound={variant['bound']}")
            for reply in public["replies"]:
                log.line(
                    "    "
                    f"source={reply['source_alias']}:{reply['source_port']} "
                    f"format={reply['payload_format']} len={reply['payload']['length']} "
                    f"SN-match={reply['monitor_sn_matches_supplied']}"
                )
                if reply.get("smart_config"):
                    log.line(
                        f"      smart_config fields={reply['smart_config']['field_count']} "
                        f"separator={reply['smart_config']['separator']}"
                    )
    except Exception as err:
        document["phase_errors"].append(error_record("udp_discovery", err))
        log.line(f"  ERROR: {type(err).__name__}: {err}")

    log.line()
    log.line("[2/5] mDNS/DNS-SD _solarhome._tcp.local (Sunology Hub path from app)")
    mdns_private: dict[str, Any] = {}
    try:
        mdns_private = mdns_discovery(args.mdns_timeout)
        for service in mdns_private.get("_private_services", []):
            for ip in service.get("addresses", []):
                book.add(ip, "mdns_solarhome_service", strong=False)
        document["mdns_solarhome"] = public_mdns(mdns_private, args.sn, book)
        log.line(
            f"  services={len(document['mdns_solarhome'].get('services', []))} "
            f"listen_mode={document['mdns_solarhome'].get('listen_mode')}"
        )
        for service in document["mdns_solarhome"].get("services", []):
            log.line(
                f"    {service['instance_redacted']} port={service['port']} "
                f"addresses={service['address_aliases']} hub-name={service['is_sunology_hub_name']}"
            )
    except Exception as err:
        document["phase_errors"].append(error_record("mdns", err))
        log.line(f"  ERROR: {type(err).__name__}: {err}")

    document["candidates"] = [
        {"alias": item.alias, "reasons": item.reasons, "strong": item.strong}
        for item in book.items()
    ]
    log.line("  Candidate hosts: " + ", ".join(item.alias for item in book.items()))

    log.line()
    log.line("[3/5] Local WebSocket ws://<mDNS-address>:<port>/ws")
    try:
        for service in mdns_private.get("_private_services", [])[:MAX_MDNS_SERVICES]:
            port = service.get("port")
            if not isinstance(port, int) or not (1 <= port <= 65535):
                continue
            for ip in service.get("addresses", [])[:2]:
                ws = websocket_listen(ip, port, args.timeout, args.ws_listen, args.sn, book)
                document["websocket"].append(ws)
                log.line(
                    f"  {book.alias(ip)}:{port}/ws connected={ws['connected']} "
                    f"frames={len(ws['events'])}"
                )
                for event in ws["events"]:
                    signals = event.get("json_signals", {}).get("interesting", {})
                    if signals:
                        log.line(f"    JSON signals: {signals}")
        if not document["websocket"]:
            log.line("  No _solarhome._tcp endpoint resolved; WebSocket test not applicable.")
    except Exception as err:
        document["phase_errors"].append(error_record("websocket", err))
        log.line(f"  ERROR: {type(err).__name__}: {err}")

    log.line()
    log.line("[4/5] HTTP/HTTPS local identity on candidate hosts")
    for candidate in book.items():
        try:
            web = web_identity(candidate.ip, args.http_timeout, args.sn, book)
            document["web_identity"].append(web)
            open_schemes = [t["scheme"] for t in web["transports"] if t["tcp_open"]]
            log.line(
                f"  {candidate.alias}: web={','.join(open_schemes) or 'none'} "
                f"firmware={web['firmware_versions'] or 'not-found'}"
            )
        except Exception as err:
            document["phase_errors"].append(error_record(f"web_identity_{candidate.alias}", err))
            log.line(f"  {candidate.alias}: ERROR {type(err).__name__}: {err}")

    log.line()
    log.line("[5/5] TCP/8899 passive + AP sequence variants + protocol/direct-read hypotheses")
    for candidate in book.items():
        full = candidate.strong or candidate.alias == "host0"
        try:
            report = run_8899(candidate.ip, args.sn, args.timeout, book, full=full)
            document["tcp_8899"].append(report)
            responding = [p for p in report.get("probes", []) if p.get("response_length", 0) > 0]
            log.line(
                f"  {candidate.alias}: open={report['open']} full-matrix={full} "
                f"probes={len(report.get('probes', []))} replies-with-bytes={len(responding)}"
            )
            for probe in responding:
                log.line(
                    f"    {probe['name']}: {probe['response_length']} bytes "
                    f"outcome={probe['outcome']} ap={probe.get('ap_analysis')}"
                )
        except Exception as err:
            document["phase_errors"].append(error_record(f"tcp_8899_{candidate.alias}", err))
            log.line(f"  {candidate.alias}: ERROR {type(err).__name__}: {err}")

    document["summary"] = summarize(document)
    document["metadata"]["timestamp_utc"] = utc_now()
    log.line()
    log.line("Summary:")
    for key, value in document["summary"].items():
        log.line(f"  {key}: {value}")

    try:
        write_json(document, json_path)
    except OSError as err:
        log.line(f"ERROR: could not write JSON: {err}")
        log.close()
        return 1

    log.line()
    log.line("Diagnostic complete · READ-ONLY · identifiers redacted")
    log.line(f"JSON: {json_path}")
    log.line(f"LOG : {log_path}")
    log.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
