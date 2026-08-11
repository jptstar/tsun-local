# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Run a private local 02B0 connection test without Home Assistant."""

from __future__ import annotations

import argparse
import asyncio
import importlib.util
import logging
from pathlib import Path
import sys


PROTOCOLS_PATH = (
    Path(__file__).parents[1]
    / "custom_components"
    / "tsun_local"
    / "protocols"
)
SPEC = importlib.util.spec_from_file_location(
    "tsun_local_diagnostic",
    PROTOCOLS_PATH / "__init__.py",
    submodule_search_locations=[str(PROTOCOLS_PATH)],
)
assert SPEC is not None and SPEC.loader is not None
PROTOCOLS = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PROTOCOLS
SPEC.loader.exec_module(PROTOCOLS)

from tsun_local_diagnostic.protocol_02b0 import Tsun02b0Client  # noqa: E402


def _positive_port(value: str) -> int:
    """Validate a TCP port supplied on the command line."""
    port = int(value)
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("port must be between 1 and 65535")
    return port


def _read_monitor_sn() -> int:
    """Read the Monitor SN interactively so it is not stored in shell history."""
    value = input("Monitor SN numérique : ").strip()
    monitor_sn = int(value)
    if not 0 <= monitor_sn <= 0xFFFFFFFF:
        raise ValueError("Monitor SN must be between 0 and 4294967295")
    return monitor_sn


async def _run(host: str, port: int, monitor_sn: int, timeout: float) -> int:
    """Read the MX device once and print a privacy-safe result."""
    client = Tsun02b0Client(host, port, monitor_sn, timeout=timeout)
    try:
        result = await client.async_read_all()
    except Exception as err:
        print(f"ÉCHEC : {type(err).__name__}: {err}")
        return 1

    print("SUCCÈS : réponse 02B0 valide")
    print(f"Blocs lus : {result.blocks_ok}")
    print(f"Durée : {result.duration_ms} ms")
    print(f"Entrées PV détectées : {client.pv_count}")
    return 0


def main() -> int:
    """Parse arguments and run the asynchronous diagnostic."""
    parser = argparse.ArgumentParser(
        description="Teste directement une connexion locale TSUN 02B0."
    )
    parser.add_argument("--host", required=True, help="adresse IP du micro-onduleur")
    parser.add_argument("--port", type=_positive_port, default=8899)
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
    try:
        monitor_sn = _read_monitor_sn()
    except (ValueError, EOFError) as err:
        print(f"Monitor SN invalide : {err}")
        return 2

    return asyncio.run(_run(args.host, args.port, monitor_sn, args.timeout))


if __name__ == "__main__":
    raise SystemExit(main())
