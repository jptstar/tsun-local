#!/usr/bin/env python3
# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Test privacy-safe UDP discovery without changing device settings."""

from __future__ import annotations

import argparse
import json
import re
import socket
import time


DEFAULT_PORT = 48899
DEFAULT_TIMEOUT = 5.0
DISCOVERY_MESSAGES = (
    b"WIFIKIT-214028-READ",
    b"HF-A11ASSISTHREAD",
    b"devicelinkfind",
)

_IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_MAC = re.compile(r"\b[0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5}\b")
_SERIAL = re.compile(r"\b(?:[1-9]\d{7,9}|[A-Za-z]\w{11,31})\b")


def _mask_ip(match: re.Match[str]) -> str:
    parts = match.group(0).split(".")
    return ".".join((*parts[:3], "xxx"))


def _mask_mac(match: re.Match[str]) -> str:
    parts = match.group(0).upper().split(":")
    return ":".join((*parts[:3], "XX", "XX", "XX"))


def sanitize(value: str) -> str:
    """Mask identifiers while preserving the response structure."""
    value = _MAC.sub(_mask_mac, value)
    value = _IPV4.sub(_mask_ip, value)
    return _SERIAL.sub("<SERIAL>", value)


def _response_summary(payload: bytes) -> str:
    text = payload.decode("utf-8", errors="replace").strip("\x00\r\n ")
    try:
        parsed = json.loads(text)
    except (ValueError, TypeError):
        return sanitize(text) if text else f"<{len(payload)} binary bytes>"
    return sanitize(json.dumps(parsed, sort_keys=True, ensure_ascii=False))


def discover(targets: list[str], port: int, timeout: float) -> int:
    """Send read-only discovery probes and print anonymized replies."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    try:
        sock.bind(("", port))
    except OSError as err:
        print(f"ERROR: impossible d'écouter UDP/{port}: {err}")
        sock.close()
        return 2

    total_replies = 0
    for target_index, target in enumerate(targets, start=1):
        for message in DISCOVERY_MESSAGES:
            try:
                sock.sendto(message, (target, port))
            except OSError as err:
                print(f"AVERTISSEMENT: envoi vers {target}:{port} impossible: {err}")
        print(
            f"CIBLE[{target_index}]={target}:{port}; "
            f"écoute pendant {timeout:g} s…"
        )
        deadline = time.monotonic() + timeout
        replies: set[tuple[str, bytes]] = set()
        while (remaining := deadline - time.monotonic()) > 0:
            sock.settimeout(remaining)
            try:
                payload, (source, _source_port) = sock.recvfrom(4096)
            except socket.timeout:
                break
            except OSError as err:
                print(f"ERROR: réception UDP impossible: {err}")
                sock.close()
                return 2
            if payload not in DISCOVERY_MESSAGES:
                replies.add((source, payload))

        print(f"CIBLE[{target_index}]_RÉPONSES={len(replies)}")
        total_replies += len(replies)
        for reply_index, (source, payload) in enumerate(
            sorted(replies), start=1
        ):
            label = f"{target_index}.{reply_index}"
            print(
                f"[{label}] source={sanitize(source)} "
                f"longueur={len(payload)}"
            )
            print(f"[{label}] contenu={_response_summary(payload)}")

    sock.close()
    if not total_replies:
        print("AUCUNE_RÉPONSE_UDP")
        return 1
    print(f"RÉPONSES_UDP_VALIDES={total_replies}")
    return 0


def main() -> int:
    """Run the command-line diagnostic."""
    parser = argparse.ArgumentParser(
        description=(
            "Teste les annonces UDP locales des loggers TSUN sans modifier "
            "leur configuration."
        )
    )
    parser.add_argument(
        "--target",
        action="append",
        default=[],
        help=(
            "adresse de diffusion à tester; option répétable "
            "(défaut: 255.255.255.255)"
        ),
    )
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    args = parser.parse_args()
    targets = list(dict.fromkeys(args.target or ["255.255.255.255"]))
    if not 1 <= args.port <= 65535 or args.timeout <= 0:
        parser.error("port ou délai invalide")
    return discover(targets, args.port, args.timeout)


if __name__ == "__main__":
    raise SystemExit(main())
