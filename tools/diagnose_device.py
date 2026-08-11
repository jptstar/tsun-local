#!/usr/bin/env python3
# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Capture a privacy-safe TSUN Local diagnostic without Home Assistant."""

from __future__ import annotations

import argparse
import asyncio
from datetime import UTC, datetime
import importlib.util
import json
from pathlib import Path
import sys


PROTOCOLS_PATH = (
    Path(__file__).parents[1] / "custom_components" / "tsun_local" / "protocols"
)
SPEC = importlib.util.spec_from_file_location(
    "tsun_local_capture",
    PROTOCOLS_PATH / "__init__.py",
    submodule_search_locations=[str(PROTOCOLS_PATH)],
)
assert SPEC is not None and SPEC.loader is not None
PROTOCOLS = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PROTOCOLS
SPEC.loader.exec_module(PROTOCOLS)

from tsun_local_capture import (  # noqa: E402
    DEFAULT_PROTOCOL,
    SUPPORTED_PROTOCOLS,
    create_protocol_client,
)
from tsun_local_capture.ap import safe_error_details  # noqa: E402


def _positive_port(value: str) -> int:
    """Validate a TCP port supplied on the command line."""
    port = int(value)
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("port must be between 1 and 65535")
    return port


def _read_monitor_sn() -> int:
    """Read the Monitor SN interactively so it is not stored in shell history."""
    value = input("Numeric Monitor SN: ").strip()
    monitor_sn = int(value)
    if not 0 <= monitor_sn <= 0xFFFFFFFF:
        raise ValueError("Monitor SN must be between 0 and 4294967295")
    return monitor_sn


async def _capture(args: argparse.Namespace, monitor_sn: int) -> tuple[dict, int]:
    """Poll once and create an anonymized capture document."""
    client = create_protocol_client(
        args.protocol, args.host, args.port, monitor_sn
    )
    document: dict = {
        "format": "tsun-local-diagnostic",
        "schema_version": 1,
        "created_at": datetime.now(UTC).isoformat(),
        "privacy": {
            "network_address_included": False,
            "logger_number_included": False,
            "ap_envelope_included": False,
        },
    }
    try:
        result = await client.async_read_all()
    except Exception as err:
        document.update(
            {
                "result": "failure",
                "detected_protocol": client.protocol_name,
                "error": safe_error_details(err),
            }
        )
        exit_code = 1
    else:
        document.update(
            {
                "result": "success",
                "detected_protocol": client.protocol_name,
                "model_family": client.model,
                "pv_count": client.pv_count,
                "duration_ms": result.duration_ms,
                "blocks_ok": result.blocks_ok,
                "measurements": result.measurements,
            }
        )
        exit_code = 0
    document["protocol_trace"] = list(client.diagnostic_trace)
    return document, exit_code


def main() -> int:
    """Capture one device poll and save its anonymized result as JSON."""
    parser = argparse.ArgumentParser(
        description="Create an anonymized TSUN Local diagnostic capture."
    )
    parser.add_argument("--host", required=True, help="local device IP address")
    parser.add_argument("--port", type=_positive_port, default=8899)
    parser.add_argument(
        "--protocol",
        choices=(DEFAULT_PROTOCOL, *SUPPORTED_PROTOCOLS),
        default=DEFAULT_PROTOCOL,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("tsun_local_diagnostic.json"),
        help="destination JSON file",
    )
    args = parser.parse_args()

    try:
        monitor_sn = _read_monitor_sn()
        document, exit_code = asyncio.run(_capture(args, monitor_sn))
        args.output.write_text(
            json.dumps(document, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except (OSError, ValueError, EOFError) as err:
        print(f"Unable to create the diagnostic: {type(err).__name__}")
        return 2

    print(f"Diagnostic saved to: {args.output.resolve()}")
    print("The file does not contain the device IP address or Monitor SN.")
    print(f"Result: {document['result']}")
    if document.get("detected_protocol"):
        print(f"Detected protocol: {document['detected_protocol']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
