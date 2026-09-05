#!/usr/bin/env python3
"""One-shot patch helper for TSUN dump 02B0 characterization."""

from pathlib import Path

ROOT = Path(__file__).parents[2]
DUMP = ROOT / "tools" / "tsun_dump.py"
TESTS = ROOT / "tests" / "test_tsun_dump_tool.py"
DOCS = ROOT / "docs" / "HARDWARE_DUMP.md"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


text = DUMP.read_text(encoding="utf-8")
text = replace_once(
    text,
    'TOOL_VERSION = "2.5.1"',
    'TOOL_VERSION = "2.6.0"',
    "tool version",
)
text = replace_once(
    text,
    'PROTOCOL_RETRY_DELAY = 0.4\nSUPPORTED_PROTOCOLS = ("1511", "02b0", "1097")',
    'PROTOCOL_RETRY_DELAY = 0.4\n'
    'CHARACTERIZATION_REPEATS = 3\n'
    'CHARACTERIZATION_CONTROL_REPEATS = 2\n'
    'CHARACTERIZATION_TIMEOUT_CAP = 2.0\n'
    'CHARACTERIZATION_MARKER_WAIT = 1.0\n'
    'CHARACTERIZATION_DELAY = 0.15\n'
    'SHORT_LOGGER_MARKERS = (b"\\x05\\x00", b"\\x06\\x00")\n'
    'SUPPORTED_PROTOCOLS = ("1511", "02b0", "1097")',
    "characterization constants",
)

