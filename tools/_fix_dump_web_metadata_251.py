#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DUMP = ROOT / "tools" / "tsun_dump.py"
TESTS = ROOT / "tests" / "test_tsun_dump_tool.py"
TOOLS_README = ROOT / "tools" / "README.md"
HARDWARE_DOC = ROOT / "docs" / "HARDWARE_DUMP.md"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, got {count}")
    return text.replace(old, new, 1)


def regex_replace_once(text: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.DOTALL)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one regex match, got {count}")
    return updated


dump = DUMP.read_text(encoding="utf-8")
dump = replace_once(
    dump,
    'TOOL_VERSION = "2.5.0"',
    'TOOL_VERSION = "2.5.1"',
    "tool version",
)

metadata_block = '''def _extract_logger_firmware(document: str) -> str | None:
    """Extract a real logger firmware value while ignoring UI help labels."""
    placeholders = {
        "main",
        "slave",
        "master",
        "primary",
        "secondary",
        "current",
        "version",
        "firmware",
        "number",
    }

    # Prefer explicit firmware variables. Optional quotes around the key also
    # cover JSON-like firmware pages in addition to the usual JavaScript form.
    explicit = re.compile(
        r'''["']?\\b(?:cover|webdata|logger|device|monitor)[_-]ver(?:sion)?\\b["']?'''
        r'''\\s*[:=]\\s*["']\\s*([A-Za-z0-9][A-Za-z0-9._-]{1,79})''',
        re.IGNORECASE,
    )
    if match := explicit.search(document):
        return match.group(1).strip()

    # Keep the existing visible-label fallback for alternate firmware layouts,
    # but reject generic UI text such as "Firmware version (main)".
    for pattern in _FIRMWARE_PATTERNS:
        for match in pattern.finditer(document):
            candidate = match.group(1).strip()
            if candidate.lower() in placeholders:
                continue
            return candidate
    return None


def _extract_logger_mac_oui(document: str) -> str | None:
    """Extract the logger MAC OUI only from actual named device fields."""
    mac_value = r"(?P<mac>[0-9A-F]{2}(?:[:-][0-9A-F]{2}){5})"
    field_names = (
        r"cover[_-]sta[_-]mac",
        r"cover[_-]ap[_-]mac",
        r"webdata[_-]mac",
        r"(?:logger|device|monitor|sta|ap)[_-]?mac",
        r"mac",
    )

    # Field priority matters: STA is the actual network-side logger identity
    # when both AP and STA values are present. Generic free-text MAC tokens are
    # deliberately ignored so examples such as "E.g. 00:01:02:..." cannot win.
    for field_name in field_names:
        assignment = re.compile(
            rf'''["']?\\b(?:{field_name})\\b["']?\\s*[:=]\\s*["']?\\s*{mac_value}''',
            re.IGNORECASE,
        )
        if match := assignment.search(document):
            token = _MAC_TOKEN.search(match.group("mac"))
            if token:
                return ":".join(part.upper() for part in token.groups()[:3])

        element = re.compile(
            rf'''(?:id|name)\\s*=\\s*["'](?:{field_name})["'][^>]*>\\s*{mac_value}''',
            re.IGNORECASE,
        )
        if match := element.search(document):
            token = _MAC_TOKEN.search(match.group("mac"))
            if token:
                return ":".join(part.upper() for part in token.groups()[:3])

    return None


def _logger_web_metadata(document: str) -> dict[str, Any]:
    """Extract non-identifying logger metadata plus a 3-character inverter prefix."""
    firmware = _extract_logger_firmware(document)
    inverter_serial = _first_web_match(_INVERTER_SERIAL_PATTERNS, document)
    raw_profile = _first_web_match(_RAW_PROFILE_PATTERNS, document)
    wifi_signal, wifi_unit, wifi_source = _parse_wifi_signal_metadata(document)
    mac_oui = _extract_logger_mac_oui(document)

    return {
        "logger_firmware_version": firmware,
        "logger_wifi_signal": wifi_signal,
        "logger_wifi_signal_unit": wifi_unit,
        "logger_wifi_signal_source": wifi_source,
        "logger_raw_profile": raw_profile,
        "logger_mac_oui": mac_oui,
        "inverter_serial_prefix": (inverter_serial[:3] if inverter_serial else None),
    }


