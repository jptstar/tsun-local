#!/usr/bin/env python3
"""Passive TSUN logger OTA traffic probe.

This research helper observes traffic that already exists between one logger and
its network. It never opens a socket to the logger, never sends a packet, never
changes DNS/server settings, and never stores packet payloads or a PCAP file.

Capture is delegated to tcpdump. The script consumes the PCAP stream in memory
and keeps only privacy-reduced metadata useful for identifying OTA paths:
DNS query names, public remote endpoints, HTTP host/path (query strings removed)
and TLS SNI names.
"""

from __future__ import annotations

import argparse
import datetime as dt
import ipaddress
import json
import os
import shutil
import signal
import struct
import subprocess
import sys
import threading
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import BinaryIO

TOOL_VERSION = "0.1.0"
DLT_EN10MB = 1
DLT_LINUX_SLL = 113
DLT_LINUX_SLL2 = 276
PRIVATE_DOMAIN_SUFFIXES = (".local", ".lan", ".home", ".internal", ".localdomain")
HTTP_METHODS = (b"GET ", b"POST ", b"HEAD ", b"PUT ", b"OPTIONS ", b"PATCH ", b"DELETE ")


def _read_exact(stream: BinaryIO, size: int) -> bytes:
    chunks: list[bytes] = []
    remaining = size
    while remaining:
        chunk = stream.read(remaining)
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _scope(ip: str) -> str:
    obj = ipaddress.ip_address(ip)
    if obj.is_loopback:
        return "loopback"
    if obj.is_link_local:
        return "link_local"
    if obj.is_private:
        return "private"
    if obj.is_multicast:
        return "multicast"
    return "public"


def _safe_domain(name: str) -> str | None:
    value = name.strip().lower().rstrip(".")
    if not value or len(value) > 253:
        return None
    if value.endswith(PRIVATE_DOMAIN_SUFFIXES) or ".local." in value:
        return "<private-domain>"
    # Keep syntactically plausible DNS/SNI names only.
    labels = value.split(".")
    if any(not label or len(label) > 63 for label in labels):
        return None
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789-_")
    if any(any(ch not in allowed for ch in label) for label in labels):
        return None
    return value


def _parse_dns_query(payload: bytes) -> str | None:
    if len(payload) < 12:
        return None
    flags = struct.unpack_from("!H", payload, 2)[0]
    qdcount = struct.unpack_from("!H", payload, 4)[0]
    if flags & 0x8000 or qdcount < 1:
        return None
    pos = 12
    labels: list[str] = []
    for _ in range(128):
        if pos >= len(payload):
            return None
        length = payload[pos]
        pos += 1
        if length == 0:
            break
        if length & 0xC0 or length > 63 or pos + length > len(payload):
            return None
        raw = payload[pos : pos + length]
        pos += length
        try:
            labels.append(raw.decode("ascii"))
        except UnicodeDecodeError:
            return None
    else:
        return None
    return _safe_domain(".".join(labels))


def _parse_http(payload: bytes) -> tuple[str | None, str | None, str | None]:
    if not payload.startswith(HTTP_METHODS):
        return None, None, None
    head = payload[:8192]
    try:
        text = head.decode("iso-8859-1", errors="replace")
    except Exception:
        return None, None, None
    lines = text.split("\r\n")
    parts = lines[0].split(" ", 2)
    if len(parts) < 2:
        return None, None, None
    method = parts[0].upper()
    raw_path = parts[1]
    path = raw_path.split("?", 1)[0].split("#", 1)[0]
    if not path.startswith("/"):
        path = "/"
    if len(path) > 512:
        path = path[:512]
    host = None
    for line in lines[1:]:
        if line.lower().startswith("host:"):
            host = line.split(":", 1)[1].strip().split(":", 1)[0]
            host = _safe_domain(host)
            break
    return method, host, path