read_modbus_anchor = '''def read_modbus_block(
    host: str,
    port: int,
    logger_sn: int,
    start: int,
    end: int,
    *,
    sensor_list: int,
    timeout: float,
) -> tuple[dict[int, int], bytes, bytes]:
    payload = build_modbus_request(start, end)
    response = exchange_ap(
        host, port, logger_sn, payload, sensor_list=sensor_list, timeout=timeout
    )
    return parse_modbus_response(response, start, end), payload, response
'''
characterization_code = read_modbus_anchor + r'''


def _observe_02b0_read(
    host: str,
    port: int,
    logger_sn: int,
    start: int,
    end: int,
    *,
    sensor_list: int,
    timeout: float,
    marker_wait: float = CHARACTERIZATION_MARKER_WAIT,
) -> dict[str, Any]:
    """Observe one read without treating short logger markers as Modbus data."""
    payload = build_modbus_request(start, end)
    request = build_ap_frame(logger_sn, payload, sensor_list=sensor_list)
    started = time.monotonic()
    with socket.create_connection((host, port), timeout=timeout) as sock:
        sock.settimeout(timeout)
        sock.sendall(request)
        first_frame = read_ap_frame(sock)
        first_latency_ms = round((time.monotonic() - started) * 1000, 1)
        first_payload = parse_ap_frame(first_frame)
        observation: dict[str, Any] = {
            "result": "failure",
            "latency_ms": first_latency_ms,
            "request_payload": payload.hex(" ").upper(),
            "first_payload": first_payload.hex(" ").upper(),
            "first_payload_bytes": len(first_payload),
        }

        if first_payload in SHORT_LOGGER_MARKERS:
            observation["result"] = "short_marker_only"
            observation["short_marker"] = first_payload.hex(" ").upper()
            followup_started = time.monotonic()
            try:
                sock.settimeout(min(timeout, marker_wait))
                second_frame = read_ap_frame(sock)
                second_payload = parse_ap_frame(second_frame)
            except (socket.timeout, TimeoutError):
                observation["followup"] = "none_before_timeout"
                observation["followup_wait_ms"] = round(
                    (time.monotonic() - followup_started) * 1000, 1
                )
                return observation
            except Exception as err:
                observation["followup"] = "invalid"
                observation["followup_error"] = safe_error_details(err)
                return observation

            observation["followup_payload"] = second_payload.hex(" ").upper()
            observation["followup_payload_bytes"] = len(second_payload)
            observation["followup_wait_ms"] = round(
                (time.monotonic() - followup_started) * 1000, 1
            )
            try:
                registers = parse_modbus_response(second_payload, start, end)
            except Exception as err:
                observation["followup"] = "non_modbus"
                observation["followup_error"] = safe_error_details(err)
            else:
                observation["result"] = "success_after_short_marker"
                observation["followup"] = "valid_modbus"
                observation["register_count"] = len(registers)
            return observation

        try:
            registers = parse_modbus_response(first_payload, start, end)
        except Exception as err:
            observation["error"] = safe_error_details(err)
        else:
            observation["result"] = "success"
            observation["register_count"] = len(registers)
        return observation


def _attempt_succeeded(attempt: dict[str, Any]) -> bool:
    return attempt.get("result") in ("success", "success_after_short_marker")


def _summarize_characterization_test(test: dict[str, Any]) -> None:
    attempts = test.get("attempts", [])
    test["successes"] = sum(_attempt_succeeded(item) for item in attempts)
    test["short_marker_only"] = sum(
        item.get("result") == "short_marker_only" for item in attempts
    )
    test["success_after_short_marker"] = sum(
        item.get("result") == "success_after_short_marker" for item in attempts
    )


def _characterization_test_by_id(
    tests: list[dict[str, Any]], test_id: str
) -> dict[str, Any] | None:
    return next((item for item in tests if item.get("id") == test_id), None)


def analyze_02b0_characterization(
    tests: list[dict[str, Any]], controls: list[dict[str, Any]]
) -> dict[str, Any]:
    """Classify only conclusions directly supported by the read matrix."""
    by_id = {item["id"]: item for item in tests}

    def successes(test_id: str) -> int:
        item = by_id.get(test_id)
        return int(item.get("successes", 0)) if item else 0

    over_16_ids = ("cross_boundary_17", "legacy_v153_22", "current_v154_v160_23")
    any_over_16_success = any(successes(test_id) for test_id in over_16_ids)
    if any_over_16_success:
        size_limit = "not_a_strict_16_register_limit"
    elif successes("cross_boundary_16") and successes("dynamic_3010_16"):
        size_limit = "evidence_supports_max_16_registers"
    else:
        size_limit = "inconclusive"

    short_markers = sorted(
        {
            attempt["short_marker"]
            for item in [*tests, *controls]
            for attempt in item.get("attempts", [])
            if attempt.get("short_marker")
        }
    )
    followup_modbus = any(
        attempt.get("result") == "success_after_short_marker"
        for item in [*tests, *controls]
        for attempt in item.get("attempts", [])
    )

    canonical_current = _characterization_test_by_id(tests, "current_v154_v160_23")
    control_current = _characterization_test_by_id(
        controls, "current_v154_v160_23_sensor_list_0000"
    )
    selector_comparison = "inconclusive"
    if canonical_current is not None and control_current is not None:
        canonical_ok = bool(canonical_current.get("successes"))
        control_ok = bool(control_current.get("successes"))
        if canonical_ok != control_ok:
            selector_comparison = "different_behavior_observed"
        elif canonical_ok and control_ok:
            selector_comparison = "both_selectors_succeeded"
        elif canonical_current.get("attempts") and control_current.get("attempts"):
            selector_comparison = "neither_selector_succeeded"

    return {
        "size_limit_16": size_limit,
        "register_0x3008_readable": bool(successes("start_3008_8")),
        "crosses_0x300F_boundary": bool(
            successes("cross_boundary_16") or successes("cross_boundary_17")
        ),
        "short_markers_seen": short_markers,
        "modbus_followup_after_short_marker_seen": followup_modbus,
        "sensor_list_02b0_vs_0000": selector_comparison,
        "interpretation_note": (
            "These are read-only observations, not assumptions about undocumented "
            "05 00 / 06 00 marker meanings."
        ),
    }


def characterize_02b0(
    host: str,
    port: int,
    logger_sn: int,
    timeout: float,
) -> dict[str, Any]:
    """Run a bounded, read-only matrix reproducing known 02B0 read shapes."""
    cases = (
        ("start_3008_8", 0x3008, 0x300F),
        ("cross_boundary_16", 0x3008, 0x3017),
        ("cross_boundary_17", 0x3008, 0x3018),
        ("legacy_v153_22", 0x3009, 0x301E),
        ("current_v154_v160_23", 0x3008, 0x301E),
        ("dynamic_3000_16", 0x3000, 0x300F),
        ("dynamic_3010_16", 0x3010, 0x301F),
        ("dynamic_3020_16", 0x3020, 0x302F),
    )
    test_timeout = min(timeout, CHARACTERIZATION_TIMEOUT_CAP)

    def run_case(
        test_id: str,
        start: int,
        end: int,
        sensor_list: int,
        repeats: int,
    ) -> dict[str, Any]:
        record: dict[str, Any] = {
            "id": test_id,
            "function": "0x03",
            "start": f"0x{start:04X}",
            "end": f"0x{end:04X}",
            "register_count": end - start + 1,
            "sensor_list": f"0x{sensor_list:04X}",
            "attempts": [],
        }
        for attempt_index in range(repeats):
            try:
                observation = _observe_02b0_read(
                    host,
                    port,
                    logger_sn,
                    start,
                    end,
                    sensor_list=sensor_list,
                    timeout=test_timeout,
                )
            except Exception as err:
                observation = {
                    "result": "failure",
                    "error": safe_error_details(err),
                }
            observation["attempt"] = attempt_index + 1
            record["attempts"].append(observation)
            if attempt_index + 1 < repeats:
                time.sleep(CHARACTERIZATION_DELAY)
        _summarize_characterization_test(record)
        return record

    tests = [
        run_case(test_id, start, end, 0x02B0, CHARACTERIZATION_REPEATS)
        for test_id, start, end in cases
    ]
    control_cases = (
        ("current_v154_v160_23_sensor_list_0000", 0x3008, 0x301E),
        ("dynamic_3010_16_sensor_list_0000", 0x3010, 0x301F),
    )
    controls = [
        run_case(test_id, start, end, 0x0000, CHARACTERIZATION_CONTROL_REPEATS)
        for test_id, start, end in control_cases
    ]
    return {
        "attempted": True,
        "read_only": True,
        "canonical_sensor_list": "0x02B0",
        "regular_dump_sensor_list": "0x0000",
        "timeout_seconds": test_timeout,
        "short_marker_followup_wait_seconds": CHARACTERIZATION_MARKER_WAIT,
        "tests": tests,
        "sensor_list_controls": controls,
        "analysis": analyze_02b0_characterization(tests, controls),
    }
'''
text = replace_once(
    text,
    read_modbus_anchor,
    characterization_code,
    "02b0 characterization functions",
)