def anonymize_web_document'''

dump = regex_replace_once(
    dump,
    r"def _logger_web_metadata\(document: str\) -> dict\[str, Any\]:\n.*?\n\ndef anonymize_web_document",
    metadata_block,
    "logger metadata parser",
)

dump = replace_once(
    dump,
    '''    firmware: str | None = None
    for pattern in _FIRMWARE_PATTERNS:
        match = pattern.search(document)
        if match:
            firmware = match.group(1)
            break
    hint = protocol_from_firmware(firmware)
''',
    '''    firmware = _extract_logger_firmware(document)
    hint = protocol_from_firmware(firmware)
''',
    "web identity firmware parser",
)
DUMP.write_text(dump, encoding="utf-8")


tests = TESTS.read_text(encoding="utf-8")
tests = replace_once(
    tests,
    'self.assertEqual(TOOL.TOOL_VERSION, "2.5.0")',
    'self.assertEqual(TOOL.TOOL_VERSION, "2.5.1")',
    "test tool version",
)

marker = '''    def test_logger_web_link_discovery_is_local_bounded_and_passive(self) -> None:
'''
regression = '''    def test_ms2000_web_metadata_ignores_help_placeholders_and_example_mac(self) -> None:
        help_document = (
            'Firmware version (main) '
            'Firmware version (slave) '
            'E.g. 00:01:02:AA:BB:CC'
        )
        help_metadata = TOOL._logger_web_metadata(help_document)
        self.assertIsNone(help_metadata["logger_firmware_version"])
        self.assertIsNone(help_metadata["logger_mac_oui"])

        status_document = (
            'var cover_ver="LSW5_SSL_02B0_1.05"; '
            'var cover_ap_mac="AA:BB:CC:11:22:33"; '
            'var cover_sta_mac="74:E9:D8:44:55:66"; '
            'var cover_sta_rssi="76%"; '
            'var webdata_sn="Y001234567890";'
        )
        status_metadata = TOOL._logger_web_metadata(status_document)
        self.assertEqual(status_metadata["logger_firmware_version"], "LSW5_SSL_02B0_1.05")
        self.assertEqual(status_metadata["logger_mac_oui"], "74:E9:D8")
        self.assertEqual(status_metadata["logger_wifi_signal"], 76)
        self.assertEqual(status_metadata["logger_wifi_signal_unit"], "%")
        self.assertEqual(status_metadata["inverter_serial_prefix"], "Y00")

        visible_firmware = TOOL._logger_web_metadata("Firmware version: V4.0.39")
        self.assertEqual(visible_firmware["logger_firmware_version"], "V4.0.39")

'''
tests = replace_once(tests, marker, regression + marker, "MS2000 regression test")
TESTS.write_text(tests, encoding="utf-8")


tools_readme = TOOLS_README.read_text(encoding="utf-8")
tools_readme = tools_readme.replace("2.5.0 dump engine", "2.5.1 dump engine")
TOOLS_README.write_text(tools_readme, encoding="utf-8")

hardware_doc = HARDWARE_DOC.read_text(encoding="utf-8")
hardware_doc = hardware_doc.replace("dump engine 2.5.0", "dump engine 2.5.1")
hardware_doc = hardware_doc.replace("The 2.5.0 dump engine therefore:", "The 2.5.1 dump engine therefore:")
needle = '''- records the page/key source used for the detected Wi-Fi signal;\n'''
addition = (
    needle
    + '- prioritizes real logger firmware/MAC fields and ignores generic help placeholders or example MAC addresses;\n'
)
hardware_doc = replace_once(hardware_doc, needle, addition, "hardware doc metadata bullet")
HARDWARE_DOC.write_text(hardware_doc, encoding="utf-8")

print("Applied TSUN dump web metadata 2.5.1 fix")
