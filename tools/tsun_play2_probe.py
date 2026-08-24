#!/usr/bin/env python3
# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later
"""Sunology PLAY2 / TSUN read-only local super-probe v1.3.

Python >=3.10, standard library only.

Goals:
- identify the actual logger through iGEN UDP discovery (48899/49999);
- recognise compact 12-hex MAC identifiers returned by smart_config;
- inspect local HTTP identity pages, including read-only Basic admin/admin GETs;
- probe TCP 8899/48899/49999 without any write command;
- fully decode Solarman V5 response envelopes (0x1510), including sequence,
  logger SN correlation, checksum, timestamps and embedded payload;
- preserve mDNS/_solarhome and passive WebSocket checks for Sunology CONNECT.

No configuration writes, no BLE/Wi-Fi provisioning, no cloud login,
no Modbus write functions, no WebSocket application messages.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import http.client
from ipaddress import IPv4Address, ip_network
import json
import re
import secrets
import socket
import ssl
import struct
import sys
import time
from pathlib import Path
from typing import Any

VER = "1.3.0"
SCHEMA = 5
UDP_PORTS = (48899, 49999)
TCP_PORTS = (8899, 48899, 49999)
SMART = b"smartlinkfind"
LEGACY = (b"WIFIKIT-214028-READ", b"HF-A11ASSISTHREAD", b"devicelinkfind")
MDNS = "224.0.0.251"
SERVICE = "_solarhome._tcp.local."
HUB_PREFIX = "sunology-hb-"
HTTP_PATHS = ("/index_cn.html", "/index.html", "/status.html", "/")
HTTP_AUTH = base64.b64encode(b"admin:admin").decode("ascii")
SN_RE = re.compile(r"(?<!\d)([1-9]\d{7,9})(?!\d)")
IP_RE = re.compile(r"(?<!\d)(?:25[0-5]|2[0-4]\d|1?\d?\d)(?:\.(?:25[0-5]|2[0-4]\d|1?\d?\d)){3}(?!\d)")
MAC_SEP_RE = re.compile(r"(?i)(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}")
MAC_RAW_RE = re.compile(r"(?i)(?<![0-9a-f])([0-9a-f]{12})(?![0-9a-f])")
MAX_EVIDENCE = 4096


class Log:
    def __init__(self, path: Path):
        self.f = path.open("w", encoding="utf-8", newline="\n")

    def w(self, text: str = "") -> None:
        print(text)
        self.f.write(text + "\n")
        self.f.flush()

    def close(self) -> None:
        self.f.close()


class Hosts:
    def __init__(self, host: str):
        self.d: dict[str, dict[str, Any]] = {
            host: {"alias": "host0", "reasons": ["supplied_host"], "strong": True, "confirmed_logger": False}
        }

    def add(self, ip: str | None, why: str, strong: bool = False) -> None:
        if not ip:
            return
        try:
            IPv4Address(ip)
        except ValueError:
            return
        if ip not in self.d and len(self.d) < 8:
            self.d[ip] = {
                "alias": f"candidate{len(self.d)}",
                "reasons": [],
                "strong": False,
                "confirmed_logger": False,
            }
        if ip in self.d:
            if why not in self.d[ip]["reasons"]:
                self.d[ip]["reasons"].append(why)
            self.d[ip]["strong"] = self.d[ip]["strong"] or strong

    def confirm(self, ip: str, why: str) -> None:
        self.add(ip, why, True)
        self.d[ip]["confirmed_logger"] = True

    def alias(self, ip: str | None) -> str | None:
        if not ip:
            return None
        return self.d.get(ip, {}).get("alias", "other-local-host")

    def public(self) -> list[dict[str, Any]]:
        return [
            {
                "alias": v["alias"],
                "reasons": v["reasons"],
                "strong": v["strong"],
                "confirmed_logger": v["confirmed_logger"],
            }
            for v in self.d.values()
        ]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def err(stage: str, e: BaseException) -> dict[str, str]:
    return {"stage": stage, "type": type(e).__name__, "detail": str(e) or type(e).__name__}


def crc16(b: bytes) -> int:
    c = 0xFFFF
    for x in b:
        c ^= x
        for _ in range(8):
            c = (c >> 1) ^ 0xA001 if c & 1 else c >> 1
    return c & 0xFFFF


def normalise_mac(value: str) -> str | None:
    v = re.sub(r"[^0-9A-Fa-f]", "", value)
    if len(v) != 12 or not re.fullmatch(r"[0-9A-Fa-f]{12}", v):
        return None
    v = v.upper()
    return ":".join(v[i : i + 2] for i in range(0, 12, 2))


def redact_bytes(b: bytes, sn: int | None, ips: list[str]) -> bytes:
    out = bytes(b)
    if sn:
        for x in (str(sn).encode(), sn.to_bytes(4, "little"), sn.to_bytes(4, "big")):
            out = out.replace(x, b"*" * len(x))
    for ip in ips:
        out = out.replace(ip.encode(), b"*" * len(ip))
        try:
            out = out.replace(socket.inet_aton(ip), b"****")
        except OSError:
            pass
    text = out.decode("latin1", "ignore")
    for regex in (MAC_SEP_RE, MAC_RAW_RE):
        for m in list(regex.finditer(text)):
            raw = m.group(0).encode("latin1")
            out = out.replace(raw, b"*" * len(raw))
    return out


def evidence(b: bytes, sn: int | None, ips: list[str]) -> dict[str, Any]:
    r = redact_bytes(b, sn, ips)
    cap = r[:MAX_EVIDENCE]
    return {
        "length": len(b),
        "sha256": sha(b),
        "redacted_hex": cap.hex(),
        "redacted_ascii": "".join(chr(x) if 32 <= x < 127 else f"\\x{x:02x}" for x in cap),
        "complete": len(b) <= MAX_EVIDENCE,
    }


def parse_udp(b: bytes) -> dict[str, Any]:
    t = b.decode("utf-8", "replace").strip("\x00\r\n ")
    out: dict[str, Any] = {"text": t, "format": "text", "sn": None, "ip": None, "mac": None}
    try:
        obj = json.loads(t)
    except Exception:
        obj = None
    if isinstance(obj, dict):
        out["format"] = "json"
        for k in ("mid", "sn", "serial", "loggerSn", "monitorSn"):
            try:
                n = int(str(obj.get(k, "")))
            except Exception:
                continue
            if 0 < n <= 0xFFFFFFFF:
                out["sn"] = n
                break
        if isinstance(obj.get("ip"), str) and IP_RE.fullmatch(obj["ip"].strip()):
            out["ip"] = obj["ip"].strip()
        if isinstance(obj.get("mac"), str):
            out["mac"] = normalise_mac(obj["mac"])
        return out

    lo = t.lower()
    if "smart_config" in lo or "smartconfig" in lo:
        out["format"] = "smart_config_text"
    elif "smartlink" in lo:
        out["format"] = "smartlink_text"

    m = SN_RE.search(t)
    if m:
        out["sn"] = int(m.group(1))
    m = IP_RE.search(t)
    if m:
        out["ip"] = m.group(0)
    m = MAC_SEP_RE.search(t) or MAC_RAW_RE.search(t)
    if m:
        out["mac"] = normalise_mac(m.group(0))

    fields = [x.strip() for x in t.split(",")]
    if len(fields) >= 2:
        out["csv_field_count"] = len(fields)
        out["csv_classes"] = []
        for x in fields:
            cls = "text"
            if IP_RE.fullmatch(x):
                cls = "ipv4"
                out["ip"] = out["ip"] or x
            elif normalise_mac(x):
                cls = "mac"
                out["mac"] = out["mac"] or normalise_mac(x)
            elif x.isdigit() and 8 <= len(x) <= 10:
                cls = "serial_like"
                if out["sn"] is None:
                    out["sn"] = int(x)
            out["csv_classes"].append({"length": len(x), "class": cls})
    return out


def smart_fields(t: str, supplied_sn: int | None) -> dict[str, Any] | None:
    lo = t.lower()
    p = lo.find("smart_config")
    prefix = "smart_config"
    if p < 0:
        p = lo.find("smartconfig")
        prefix = "smartconfig"
    if p < 0:
        return None
    tail = t[p + len(prefix) :].strip("\x00\r\n #")
    fs = tail.split("##") if tail else []
    result = []
    for i, x in enumerate(fs):
        mac = normalise_mac(x)
        if IP_RE.fullmatch(x):
            cls = "ipv4"
        elif mac:
            cls = "mac"
        elif x.isdigit() and 8 <= len(x) <= 10:
            cls = "serial_like"
        else:
            cls = "text"
        result.append({"index": i, "length": len(x), "class": cls, "mac_suffix": mac[-5:].replace(":", "") if mac else None, "matches_supplied_sn": bool(supplied_sn and x == str(supplied_sn))})
    return {"prefix": prefix, "separator": "##", "field_count": len(fs), "fields": result}


def udp_variant(host: str, bindp: int, sendp: int, msgs: tuple[bytes, ...], timeout: float) -> dict[str, Any]:
    R: dict[str, Any] = {"bind_port": bindp, "send_port": sendp, "messages": [x.decode("ascii") for x in msgs], "bound": False, "replies": [], "error": None}
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    try:
        try:
            s.bind(("", bindp)); R["bound"] = True
        except OSError as e:
            R["error"] = err("bind", e); return R
        if bindp == 49999 and sendp == 48899:
            try:
                s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, socket.inet_aton("239.0.0.0") + socket.inet_aton("0.0.0.0"))
            except OSError:
                pass
        destinations = (host, str(ip_network(f"{host}/24", strict=False).broadcast_address), "255.255.255.255")
        for d in destinations:
            for m in msgs:
                try: s.sendto(m, (d, sendp))
                except OSError: pass
        end = time.monotonic() + timeout; seen: set[tuple[str, int, str]] = set()
        while (left := end - time.monotonic()) > 0:
            s.settimeout(left)
            try: b, (src, sp) = s.recvfrom(8192)
            except socket.timeout: break
            except OSError as e: R["error"] = err("recv", e); break
            if b in msgs: continue
            key = (src, sp, sha(b))
            if key in seen: continue
            seen.add(key); R["replies"].append({"_src": src, "source_port": sp, "_raw": b, "_p": parse_udp(b)})
    finally:
        s.close()
    return R


def udp_all(host: str, timeout: float) -> list[dict[str, Any]]:
    out = []
    for bp in UDP_PORTS:
        for sp in UDP_PORTS:
            for name, msgs in (("smartlink", (SMART,)), ("legacy", LEGACY)):
                r = udp_variant(host, bp, sp, msgs, timeout); r["name"] = f"udp_{bp}_to_{sp}_{name}"; out.append(r)
    return out


def dns_name(name: str) -> bytes:
    return b"".join(bytes((len(x),)) + x.encode() for x in name.rstrip(".").split(".")) + b"\0"


def read_dns_name(b: bytes, o: int, seen: set[int] | None = None) -> tuple[str, int]:
    seen = set() if seen is None else seen; labels: list[str] = []; nxt = None
    while True:
        n = b[o]
        if n == 0: return ".".join(labels) + ".", nxt if nxt is not None else o + 1
        if n & 0xC0 == 0xC0:
            p = ((n & 0x3F) << 8) | b[o + 1]
            if p in seen: raise ValueError("dns pointer loop")
            seen.add(p); nxt = o + 2 if nxt is None else nxt; o = p; continue
        o += 1; labels.append(b[o:o+n].decode("utf8", "replace")); o += n


def mdns(timeout: float) -> dict[str, Any]:
    q = struct.pack("!HHHHHH", 0, 0, 1, 0, 0, 0) + dns_name(SERVICE) + struct.pack("!HH", 12, 1); packets = []; errors = []
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        try:
            s.bind(("", 5353)); s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, socket.inet_aton(MDNS) + socket.inet_aton("0.0.0.0")); mode = "5353_multicast"
        except OSError as e:
            errors.append(err("mdns_bind", e)); s.close(); s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.bind(("", 0)); mode = "ephemeral"
        s.sendto(q, (MDNS, 5353)); end = time.monotonic() + timeout
        while (left := end - time.monotonic()) > 0:
            s.settimeout(left)
            try: b, (src, sp) = s.recvfrom(9000)
            except socket.timeout: break
            packets.append((b, src, sp))
    finally: s.close()
    srv: dict[str, tuple[int, str]] = {}; A: dict[str, set[str]] = {}; ptr: set[str] = set(); txt: dict[str, list[str]] = {}
    for b, _, _ in packets:
        try:
            _, _, qd, an, ns, ar = struct.unpack_from("!HHHHHH", b, 0); o = 12
            for _ in range(qd): _, o = read_dns_name(b, o); o += 4
            for _ in range(an + ns + ar):
                name, o = read_dns_name(b, o); typ, _, _, ln = struct.unpack_from("!HHIH", b, o); o += 10; rs, re_ = o, o + ln
                if typ == 12: target, _ = read_dns_name(b, rs); ptr.add(target)
                elif typ == 33 and ln >= 6: _, _, port = struct.unpack_from("!HHH", b, rs); target, _ = read_dns_name(b, rs + 6); srv[name] = (port, target)
                elif typ == 1 and ln == 4: A.setdefault(name, set()).add(socket.inet_ntoa(b[rs:re_]))
                elif typ == 16:
                    cur, vals = rs, []
                    while cur < re_: n = b[cur]; cur += 1; vals.append(b[cur:cur+n].decode("utf8", "replace")); cur += n
                    txt[name] = vals
                o = re_
        except Exception: continue
    services = []
    for ins in sorted(ptr | set(srv)):
        port, target = srv.get(ins, (None, None)); services.append({"instance": ins, "port": port, "addresses": sorted(A.get(target, set())) if target else [], "txt": txt.get(ins, []), "hub_name": ins.lower().startswith(HUB_PREFIX)})
    return {"mode": mode, "packet_count": len(packets), "services": services[:8], "errors": errors}


def websocket(host: str, port: int, timeout: float, listen: float, sn: int | None, ips: list[str]) -> dict[str, Any]:
    R: dict[str, Any] = {"port": port, "connected": False, "events": [], "errors": []}
    for origin in (None, "http://localhost", "capacitor://localhost"):
        key = base64.b64encode(secrets.token_bytes(16)).decode(); h = ["GET /ws HTTP/1.1", f"Host: {host}:{port}", "Upgrade: websocket", "Connection: Upgrade", f"Sec-WebSocket-Key: {key}", "Sec-WebSocket-Version: 13"]
        if origin: h.append(f"Origin: {origin}")
        try:
            with socket.create_connection((host, port), timeout=timeout) as s:
                s.settimeout(timeout); s.sendall(("\r\n".join(h) + "\r\n\r\n").encode()); r = b""
                while b"\r\n\r\n" not in r and len(r) < 16384: r += s.recv(2048)
                status = r.decode("latin1", "replace").split("\r\n", 1)[0]
                if " 101 " not in f" {status} ": R["errors"].append({"origin": origin, "status": status}); continue
                R.update({"connected": True, "origin": origin, "status": status}); end = time.monotonic() + listen
                def rx(n: int) -> bytes:
                    z = b""
                    while len(z) < n:
                        x = s.recv(n - len(z))
                        if not x: raise EOFError
                        z += x
                    return z
                while len(R["events"]) < 24 and (left := end - time.monotonic()) > 0:
                    s.settimeout(min(1.5, left))
                    try: a = rx(2)
                    except socket.timeout: continue
                    except EOFError: break
                    op, n, masked = a[0] & 15, a[1] & 127, a[1] & 128
                    if n == 126: n = int.from_bytes(rx(2), "big")
                    elif n == 127: n = int.from_bytes(rx(8), "big")
                    if n > 16384: break
                    mask = rx(4) if masked else b""; p = rx(n)
                    if masked: p = bytes(x ^ mask[i % 4] for i, x in enumerate(p))
                    ev: dict[str, Any] = {"opcode": op, "payload": evidence(p, sn, ips)}
                    if op == 1:
                        try: obj = json.loads(p.decode("utf8", "replace"))
                        except Exception: obj = None
                        if isinstance(obj, dict):
                            data = obj.get("data") if isinstance(obj.get("data"), dict) else obj; ev["event"] = obj.get("event") or obj.get("type"); ev["signals"] = {k: data[k] for k in ("pvP", "power", "production", "soc", "batteryPower", "gridPower", "state", "deviceState") if k in data and isinstance(data[k], (int, float, str, bool, type(None)))}
                    R["events"].append(ev)
                    if op == 8: break
                return R
        except Exception as e: R["errors"].append(err("websocket", e))
    return R


def isopen(host: str, port: int, timeout: float) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout): return True
    except OSError: return False


def http_get(host: str, port: int, tls: bool, path: str, timeout: float, auth: bool) -> dict[str, Any]:
    headers = {"Connection": "close", "User-Agent": "TSUN-Local-PLAY2-Probe"}
    if auth: headers["Authorization"] = f"Basic {HTTP_AUTH}"
    if tls:
        ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE; c: http.client.HTTPConnection = http.client.HTTPSConnection(host, port, timeout=timeout, context=ctx)
    else: c = http.client.HTTPConnection(host, port, timeout=timeout)
    try:
        c.request("GET", path, headers=headers); r = c.getresponse(); body = r.read(524289)
        return {"status": r.status, "server": r.getheader("Server"), "content_type": r.getheader("Content-Type"), "www_authenticate": r.getheader("WWW-Authenticate"), "body": body}
    finally: c.close()


def http_id(host: str, timeout: float, sn: int | None, ips: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {"transports": []}
    for port, tls in ((80, False), (443, True)):
        tr: dict[str, Any] = {"scheme": "https" if tls else "http", "open": isopen(host, port, min(timeout, 1.2)), "pages": []}
        if tr["open"]:
            for path in HTTP_PATHS:
                page: dict[str, Any] = {"path": path}
                try:
                    a = http_get(host, port, tls, path, timeout, False); page.update({"status": a["status"], "server": a["server"], "content_type": a["content_type"], "www_authenticate": a["www_authenticate"], "body": evidence(a["body"], sn, ips) if len(a["body"]) <= 524288 else None})
                    if a["status"] == 401:
                        try:
                            b = http_get(host, port, tls, path, timeout, True); page["basic_admin_admin"] = {"attempted_read_only": True, "status": b["status"], "server": b["server"], "content_type": b["content_type"], "body": evidence(b["body"], sn, ips) if len(b["body"]) <= 524288 else None}
                        except Exception as e: page["basic_admin_admin"] = {"attempted_read_only": True, "error": err("http_basic", e)}
                except Exception as e: page["error"] = err("http", e)
                tr["pages"].append(page)
        result["transports"].append(tr)
    return result


def mbread(addr: int, count: int = 1, function: int = 3) -> bytes:
    b = b"\x01" + bytes((function,)) + addr.to_bytes(2, "big") + count.to_bytes(2, "big"); return b + crc16(b).to_bytes(2, "little")


def mbtcp(addr: int, count: int = 1, tx: int = 1) -> bytes:
    p = b"\x01\x03" + addr.to_bytes(2, "big") + count.to_bytes(2, "big"); return struct.pack("!HHH", tx, 0, len(p)) + p


def r1511(tag: int, fn: int, start: int, end: int) -> bytes:
    n = end - start + 1; b = bytes((tag, fn, 0)) + start.to_bytes(2, "big") + b"\x00\x02" + n.to_bytes(2, "big"); return b + crc16(b).to_bytes(2, "big")


def ap(sn: int, payload: bytes, sensor_list: int = 0, seq: int = 0) -> bytes:
    data = b"\x02" + sensor_list.to_bytes(2, "little") + bytes(12) + payload; x = len(data).to_bytes(2, "little") + b"\x10\x45" + seq.to_bytes(2, "little") + sn.to_bytes(4, "little") + data; return b"\xA5" + x + bytes((sum(x) & 0xFF, 0x15))


def probe_matrix(sn: int | None) -> list[tuple[str, bytes, dict[str, Any]]]:
    q: list[tuple[str, bytes, dict[str, Any]]] = []
    for S in ([0, sn] if sn else [0]):
        who = "sn0" if S == 0 else "snsupplied"; tests = (("native_a1_01_sl0000", r1511(0xA1, 0x01, 0x0BB8, 0x0BD0), 0x0000), ("native_a1_01_sl1511", r1511(0xA1, 0x01, 0x0BB8, 0x0BD0), 0x1511), ("native_a1_01_sl02b0", r1511(0xA1, 0x01, 0x0BB8, 0x0BD0), 0x02B0), ("modbus03_3000_sl02b0", mbread(0x3000, 1, 3), 0x02B0), ("modbus04_3000_sl02b0", mbread(0x3000, 1, 4), 0x02B0), ("modbus03_1100_sl1097", mbread(0x1100, 1, 3), 0x1097), ("modbus04_1100_sl1097", mbread(0x1100, 1, 4), 0x1097), ("modbus03_0000_sl3026", mbread(0x0000, 1, 3), 0x3026))
        for idx, (name, payload, sl) in enumerate(tests):
            seq = 0x40 + idx; q.append((f"ap_{name}_{who}", ap(int(S), payload, sl, seq), {"kind": "AP", "sensor_list": f"0x{sl:04X}", "sn_zero": S == 0, "request_seq_low": seq & 0xFF}))
    q += [("direct_rtu_fc03_3000", mbread(0x3000, 1, 3), {"kind": "RTU-FC03"}), ("direct_rtu_fc04_3000", mbread(0x3000, 1, 4), {"kind": "RTU-FC04"}), ("direct_modbus_tcp_3000", mbtcp(0x3000), {"kind": "Modbus-TCP-FC03"}), ("direct_native_1511", r1511(0xA1, 0x01, 0x0BB8, 0x0BD0), {"kind": "1511-native"})]
    return q


def control_name(control: int) -> str:
    return {0x4110: "HANDSHAKE", 0x4210: "DATA", 0x4310: "INFO", 0x4510: "REQUEST", 0x1510: "RESPONSE", 0x4710: "HEARTBEAT", 0x4810: "REPORT"}.get(control, "UNKNOWN")


def decode_v5(frame: bytes, supplied_sn: int | None, request_meta: dict[str, Any] | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {"looks_like_v5": False, "valid_start": False, "valid_end": False, "length_valid": False, "checksum_valid": False}
    if len(frame) < 13: out["reason"] = "too_short"; return out
    out["valid_start"] = frame[0] == 0xA5; out["valid_end"] = frame[-1] == 0x15
    if not out["valid_start"]: out["reason"] = "missing_A5"; return out
    declared = int.from_bytes(frame[1:3], "little"); expected_total = 11 + declared + 2; out["declared_payload_length"] = declared; out["actual_total_length"] = len(frame); out["expected_total_length"] = expected_total; out["length_valid"] = len(frame) == expected_total
    control = int.from_bytes(frame[3:5], "little"); seq = int.from_bytes(frame[5:7], "little"); logger_sn = int.from_bytes(frame[7:11], "little")
    out.update({"looks_like_v5": True, "control": f"0x{control:04X}", "control_name": control_name(control), "sequence": seq, "sequence_low": seq & 0xFF, "response_counter_high": (seq >> 8) & 0xFF, "logger_sn_present": logger_sn != 0, "logger_sn_matches_supplied": bool(supplied_sn and logger_sn == supplied_sn)})
    if request_meta and isinstance(request_meta.get("request_seq_low"), int): out["request_sequence_low"] = request_meta["request_seq_low"]; out["sequence_low_echo_matches"] = (seq & 0xFF) == request_meta["request_seq_low"]
    out["checksum_valid"] = (sum(frame[1:-2]) & 0xFF) == frame[-2]; out["checksum_byte"] = frame[-2]
    if not out["length_valid"] or declared < 1 or len(frame) < 11 + declared + 2: return out
    p = frame[11:11+declared]; out["payload_length"] = len(p)
    if control == 0x1510 and len(p) >= 14:
        frame_type = p[0]; status = p[1]; total_working = int.from_bytes(p[2:6], "little"); power_on = int.from_bytes(p[6:10], "little"); offset = int.from_bytes(p[10:14], "little"); acq = total_working + offset; embedded = p[14:]
        out["response"] = {"frame_type": frame_type, "frame_type_name": {0: "cloud_or_keepalive", 1: "logger", 2: "inverter"}.get(frame_type, "unknown"), "status": status, "total_working_time_s": total_working, "power_on_time_s": power_on, "device_total_operation_time_s": total_working - power_on, "offset_time_s": offset, "acquisition_timestamp_unix": acq, "acquisition_timestamp_utc": datetime.fromtimestamp(acq, timezone.utc).isoformat() if 946684800 <= acq <= 4102444800 else None, "embedded_length": len(embedded), "embedded_hex": embedded.hex()}
        if len(embedded) == 2:
            out["response"].update({"embedded_class": "short_response_marker", "short_marker_le": int.from_bytes(embedded, "little"), "short_marker_bytes": list(embedded), "note": "Too short for a valid Modbus RTU response; preserve as protocol marker/error evidence."})
        elif len(embedded) >= 5:
            out["response"]["embedded_class"] = "candidate_protocol_payload"; out["response"]["rtu_crc_candidate_valid"] = crc16(embedded[:-2]) == int.from_bytes(embedded[-2:], "little")
    return out


def tcp_one(host: str, port: int, name: str, req: bytes, meta: dict[str, Any], timeout: float, sn: int | None, ips: list[str]) -> dict[str, Any]:
    R: dict[str, Any] = {"name": name, "meta": meta, "connected": False, "sent": False, "response_length": 0}; start = time.monotonic()
    try:
        with socket.create_connection((host, port), timeout=timeout) as s:
            R["connected"] = True; s.settimeout(timeout); s.sendall(req); R["sent"] = True; z = b""
            try:
                while len(z) < 65536:
                    x = s.recv(min(4096, 65536-len(z)))
                    if not x: break
                    z += x
                    if z: s.settimeout(0.35)
            except socket.timeout: pass
            R["response_length"] = len(z); R["outcome"] = "bytes" if z else "no_bytes"
            if z: R["response"] = evidence(z, sn, ips); R["v5"] = decode_v5(z, sn, meta)
    except Exception as e: R["outcome"] = "error"; R["error"] = err("tcp", e)
    R["elapsed_ms"] = round((time.monotonic()-start)*1000, 1); return R


def tcp_port(host: str, port: int, timeout: float, sn: int | None, ips: list[str], full: bool) -> dict[str, Any]:
    R: dict[str, Any] = {"port": port, "open": isopen(host, port, min(timeout, 1.2)), "passive": None, "probes": []}
    if not R["open"]: return R
    try:
        with socket.create_connection((host, port), timeout=timeout) as s:
            s.settimeout(min(timeout, 1.0))
            try: b = s.recv(1024)
            except socket.timeout: b = b""
            R["passive"] = {"received": bool(b), "payload": evidence(b, sn, ips) if b else None, "v5": decode_v5(b, sn) if b else None}
    except Exception as e: R["passive"] = {"error": err("passive", e)}
    probes = probe_matrix(sn)
    if not full: probes = probes[:4]
    for name, req, meta in probes: R["probes"].append(tcp_one(host, port, name, req, meta, timeout, sn, ips)); time.sleep(0.08)
    return R


def main() -> int:
    if sys.version_info < (3, 10): print("Python 3.10+ required", file=sys.stderr); return 2
    p = argparse.ArgumentParser(description="Sunology PLAY2 read-only super-probe v1.3"); p.add_argument("--host", required=True); p.add_argument("--monitor-sn", "--serial", dest="sn", type=int); p.add_argument("--udp-timeout", type=float, default=3.0); p.add_argument("--mdns-timeout", type=float, default=6.0); p.add_argument("--ws-listen", type=float, default=6.0); p.add_argument("--timeout", type=float, default=2.2); p.add_argument("--http-timeout", type=float, default=2.0); p.add_argument("--output", type=Path); a = p.parse_args()
    try: IPv4Address(a.host)
    except ValueError: print("Invalid --host", file=sys.stderr); return 2
    if a.sn is not None and not (0 < a.sn <= 0xFFFFFFFF): print("Invalid --monitor-sn", file=sys.stderr); return 2
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"); jp = a.output or Path(f"tsun_play2_superprobe_{stamp}.json"); lp = jp.with_suffix(".log"); L = Log(lp); H = Hosts(a.host)
    D: dict[str, Any] = {"format": "tsun-local-play2-superprobe", "schema_version": SCHEMA, "metadata": {"tool_version": VER, "timestamp_utc": now_iso(), "read_only": True, "writes": 0, "cloud_requests": 0, "apk_evidence": {"smartlink": "UDP 48899/49999", "smart_config": "prefix + ## fields", "mdns": "_solarhome._tcp.local", "websocket": "/ws", "mock_only": "ws://127.0.0.1:20199"}, "v5_reference_model": {"request_control": "0x4510", "response_control": "0x1510", "response_payload_header_bytes": 14, "fields": ["frame_type", "status", "total_working_time", "power_on_time", "offset_time", "embedded_payload"]}}, "udp": [], "mdns": {}, "websocket": [], "http": [], "tcp": [], "candidates": [], "analysis": {}, "errors": []}
    L.w(f"TSUN Local PLAY2 Super-Probe v{VER} - READ-ONLY"); L.w("UDP identity + MAC parsing + HTTP Basic read-only + V5 decode + mDNS/WS + TCP port matrix")
    try:
        U = udp_all(a.host, a.udp_timeout)
        for r in U:
            for x in r["replies"]:
                pp = x["_p"]; match = bool(a.sn and pp.get("sn") == a.sn); H.add(x["_src"], f"udp:{r['name']}", match)
                if pp.get("ip"): H.add(pp["ip"], f"udp-declared:{r['name']}", match)
        for r in U:
            pub = {k: v for k, v in r.items() if k != "replies"}; pub["replies"] = []
            for x in r["replies"]:
                pp = x["_p"]; mac = pp.get("mac"); pub["replies"].append({"source_alias": H.alias(x["_src"]), "source_port": x["source_port"], "format": pp["format"], "sn_present": pp.get("sn") is not None, "sn_matches": bool(a.sn and pp.get("sn") == a.sn), "declared_ip_alias": H.alias(pp["ip"]) if pp.get("ip") else None, "mac_present": bool(mac), "mac_suffix": mac[-5:].replace(":", "") if mac else None, "csv_field_count": pp.get("csv_field_count"), "csv_classes": pp.get("csv_classes"), "smart_config": smart_fields(pp["text"], a.sn), "payload": evidence(x["_raw"], a.sn, list(H.d))})
            D["udp"].append(pub); L.w(f"UDP {r['name']}: {len(pub['replies'])} replies")
    except Exception as e: D["errors"].append(err("udp", e))
    try:
        M = mdns(a.mdns_timeout)
        for s in M["services"]:
            for ip in s["addresses"]: H.add(ip, "mdns")
        D["mdns"] = {"mode": M["mode"], "packet_count": M["packet_count"], "errors": M["errors"], "services": [{"instance": "<sunology-hb>" if s["hub_name"] else "<service>", "port": s["port"], "address_aliases": [H.alias(x) for x in s["addresses"]], "hub_name": s["hub_name"], "txt": s["txt"]} for s in M["services"]]}; L.w(f"mDNS services: {len(M['services'])}")
        for s in M["services"]:
            if isinstance(s["port"], int):
                for ip in s["addresses"][:2]:
                    w = websocket(ip, s["port"], a.timeout, a.ws_listen, a.sn, list(H.d)); w["host_alias"] = H.alias(ip); D["websocket"].append(w); L.w(f"WS {H.alias(ip)}:{s['port']}: connected={w['connected']} events={len(w['events'])}")
    except Exception as e: D["errors"].append(err("mdns/ws", e))
    for ip, v in list(H.d.items()):
        try:
            h = http_id(ip, a.http_timeout, a.sn, list(H.d)); h["host_alias"] = v["alias"]; D["http"].append(h); auth_ok = any(p.get("basic_admin_admin", {}).get("status") == 200 for tr in h["transports"] for p in tr["pages"]); L.w(f"HTTP {v['alias']}: basic-admin-read={'yes' if auth_ok else 'no'}")
        except Exception as e: D["errors"].append(err("http", e))
    for ip, v in list(H.d.items()):
        for port in TCP_PORTS:
            try:
                full = port == 8899 and bool(v["strong"]); r = tcp_port(ip, port, a.timeout, a.sn, list(H.d), full); r["host_alias"] = v["alias"]; D["tcp"].append(r); good = [q for q in r["probes"] if q.get("v5", {}).get("control") == "0x1510" and q.get("v5", {}).get("checksum_valid") and q.get("v5", {}).get("logger_sn_matches_supplied")]
                if good: H.confirm(ip, f"valid_v5_response:{port}")
                L.w(f"TCP {v['alias']}:{port}: open={r['open']} v5-valid={len(good)}")
            except Exception as e: D["errors"].append(err(f"tcp:{port}", e))
    D["candidates"] = H.public(); confirmed = [v["alias"] for v in H.d.values() if v["confirmed_logger"]]; markers: dict[str, int] = {}; v5_valid = 0; timestamp_samples = []
    for t in D["tcp"]:
        for q in t.get("probes", []):
            v5 = q.get("v5") or {}
            if v5.get("checksum_valid") and v5.get("control") == "0x1510": v5_valid += 1
            rsp = v5.get("response") or {}
            if rsp.get("embedded_class") == "short_response_marker": key = rsp.get("embedded_hex", ""); markers[key] = markers.get(key, 0) + 1
            if rsp.get("acquisition_timestamp_utc"): timestamp_samples.append(rsp["acquisition_timestamp_utc"])
    D["analysis"] = {"confirmed_logger_aliases": confirmed, "valid_v5_response_count": v5_valid, "short_response_markers": markers, "v5_timestamp_first": timestamp_samples[0] if timestamp_samples else None, "v5_timestamp_last": timestamp_samples[-1] if timestamp_samples else None, "interpretation": {"short_markers": "Two-byte embedded payloads are valid V5 envelopes but are too short to be normal Modbus RTU data; treat 05 00 / 06 00 as response/error markers until mapped.", "next_success_condition": "A response with embedded_length > 2 and a protocol payload (native or Modbus-like) is the target for telemetry decoding."}}
    D["summary"] = {"udp_variants": len(D["udp"]), "udp_replies": sum(len(x["replies"]) for x in D["udp"]), "candidates": len(D["candidates"]), "confirmed_loggers": len(confirmed), "mdns_services": len(D.get("mdns", {}).get("services", [])), "ws_connections": sum(1 for x in D["websocket"] if x["connected"]), "valid_v5_responses": v5_valid, "tcp_open": {str(port): sum(1 for x in D["tcp"] if x["port"] == port and x["open"]) for port in TCP_PORTS}}
    D["metadata"]["timestamp_utc"] = now_iso(); jp.write_text(json.dumps(D, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"); L.w(f"Confirmed logger(s): {confirmed or 'none'}"); L.w(f"Valid V5 responses: {v5_valid}; short markers: {markers}"); L.w(f"JSON: {jp}"); L.w(f"LOG : {lp}"); L.close(); return 0


if __name__ == "__main__":
    raise SystemExit(main())