def _parse_tls_sni(payload: bytes) -> str | None:
    """Return SNI from a TLS ClientHello contained in one TCP payload."""
    try:
        if len(payload) < 9 or payload[0] != 22:  # handshake record
            return None
        record_len = struct.unpack_from("!H", payload, 3)[0]
        record_end = min(len(payload), 5 + record_len)
        if record_end < 9 or payload[5] != 1:  # ClientHello
            return None
        hs_len = int.from_bytes(payload[6:9], "big")
        end = min(record_end, 9 + hs_len)
        pos = 9
        if pos + 34 > end:
            return None
        pos += 2 + 32  # client version + random
        if pos >= end:
            return None
        sid_len = payload[pos]
        pos += 1 + sid_len
        if pos + 2 > end:
            return None
        cs_len = struct.unpack_from("!H", payload, pos)[0]
        pos += 2 + cs_len
        if pos >= end:
            return None
        comp_len = payload[pos]
        pos += 1 + comp_len
        if pos + 2 > end:
            return None
        ext_total = struct.unpack_from("!H", payload, pos)[0]
        pos += 2
        ext_end = min(end, pos + ext_total)
        while pos + 4 <= ext_end:
            ext_type, ext_len = struct.unpack_from("!HH", payload, pos)
            pos += 4
            data_end = pos + ext_len
            if data_end > ext_end:
                return None
            if ext_type == 0 and ext_len >= 5:  # server_name
                if pos + 2 > data_end:
                    return None
                list_len = struct.unpack_from("!H", payload, pos)[0]
                p = pos + 2
                list_end = min(data_end, p + list_len)
                while p + 3 <= list_end:
                    name_type = payload[p]
                    name_len = struct.unpack_from("!H", payload, p + 1)[0]
                    p += 3
                    if p + name_len > list_end:
                        return None
                    if name_type == 0:
                        try:
                            return _safe_domain(payload[p : p + name_len].decode("ascii"))
                        except UnicodeDecodeError:
                            return None
                    p += name_len
            pos = data_end
    except (IndexError, struct.error, ValueError):
        return None
    return None


class TrafficAnalyzer:
    def __init__(self, logger_ip: str) -> None:
        self.logger_ip = str(ipaddress.ip_address(logger_ip))
        self.packet_count = 0
        self.byte_count = 0
        self.dns_queries: Counter[str] = Counter()
        self.tls_sni: Counter[str] = Counter()
        self.http_requests: Counter[tuple[str, str, str]] = Counter()
        self.endpoints: Counter[tuple[str, int, str, str]] = Counter()
        self.port_counts: Counter[int] = Counter()
        self.protocol_counts: Counter[str] = Counter()

    def process_ipv4(self, packet: bytes) -> None:
        if len(packet) < 20 or packet[0] >> 4 != 4:
            return
        ihl = (packet[0] & 0x0F) * 4
        if ihl < 20 or len(packet) < ihl:
            return
        total_len = struct.unpack_from("!H", packet, 2)[0]
        total_len = min(total_len or len(packet), len(packet))
        proto = packet[9]
        src = ".".join(str(b) for b in packet[12:16])
        dst = ".".join(str(b) for b in packet[16:20])
        if src != self.logger_ip and dst != self.logger_ip:
            return
        outbound = src == self.logger_ip
        remote = dst if outbound else src
        direction = "outbound" if outbound else "inbound"
        scope = _scope(remote)
        self.packet_count += 1
        self.byte_count += total_len

        if proto == 17 and total_len >= ihl + 8:
            self.protocol_counts["udp"] += 1
            src_port, dst_port, udp_len = struct.unpack_from("!HHH", packet, ihl)
            remote_port = dst_port if outbound else src_port
            self.port_counts[remote_port] += 1
            self.endpoints[(scope, remote_port, "udp", direction)] += 1
            payload_end = min(total_len, ihl + max(8, udp_len))
            payload = packet[ihl + 8 : payload_end]
            if outbound and dst_port == 53:
                qname = _parse_dns_query(payload)
                if qname:
                    self.dns_queries[qname] += 1
            return

        if proto == 6 and total_len >= ihl + 20:
            self.protocol_counts["tcp"] += 1
            src_port, dst_port = struct.unpack_from("!HH", packet, ihl)
            data_offset = ((packet[ihl + 12] >> 4) & 0x0F) * 4
            if data_offset < 20 or ihl + data_offset > total_len:
                return
            remote_port = dst_port if outbound else src_port
            self.port_counts[remote_port] += 1
            self.endpoints[(scope, remote_port, "tcp", direction)] += 1
            if not outbound:
                return
            payload = packet[ihl + data_offset : total_len]
            if not payload:
                return
            method, host, path = _parse_http(payload)
            if method and path:
                self.http_requests[(method, host or "<no-host>", path)] += 1
            sni = _parse_tls_sni(payload)
            if sni:
                self.tls_sni[sni] += 1

    def report(self, duration_s: float, interface: str | None) -> dict:
        endpoints = []
        for (scope, port, proto, direction), count in sorted(
            self.endpoints.items(), key=lambda item: (-item[1], item[0])
        ):
            endpoints.append(
                {
                    "scope": scope,
                    "remote_port": port,
                    "transport": proto,
                    "direction": direction,
                    "packet_count": count,
                }
            )
        http = [
            {"method": method, "host": host, "path": path, "count": count}
            for (method, host, path), count in sorted(
                self.http_requests.items(), key=lambda item: (-item[1], item[0])
            )
        ]
        return {
            "format": "tsun-local-passive-ota-probe",
            "tool_version": TOOL_VERSION,
            "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "read_only": True,
            "passive_capture": True,
            "traffic_injected": False,
            "configuration_write_performed": False,
            "raw_packets_stored": False,
            "packet_payload_stored": False,
            "logger_ip_stored": False,
            "capture": {
                "duration_seconds": round(duration_s, 3),
                "interface": interface or "tcpdump-default",
                "filter": "host <LOGGER_IP> and (udp port 53 or (tcp and not port 8899))",
                "packet_count": self.packet_count,
                "captured_ipv4_bytes": self.byte_count,
            },
            "observations": {
                "dns_queries": [
                    {"name": name, "count": count}
                    for name, count in self.dns_queries.most_common()
                ],
                "tls_sni": [
                    {"name": name, "count": count}
                    for name, count in self.tls_sni.most_common()
                ],
                "http_requests": http,
                "remote_endpoints": endpoints,
                "remote_ports": [
                    {"port": port, "packet_count": count}
                    for port, count in self.port_counts.most_common()
                ],
                "protocols": dict(self.protocol_counts),
            },
            "limitations": [
                "TLS payload is not decrypted; only ClientHello SNI can be observed.",
                "SNI/HTTP extraction requires the relevant header to fit in one captured TCP segment.",
                "Only IPv4 traffic is decoded in this first research version.",
                "No OTA is triggered by this tool; the user must initiate any vendor-side update check separately.",
            ],
        }


