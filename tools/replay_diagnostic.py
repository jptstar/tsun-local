#!/usr/bin/env python3
# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Replay TSUN Local protocol responses from an anonymized diagnostic."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


PROTOCOLS_PATH = (
    Path(__file__).parents[1] / "custom_components" / "tsun_local" / "protocols"
)
SPEC = importlib.util.spec_from_file_location(
    "tsun_local_replay",
    PROTOCOLS_PATH / "__init__.py",
    submodule_search_locations=[str(PROTOCOLS_PATH)],
)
assert SPEC is not None and SPEC.loader is not None
PROTOCOLS = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PROTOCOLS
SPEC.loader.exec_module(PROTOCOLS)

from tsun_local_replay.protocol_02b0 import (  # noqa: E402
    decode_alarms as decode_02b0_alarms,
    decode_measurements as decode_02b0_measurements,
    detect_pv_count as detect_02b0_pv_count,
    parse_modbus_response,
)
from tsun_local_replay.protocol_1511 import (  # noqa: E402
    PV_COUNT as PV_COUNT_1511,
    decode_alarms as decode_1511_alarms,
    decode_measurements as decode_1511_measurements,
    parse_1511_response,
)
from tsun_local_replay.ap import TsunProtocolError  # noqa: E402


def _find_trace(value: Any) -> list[dict[str, Any]] | None:
    """Find protocol_trace in a standalone or Home Assistant diagnostic."""
    if isinstance(value, dict):
        trace = value.get("protocol_trace")
        if isinstance(trace, list):
            return trace
        for nested in value.values():
            found = _find_trace(nested)
            if found is not None:
                return found
    elif isinstance(value, list):
        for nested in value:
            found = _find_trace(nested)
            if found is not None:
                return found
    return None


def _hex_int(event: dict[str, Any], key: str) -> int:
    """Read a hexadecimal integer from one trace event."""
    return int(str(event[key]), 16)


def replay(trace: list[dict[str, Any]]) -> dict[str, Any]:
    """Re-run parsers and decoders against captured inner responses."""
    registers: dict[str, dict[int, int]] = {"1511": {}, "02b0": {}}
    parsed_blocks = 0
    errors: list[dict[str, str]] = []
    transport_failures: list[dict[str, Any]] = []

    for event in trace:
        response_text = event.get("response_payload")
        if not isinstance(response_text, str):
            if "error" in event:
                transport_failures.append(
                    {
                        "protocol": str(event.get("protocol", "unknown")),
                        "stage": str(event.get("stage", "unknown")),
                        "error": event["error"],
                    }
                )
            continue
        protocol = str(event.get("protocol", ""))
        try:
            frame = bytes.fromhex(response_text)
            function = _hex_int(event, "function")
            start = _hex_int(event, "start_register")
            end = _hex_int(event, "end_register")
            if protocol == "1511":
                values = parse_1511_response(
                    frame,
                    _hex_int(event, "address_tag"),
                    function,
                    start,
                    end,
                )
            elif protocol == "02b0":
                values = parse_modbus_response(frame, function, start, end)
            else:
                raise ValueError("unsupported protocol in trace")
            registers[protocol].update(values)
            parsed_blocks += 1
        except (KeyError, TypeError, ValueError, TsunProtocolError) as err:
            errors.append(
                {
                    "protocol": protocol or "unknown",
                    "start_register": str(event.get("start_register", "unknown")),
                    "error": type(err).__name__,
                }
            )

    decoded: dict[str, Any] = {}
    for protocol, values in registers.items():
        if not values:
            continue
        try:
            if protocol == "1511":
                pv_count = PV_COUNT_1511
                measurements = decode_1511_measurements(values, pv_count)
                measurements.update(decode_1511_alarms(values, pv_count))
            else:
                pv_count = detect_02b0_pv_count(values)
                measurements = decode_02b0_measurements(values, pv_count)
                measurements.update(decode_02b0_alarms(values))
        except KeyError as err:
            decoded[protocol] = {
                "status": "partial_capture",
                "registers_parsed": len(values),
                "missing_register": f"0x{int(err.args[0]):04X}",
            }
        else:
            decoded[protocol] = {
                "status": "decoded",
                "pv_count": pv_count,
                "measurements": measurements,
            }

    return {
        "parsed_blocks": parsed_blocks,
        "parser_errors": errors,
        "transport_failures": transport_failures,
        "protocols": decoded,
    }


def main() -> int:
    """Load one diagnostic file and print the replay result."""
    parser = argparse.ArgumentParser(
        description="Replay an anonymized TSUN Local diagnostic."
    )
    parser.add_argument("diagnostic", type=Path)
    args = parser.parse_args()

    try:
        document = json.loads(args.diagnostic.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        print(f"Unable to read the diagnostic: {type(err).__name__}")
        return 2

    trace = _find_trace(document)
    if trace is None:
        print("No TSUN Local protocol trace was found in this file.")
        return 1
    print(json.dumps(replay(trace), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