# Make snapshot coherence explicit and never decode from a partial final snapshot.
old_snapshot = '''        snapshots.append(
            {
                "index": index + 1,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "registers": registers,
            }
        )
'''
new_snapshot = '''        successful_snapshot_blocks = sum(
            block["result"] == "success" for block in blocks
        )
        snapshots.append(
            {
                "index": index + 1,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "registers": registers,
                "coherent": successful_snapshot_blocks == len(blocks),
                "successful_blocks": successful_snapshot_blocks,
                "failed_blocks": len(blocks) - successful_snapshot_blocks,
            }
        )
'''
text = replace_once(text, old_snapshot, new_snapshot, "snapshot coherence")

old_latest = '''    latest = snapshots[-1]["registers"] if snapshots else {}
    merged = {**supplemental_registers, **latest}
'''
new_latest = '''    coherent_snapshots = [
        snapshot for snapshot in snapshots if snapshot.get("coherent") is True
    ]
    decoded_snapshot = coherent_snapshots[-1] if coherent_snapshots else None
    latest = decoded_snapshot["registers"] if decoded_snapshot is not None else {}
    merged = {**supplemental_registers, **latest}
'''
text = replace_once(text, old_latest, new_latest, "coherent snapshot selection")

old_logger_web = '''    logger_web = capture_logger_web_pages(host, args.http_page_timeout)

    return {
'''
new_logger_web = '''    logger_web = capture_logger_web_pages(host, args.http_page_timeout)
    protocol_characterization = (
        characterize_02b0(host, args.port, sn, args.timeout)
        if protocol == "02b0" and args.full
        else {
            "attempted": False,
            "reason": "requires a full 02B0 capture",
        }
    )

    return {
'''
text = replace_once(text, old_logger_web, new_logger_web, "characterization capture hook")

text = replace_once(
    text,
    '''        "logger_web": logger_web,
        "discovery": discovery,
''',
    '''        "logger_web": logger_web,
        "protocol_characterization": protocol_characterization,
        "discovery": discovery,
''',
    "characterization output field",
)

text = replace_once(
    text,
    '''            "snapshot_interval_seconds": args.interval,
            "successful_block_reads": successful,
''',
    '''            "snapshot_interval_seconds": args.interval,
            "coherent_snapshots": len(coherent_snapshots),
            "decoded_snapshot_index": (
                decoded_snapshot["index"] if decoded_snapshot is not None else None
            ),
            "successful_block_reads": successful,
''',
    "coherent snapshot summary",
)