def _ipv4_from_link(packet: bytes, linktype: int) -> bytes | None:
    if linktype == DLT_EN10MB:
        if len(packet) < 14:
            return None
        ethertype = struct.unpack_from("!H", packet, 12)[0]
        pos = 14
        while ethertype in (0x8100, 0x88A8) and len(packet) >= pos + 4:
            ethertype = struct.unpack_from("!H", packet, pos + 2)[0]
            pos += 4
        return packet[pos:] if ethertype == 0x0800 else None
    if linktype == DLT_LINUX_SLL:
        if len(packet) < 16:
            return None
        return packet[16:] if struct.unpack_from("!H", packet, 14)[0] == 0x0800 else None
    if linktype == DLT_LINUX_SLL2:
        if len(packet) < 20:
            return None
        return packet[20:] if struct.unpack_from("!H", packet, 0)[0] == 0x0800 else None
    return None


def consume_pcap(stream: BinaryIO, analyzer: TrafficAnalyzer) -> int:
    header = _read_exact(stream, 24)
    if len(header) != 24:
        raise ValueError("tcpdump did not provide a complete PCAP header")
    magic = header[:4]
    if magic in (b"\xd4\xc3\xb2\xa1", b"\x4d\x3c\xb2\xa1"):
        endian = "<"
    elif magic in (b"\xa1\xb2\xc3\xd4", b"\xa1\xb2\x3c\x4d"):
        endian = ">"
    else:
        raise ValueError("unsupported capture format (expected classic PCAP)")
    linktype = struct.unpack_from(endian + "I", header, 20)[0]
    if linktype not in (DLT_EN10MB, DLT_LINUX_SLL, DLT_LINUX_SLL2):
        raise ValueError(f"unsupported tcpdump link type: {linktype}")

    packets = 0
    while True:
        ph = _read_exact(stream, 16)
        if not ph:
            break
        if len(ph) != 16:
            raise ValueError("truncated PCAP packet header")
        _, _, incl_len, _ = struct.unpack(endian + "IIII", ph)
        if incl_len > 4 * 1024 * 1024:
            raise ValueError("unreasonable PCAP packet size")
        raw = _read_exact(stream, incl_len)
        if len(raw) != incl_len:
            raise ValueError("truncated PCAP packet")
        ipv4 = _ipv4_from_link(raw, linktype)
        if ipv4 is not None:
            analyzer.process_ipv4(ipv4)
        packets += 1
    return packets


