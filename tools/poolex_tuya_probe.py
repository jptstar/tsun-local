#!/usr/bin/env python3
# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Read-only Poolex/Tuya LAN diagnostic probe for TSUN Local research.

This experimental helper is intentionally separate from ``tsun_dump.py`` until
Poolex/Tuya hardware has been validated on a real device. It never sends a
Tuya control command. Without TinyTuya it can still listen for Tuya discovery
traffic and perform a bounded TCP/6668 reachability scan. When TinyTuya is
installed it can additionally decode Tuya LAN discovery broadcasts. A real
read-only ``status()`` request is attempted only when the user explicitly
provides a Device ID and Local Key.

Typical use::

    python poolex_tuya_probe.py --network 10.10.0.0/24 --output poolex_tuya.json

Optional full local read (requires TinyTuya and the device local key)::

    python poolex_tuya_probe.py --host 10.10.0.42 --device-id <id> \
        --local-key <16-char-key> --version 3.4 --output poolex_tuya.json

The local key is never written to the report.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
from ipaddress import IPv4Address, IPv4Network, ip_network
import json
from pathlib import Path
import select
import socket
import sys
import time
from typing import Any, Iterable


TOOL_VERSION = "0.1.0"
REPORT_FORMAT = "tsun-local-poolex-tuya-probe"
TUYA_TCP_PORT = 6668
TUYA_UDP_PORTS = (6666, 6667, 7000)
DEFAULT_TIMEOUT = 20.0
DEFAULT_CONNECT_TIMEOUT = 0.35
DEFAULT_WORKERS = 64
MIN_SCAN_PREFIX = 24
MAX_UDP_PACKET = 65535


@dataclass(slots=True)
class TcpCandidate:
    host: str
    port: int = TUYA_TCP_PORT


@dataclass(slots=True)
class UdpObservation:
    source_host: str
    source_port: int
    listen_port: int
    size: int
    framing: str
    json_keys: list[str]
    product_id: str | None = None
    protocol_version: str | None = None
    device_id_hash: str | None = None


