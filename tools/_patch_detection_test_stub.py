#!/usr/bin/env python3
"""Patch the lightweight config-flow protocol stub for 1.6.2 tests."""

from pathlib import Path

path = Path("tests/test_config_flow_continuation.py")
text = path.read_text(encoding="utf-8")
old = '''    _module(
        f"{PACKAGE}.protocols",
        DEFAULT_PROTOCOL="auto",
        FORCE_PROTOCOL="force_probe",
        SUPPORTED_PROTOCOLS=("1511", "1097", "02b0"),
        protocol_from_firmware=lambda firmware: next(
            (
                protocol
                for protocol in ("1511", "1097", "02b0")
                if protocol in str(firmware).lower()
            ),
            None,
        ),
        create_protocol_client=lambda *args: None,
    )
'''
new = '''    _module(
        f"{PACKAGE}.protocols",
        DEFAULT_PROTOCOL="auto",
        DETECTION_MIN_SCORE=80,
        FORCE_PROTOCOL="force_probe",
        SUPPORTED_PROTOCOLS=("1511", "1097", "02b0"),
        score_protocol_candidate=lambda *args: SimpleNamespace(
            hard_valid=True, score=100
        ),
        create_protocol_client=lambda *args: None,
    )
'''
if old not in text:
    raise SystemExit("config-flow protocol stub not found")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