def build_tcpdump_command(
    tcpdump: str, host: str, interface: str | None
) -> list[str]:
    ipaddress.ip_address(host)
    cmd = [tcpdump, "-U", "-n", "-s", "1024"]
    if interface:
        cmd += ["-i", interface]
    cmd += [
        "-w",
        "-",
        "host",
        host,
        "and",
        "(",
        "udp",
        "port",
        "53",
        "or",
        "(",
        "tcp",
        "and",
        "not",
        "port",
        "8899",
        ")",
        ")",
    ]
    return cmd


def _default_output() -> Path:
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return Path(f"tsun_ota_probe_{stamp}.json")


def run_capture(args: argparse.Namespace) -> int:
    tcpdump = args.tcpdump or shutil.which("tcpdump")
    if not tcpdump:
        print(
            "tcpdump was not found. Install/use tcpdump (or Npcap's tcpdump-compatible binary) "
            "and retry with --tcpdump PATH.",
            file=sys.stderr,
        )
        return 2

    analyzer = TrafficAnalyzer(args.host)
    cmd = build_tcpdump_command(tcpdump, args.host, args.interface)
    started = time.monotonic()
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.DEVNULL,
    )
    assert proc.stdout is not None
    error: list[BaseException] = []

    def reader() -> None:
        try:
            consume_pcap(proc.stdout, analyzer)
        except BaseException as exc:  # surfaced after capture shutdown
            error.append(exc)

    thread = threading.Thread(target=reader, name="tsun-ota-pcap-reader", daemon=True)
    thread.start()
    interrupted = False
    try:
        deadline = started + args.duration
        while proc.poll() is None and time.monotonic() < deadline:
            time.sleep(0.2)
    except KeyboardInterrupt:
        interrupted = True
    finally:
        if proc.poll() is None:
            try:
                proc.send_signal(signal.SIGINT)
            except (OSError, ValueError):
                proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=2)
        thread.join(timeout=5)

    stderr = b""
    if proc.stderr is not None:
        stderr = proc.stderr.read()
    if error:
        print(f"Capture parser error: {error[0]}", file=sys.stderr)
        return 3
    if proc.returncode not in (0, 130, -signal.SIGINT):
        message = stderr.decode("utf-8", errors="replace").strip()
        print(f"tcpdump failed ({proc.returncode}): {message}", file=sys.stderr)
        return 4

    duration = time.monotonic() - started
    report = analyzer.report(duration, args.interface)
    report["capture"]["interrupted_by_user"] = interrupted
    output = Path(args.output) if args.output else _default_output()
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Passive OTA report written to {output}")
    print(f"Packets observed: {analyzer.packet_count}")
    print("No packet payload or logger IP was stored.")
    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Passively observe TSUN logger cloud/OTA network metadata without sending traffic."
    )
    parser.add_argument("--host", required=True, help="Logger IPv4 address (never stored in output)")
    parser.add_argument(
        "--duration", type=float, default=180.0, help="Capture duration in seconds (default: 180)"
    )
    parser.add_argument("--interface", help="tcpdump interface, e.g. any, eth0, en0")
    parser.add_argument("--output", help="JSON output path")
    parser.add_argument("--tcpdump", help="Path to tcpdump-compatible capture binary")
    parser.add_argument("--version", action="version", version=TOOL_VERSION)
    return parser


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()
    if args.duration <= 0 or args.duration > 3600:
        parser.error("--duration must be > 0 and <= 3600 seconds")
    try:
        ip = ipaddress.ip_address(args.host)
    except ValueError as exc:
        parser.error(str(exc))
    if ip.version != 4:
        parser.error("this first probe version supports IPv4 logger addresses only")
    return run_capture(args)


if __name__ == "__main__":
    raise SystemExit(main())