def _hash_identifier(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", "replace")).hexdigest()[:16]


def _parse_network(value: str) -> IPv4Network:
    try:
        network = ip_network(value.strip(), strict=False)
    except ValueError as err:
        raise argparse.ArgumentTypeError(str(err)) from err
    if not isinstance(network, IPv4Network):
        raise argparse.ArgumentTypeError("only IPv4 networks are supported")
    if network.prefixlen < MIN_SCAN_PREFIX:
        raise argparse.ArgumentTypeError(
            f"network scan must be /{MIN_SCAN_PREFIX} or smaller (for example /24)"
        )
    return network


def _local_ipv4_addresses() -> set[str]:
    addresses: set[str] = set()
    try:
        for item in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            address = item[4][0]
            if not address.startswith("127."):
                addresses.add(address)
    except OSError:
        pass

    # This does not transmit application data; connect() on UDP only asks the OS
    # which local interface would be used for that destination.
    for remote in (("1.1.1.1", 53), ("8.8.8.8", 53)):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.connect(remote)
                address = sock.getsockname()[0]
                if address and not address.startswith("127."):
                    addresses.add(address)
        except OSError:
            continue
    return addresses


def _default_networks() -> set[IPv4Network]:
    return {
        ip_network(f"{address}/24", strict=False)
        for address in _local_ipv4_addresses()
        if not address.startswith("169.254.")
    }


def _hosts(networks: Iterable[IPv4Network], explicit_hosts: Iterable[str]) -> list[str]:
    result: set[str] = set()
    for host in explicit_hosts:
        try:
            result.add(str(IPv4Address(host.strip())))
        except ValueError as err:
            raise ValueError(f"invalid IPv4 host: {host}") from err
    for network in networks:
        result.update(str(host) for host in network.hosts())
    return sorted(result, key=lambda value: int(IPv4Address(value)))


def _tcp_open(host: str, timeout: float) -> bool:
    try:
        with socket.create_connection((host, TUYA_TCP_PORT), timeout=timeout):
            return True
    except OSError:
        return False


def scan_tcp_6668(hosts: list[str], timeout: float, workers: int) -> list[TcpCandidate]:
    if not hosts:
        return []
    found: list[TcpCandidate] = []
    with ThreadPoolExecutor(max_workers=min(workers, len(hosts))) as executor:
        futures = {executor.submit(_tcp_open, host, timeout): host for host in hosts}
        for future in as_completed(futures):
            host = futures[future]
            try:
                opened = bool(future.result())
            except Exception:
                opened = False
            if opened:
                found.append(TcpCandidate(host=host))
    return sorted(found, key=lambda item: int(IPv4Address(item.host)))


def _framing(payload: bytes, listen_port: int) -> str:
    if payload.startswith(b"\x00\x00\x55\xaa"):
        return "tuya-55aa"
    if payload.startswith(b"\x00\x00\x66\x99"):
        return "tuya-6699"
    stripped = payload.lstrip()
    if stripped.startswith(b"{"):
        return "json/plaintext"
    if listen_port == 6667:
        return "tuya-encrypted/6667"
    if listen_port == 7000:
        return "tuya-app/7000"
    return "unknown"


def _parse_plain_json(payload: bytes) -> dict[str, Any] | None:
    try:
        text = payload.decode("utf-8", "strict").strip("\x00\r\n \t")
        value = json.loads(text)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _observation_from_payload(
    payload: bytes,
    source: tuple[str, int],
    listen_port: int,
    decoded: dict[str, Any] | None = None,
) -> UdpObservation:
    parsed = decoded if decoded is not None else _parse_plain_json(payload)
    keys: list[str] = []
    product_id: str | None = None
    version: str | None = None
    device_hash: str | None = None
    if isinstance(parsed, dict):
        keys = sorted(str(key) for key in parsed.keys())[:32]
        product = parsed.get("productKey") or parsed.get("product_id") or parsed.get("productId")
        if isinstance(product, str) and product:
            product_id = product[:128]
        protocol = parsed.get("version") or parsed.get("ver")
        if isinstance(protocol, (str, int, float)):
            version = str(protocol)[:16]
        dev_id = parsed.get("gwId") or parsed.get("devId") or parsed.get("id")
        if isinstance(dev_id, str) and dev_id:
            device_hash = _hash_identifier(dev_id)
    return UdpObservation(
        source_host=source[0],
        source_port=int(source[1]),
        listen_port=listen_port,
        size=len(payload),
        framing=_framing(payload, listen_port),
        json_keys=keys,
        product_id=product_id,
        protocol_version=version,
        device_id_hash=device_hash,
    )


def listen_udp(timeout: float) -> tuple[list[UdpObservation], list[str]]:
    sockets: list[socket.socket] = []
    warnings: list[str] = []
    for port in TUYA_UDP_PORTS:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("", port))
        except OSError as err:
            warnings.append(f"UDP {port} listener unavailable: {type(err).__name__}")
            sock.close()
            continue
        sock.setblocking(False)
        sockets.append(sock)

    observations: list[UdpObservation] = []
    deadline = time.monotonic() + timeout
    try:
        while sockets:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            readable, _, _ = select.select(sockets, [], [], min(0.5, remaining))
            for sock in readable:
                try:
                    payload, source = sock.recvfrom(MAX_UDP_PACKET)
                except OSError:
                    continue
                observations.append(
                    _observation_from_payload(payload, source, int(sock.getsockname()[1]))
                )
    finally:
        for sock in sockets:
            sock.close()
    return observations, warnings


def _tiny_tuya_import() -> tuple[Any | None, str | None]:
    try:
        import tinytuya  # type: ignore
    except Exception as err:
        return None, f"{type(err).__name__}: {err}"
    return tinytuya, None


def tinytuya_discovery(timeout: float) -> tuple[list[dict[str, Any]], str | None]:
    tinytuya, import_error = _tiny_tuya_import()
    if tinytuya is None:
        return [], import_error
    try:
        found = tinytuya.deviceScan(False, max(1, int(round(timeout))))
    except Exception as err:
        return [], f"{type(err).__name__}: {err}"

    results: list[dict[str, Any]] = []
    if isinstance(found, dict):
        for host, raw in found.items():
            if not isinstance(raw, dict):
                raw = {}
            dev_id = raw.get("gwId") or raw.get("id") or raw.get("devId")
            product_id = raw.get("productKey") or raw.get("product_id") or raw.get("productId")
            version = raw.get("version") or raw.get("ver")
            results.append(
                {
                    "host": str(host),
                    "device_id_hash": _hash_identifier(str(dev_id)) if dev_id else None,
                    "product_id": str(product_id)[:128] if product_id else None,
                    "version": str(version)[:16] if version is not None else None,
                    "raw_keys": sorted(str(key) for key in raw.keys())[:40],
                }
            )
    return results, None