DUMP.write_text(text, encoding="utf-8")

# Keep tests focused on deterministic classification and snapshot-safety helpers.
tests = TESTS.read_text(encoding="utf-8")
tests = replace_once(
    tests,
    'self.assertEqual(TOOL.TOOL_VERSION, "2.5.1")',
    'self.assertEqual(TOOL.TOOL_VERSION, "2.6.0")',
    "test tool version",
)
insert_anchor = '''    def test_1511_plan_uses_only_known_native_read_functions(self) -> None:
'''
new_tests = '''    def test_02b0_characterization_classifies_strict_16_limit(self) -> None:
        def record(test_id: str, successes: int) -> dict[str, object]:
            return {
                "id": test_id,
                "successes": successes,
                "attempts": [{"result": "success"}] if successes else [{"result": "failure"}],
            }

        tests = [
            record("start_3008_8", 1),
            record("cross_boundary_16", 1),
            record("cross_boundary_17", 0),
            record("legacy_v153_22", 0),
            record("current_v154_v160_23", 0),
            record("dynamic_3000_16", 1),
            record("dynamic_3010_16", 1),
            record("dynamic_3020_16", 1),
        ]
        analysis = TOOL.analyze_02b0_characterization(tests, [])
        self.assertEqual(
            analysis["size_limit_16"], "evidence_supports_max_16_registers"
        )
        self.assertTrue(analysis["register_0x3008_readable"])
        self.assertTrue(analysis["crosses_0x300F_boundary"])

    def test_02b0_characterization_rejects_strict_limit_if_17_succeeds(self) -> None:
        tests = [
            {"id": "cross_boundary_17", "successes": 1, "attempts": [{"result": "success"}]},
            {"id": "cross_boundary_16", "successes": 1, "attempts": [{"result": "success"}]},
            {"id": "dynamic_3010_16", "successes": 1, "attempts": [{"result": "success"}]},
        ]
        analysis = TOOL.analyze_02b0_characterization(tests, [])
        self.assertEqual(
            analysis["size_limit_16"], "not_a_strict_16_register_limit"
        )

    def test_02b0_characterization_preserves_short_marker_without_meaning(self) -> None:
        tests = [
            {
                "id": "current_v154_v160_23",
                "successes": 0,
                "attempts": [
                    {"result": "short_marker_only", "short_marker": "05 00"}
                ],
            }
        ]
        analysis = TOOL.analyze_02b0_characterization(tests, [])
        self.assertEqual(analysis["short_markers_seen"], ["05 00"])
        self.assertFalse(analysis["modbus_followup_after_short_marker_seen"])

'''+insert_anchor
tests = replace_once(tests, insert_anchor, new_tests, "characterization tests")
TESTS.write_text(tests, encoding="utf-8")

# Append concise documentation once; keep the normal dump privacy contract unchanged.
docs = DOCS.read_text(encoding="utf-8")
heading = "## 02B0 compatibility characterization"
if heading not in docs:
    docs = docs.rstrip() + '''

## 02B0 compatibility characterization

Full 02B0 captures run an additional strictly read-only characterization matrix. It reproduces the short and long telemetry read shapes used by TSUN Local, including the historical 1.5.3 block and the 1.5.4/1.6.0 block, and compares the explicit `0x02B0` AP sensor-list selector with the legacy `0x0000` selector on bounded control reads.

Short inner logger payloads such as `05 00` and `06 00` are preserved as unknown markers. The dumper briefly keeps the same socket open to observe whether a second AP envelope containing valid Modbus data follows; it does not assign an undocumented error meaning to those markers.

The JSON `protocol_characterization` section records every request shape, attempt result, inner response payload, response timing, optional follow-up payload and a conservative classification. This can distinguish a strict 16-register limit from register-boundary, selector, timing or short-marker behavior without writing to the inverter.

Dynamic snapshots now include a `coherent` flag. Only the latest snapshot in which every planned dynamic block succeeded is used for decoded measurements and PV-count inference. A partial later snapshot remains in the evidence but cannot overwrite a coherent earlier one or create false PV inputs from shifted/stale responses.
'''
    DOCS.write_text(docs + "\n", encoding="utf-8")

print("Applied 02B0 dump characterization patch")