def read_status(
    *,
    host: str,
    device_id: str,
    local_key: str,
    version: str,
    timeout: float,
) -> dict[str, Any]:
    tinytuya, import_error = _tiny_tuya_import()
    if tinytuya is None:
        return {
            "attempted": False,
            "ok": False,
            "reason": "tinytuya_not_installed",
            "detail": import_error,
        }
    if len(local_key) != 16:
        return {
            "attempted": False,
            "ok": False,
            "reason": "invalid_local_key_length",
        }
    try:
        protocol_version = float(version)
    except ValueError:
        return {"attempted": False, "ok": False, "reason": "invalid_protocol_version"}

    try:
        device = tinytuya.Device(
            device_id,
            host,
            local_key,
            version=protocol_version,
            connection_timeout=min(max(timeout, 1.0), 10.0),
        )
        response = device.status()
    except Exception as err:
        return {
            "attempted": True,
            "ok": False,
            "error_type": type(err).__name__,
        }

    safe: dict[str, Any] = {
        "attempted": True,
        "ok": isinstance(response, dict),
        "device_id_hash": _hash_identifier(device_id),
        "version": version,
    }
    if isinstance(response, dict):
        dps = response.get("dps")
        if isinstance(dps, dict):
            # DPS values are read-only telemetry/state. Keep them because this
            # probe is specifically intended to discover the MX800 mapping.
            safe["dps"] = dps
            safe["dps_ids"] = sorted(str(key) for key in dps.keys())
        safe["response_keys"] = sorted(str(key) for key in response.keys())
        if "Error" in response:
            safe["error"] = str(response.get("Error"))[:240]
    return safe


def _deduplicate_udp(observations: list[UdpObservation]) -> list[UdpObservation]:
    unique: dict[tuple[Any, ...], UdpObservation] = {}
    for item in observations:
        key = (
            item.source_host,
            item.source_port,
            item.listen_port,
            item.framing,
            item.product_id,
            item.protocol_version,
            item.device_id_hash,
            tuple(item.json_keys),
        )
        unique[key] = item
    return sorted(
        unique.values(),
        key=lambda item: (int(IPv4Address(item.source_host)), item.listen_port, item.source_port),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only Poolex/Tuya LAN diagnostic probe for TSUN Local"
    )
    parser.add_argument(
        "--network",
        action="append",
        type=_parse_network,
        default=[],
        metavar="CIDR",
        help="IPv4 /24-or-smaller network to scan; may be repeated",
    )
    parser.add_argument(
        "--host",
        action="append",
        default=[],
        metavar="IP",
        help="explicit IPv4 device address; may be repeated",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help=f"UDP/TinyTuya discovery time in seconds (default {DEFAULT_TIMEOUT:g})",
    )
    parser.add_argument(
        "--connect-timeout",
        type=float,
        default=DEFAULT_CONNECT_TIMEOUT,
        help="TCP/6668 connect timeout",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_WORKERS,
        help="maximum parallel TCP scan workers",
    )
    parser.add_argument("--output", type=Path, default=Path("poolex_tuya_diagnostic.json"))

    # Optional read-only status transaction. These are intentionally explicit
    # and never inferred or persisted.
    parser.add_argument("--device-id", default="", help="Tuya Device ID for optional status read")
    parser.add_argument("--local-key", default="", help="Tuya 16-character local key (never saved)")
    parser.add_argument("--version", default="3.4", help="Tuya LAN version for optional status read")
    parser.add_argument(
        "--status-host",
        default="",
        help="device IP for optional status read; defaults to sole --host/TCP candidate",
    )
    return parser


def main() -> int:
    if sys.version_info < (3, 10):
        print("ERROR: Python 3.10 or newer is required.", file=sys.stderr)
        return 2

    args = build_parser().parse_args()
    if args.timeout <= 0 or args.connect_timeout <= 0 or args.workers <= 0:
        print("ERROR: timeout and workers values must be positive.", file=sys.stderr)
        return 2

    networks = set(args.network) if args.network else _default_networks()
    try:
        scan_hosts = _hosts(networks, args.host)
    except ValueError as err:
        print(f"ERROR: {err}", file=sys.stderr)
        return 2

    print("TSUN Local · Poolex/Tuya experimental LAN probe")
    print(f"v{TOOL_VERSION} · READ-ONLY")
    print("No Tuya control/write command is implemented.\n")
    if networks:
        print(
            "Networks:",
            ", ".join(
                str(network)
                for network in sorted(networks, key=lambda n: int(n.network_address))
            ),
        )
    if args.host:
        print("Explicit hosts:", ", ".join(args.host))

    print(f"Scanning TCP {TUYA_TCP_PORT}...")
    tcp = scan_tcp_6668(scan_hosts, args.connect_timeout, args.workers)
    print(f"TCP {TUYA_TCP_PORT} candidates: {len(tcp)}")

    print(f"Listening for Tuya UDP discovery on {TUYA_UDP_PORTS} for {args.timeout:g}s...")
    udp, udp_warnings = listen_udp(args.timeout)
    udp = _deduplicate_udp(udp)
    print(f"UDP observations: {len(udp)}")

    print("Running TinyTuya discovery when available...")
    tiny, tiny_error = tinytuya_discovery(args.timeout)
    if tiny_error:
        print("TinyTuya discovery unavailable.")
        print("Optional: python -m pip install tinytuya")
    else:
        print(f"TinyTuya devices: {len(tiny)}")

    status_host = args.status_host.strip()
    if not status_host and len(args.host) == 1:
        status_host = args.host[0].strip()
    if not status_host and len(tcp) == 1:
        status_host = tcp[0].host

    if args.device_id or args.local_key:
        if not (args.device_id and args.local_key and status_host):
            status = {
                "attempted": False,
                "ok": False,
                "reason": "device_id_local_key_and_status_host_are_all_required",
            }
        else:
            print(f"Attempting one read-only Tuya status transaction to {status_host}...")
            status = read_status(
                host=status_host,
                device_id=args.device_id,
                local_key=args.local_key,
                version=args.version,
                timeout=args.connect_timeout,
            )
            print("Status read:", "OK" if status.get("ok") else "not confirmed")
    else:
        status = {
            "attempted": False,
            "ok": False,
            "reason": "local_key_not_supplied",
            "note": "Discovery remains useful; encrypted DPS status requires the device local key.",
        }

    document = {
        "format": REPORT_FORMAT,
        "tool_version": TOOL_VERSION,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "read_only": True,
        "networks_scanned": [
            str(network)
            for network in sorted(networks, key=lambda n: int(n.network_address))
        ],
        "summary": {
            "tcp_6668_candidates": len(tcp),
            "udp_observations": len(udp),
            "tinytuya_devices": len(tiny),
            "status_attempted": bool(status.get("attempted")),
            "status_ok": bool(status.get("ok")),
        },
        "tcp_6668": [asdict(item) for item in tcp],
        "udp_discovery": [asdict(item) for item in udp],
        "udp_warnings": udp_warnings,
        "tinytuya": {
            "available": tiny_error is None,
            "error": tiny_error,
            "devices": tiny,
        },
        "status_read": status,
        "privacy": {
            "local_key_saved": False,
            "device_id_saved": False,
            "device_id_hash_only": True,
            "note": "IP addresses are retained because this is a local network diagnostic report.",
        },
    }

    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(document, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    except OSError as err:
        print(f"ERROR: could not write report: {err}", file=sys.stderr)
        return 1

    print(f"\nReport: {args.output}")
    if tcp or udp or tiny:
        print("Result: Tuya-compatible LAN activity/candidate(s) detected.")
        return 0
    print("Result: no Tuya LAN device detected during this run.")
    print("If the device is on another VLAN, run with --network on that VLAN or --host with its IP.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
