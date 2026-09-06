from __future__ import annotations

from pathlib import Path


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one match, found {count}: {old[:80]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


root = Path(__file__).parents[1]
tool = root / "tools" / "tsun_dump.py"
tests = root / "tests" / "test_tsun_dump_tool.py"
tools_readme = root / "tools" / "README.md"
hardware_doc = root / "docs" / "HARDWARE_DUMP.md"
readme = root / "README.md"
test_page = root / "docs" / "test-your-inverter.html"

replace_once(tool, 'TOOL_VERSION = "2.7.0"', 'TOOL_VERSION = "2.7.1"')

replace_once(
    tool,
    '''DISCOVERY_MESSAGES = (\n    b"WIFIKIT-214028-READ",\n    b"HF-A11ASSISTHREAD",\n    b"devicelinkfind",\n)\nLOGGER_STATUS_PATHS''',
    '''DISCOVERY_MESSAGES = (\n    b"WIFIKIT-214028-READ",\n    b"HF-A11ASSISTHREAD",\n    b"devicelinkfind",\n)\nLOGGER_AT_DISCOVERY_MESSAGES = (\n    b"WIFIKIT-214028-READ",\n    b"HF-A11ASSISTHREAD",\n)\nLOGGER_DNS_QUERY = b"AT+WSDNS\\n"\nLOGGER_AT_QUIT = b"AT+Q\\n"\nLOGGER_AT_MAX_RESPONSE = 2048\nLOGGER_STATUS_PATHS''',
)

replace_once(
    tool,
    '''def discover_udp_targets(\n    targets: Iterable[str],\n''',
    '''def _dns_address_scope(address: IPv4Address) -> str:\n    """Return a privacy-safe classification for one DNS server address."""\n    if address.is_unspecified:\n        return "unset"\n    if address.is_loopback:\n        return "loopback"\n    if address.is_link_local:\n        return "link_local"\n    if address.is_multicast:\n        return "multicast"\n    if address.is_private:\n        return "private"\n    if address.is_reserved:\n        return "reserved"\n    return "public"\n\n\ndef summarize_logger_dns_response(response: bytes) -> dict[str, Any]:\n    """Summarize AT+WSDNS without retaining the DNS server address."""\n    text = response.decode("utf-8", errors="replace").strip("\\x00\\r\\n ")\n    if not text.lower().startswith("+ok"):\n        return {\n            "supported": False,\n            "response_status": "not_ok",\n            "response_has_value": bool(text),\n            "dns_server_present": False,\n            "address_count": 0,\n            "address_scopes": [],\n        }\n\n    value = text.split("=", 1)[1].strip() if "=" in text else ""\n    addresses: list[IPv4Address] = []\n    for match in _IPV4_TOKEN.finditer(value):\n        try:\n            addresses.append(IPv4Address(match.group(0)))\n        except ValueError:\n            continue\n    scopes = sorted({_dns_address_scope(address) for address in addresses})\n    return {\n        "supported": True,\n        "response_status": "ok",\n        "response_has_value": bool(value),\n        "dns_server_present": any(not address.is_unspecified for address in addresses),\n        "address_count": len(addresses),\n        "address_scopes": scopes,\n    }\n\n\ndef probe_logger_dns_read_only(host: str, timeout: float) -> dict[str, Any]:\n    """Query AT+WSDNS over UDP 48899 without changing logger configuration."""\n    base: dict[str, Any] = {\n        "attempted": True,\n        "read_only": True,\n        "transport": "udp48899",\n        "command": "AT+WSDNS",\n        "configuration_write_performed": False,\n        "dns_server_address_stored": False,\n    }\n    last_error: dict[str, str] | None = None\n    last_summary: dict[str, Any] | None = None\n\n    for handshake in LOGGER_AT_DISCOVERY_MESSAGES:\n        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)\n        session_open = False\n        try:\n            sock.settimeout(timeout)\n            sock.connect((host, DEFAULT_DISCOVERY_PORT))\n            sock.send(handshake)\n            handshake_response = sock.recv(LOGGER_AT_MAX_RESPONSE)\n            if not handshake_response:\n                continue\n\n            # This acknowledgement enters the logger's existing AT assistant\n            # session. The only actual query below is AT+WSDNS without '='.\n            sock.send(b"+ok")\n            session_open = True\n            time.sleep(0.05)\n            sock.send(LOGGER_DNS_QUERY)\n            response = sock.recv(LOGGER_AT_MAX_RESPONSE)\n            summary = summarize_logger_dns_response(response)\n            last_summary = summary\n            if summary["supported"]:\n                return {\n                    **base,\n                    **summary,\n                    "result": "supported",\n                    "assistant_handshake": handshake.decode("ascii"),\n                }\n        except socket.timeout:\n            last_error = {"type": "TimeoutError", "detail": "timeout waiting for AT response"}\n        except OSError as err:\n            last_error = safe_error_details(err)\n        finally:\n            if session_open:\n                try:\n                    sock.send(LOGGER_AT_QUIT)\n                except OSError:\n                    pass\n            sock.close()\n\n    result = {\n        **base,\n        "supported": False,\n        "result": "no_supported_response",\n    }\n    if last_summary is not None:\n        result.update(last_summary)\n    if last_error is not None:\n        result["error"] = last_error\n    return result\n\n\ndef discover_udp_targets(\n    targets: Iterable[str],\n''',
)

replace_once(
    tool,
    '''    logger_web = capture_logger_web_pages(host, args.http_page_timeout)\n    protocol_characterization = (\n''',
    '''    logger_web = capture_logger_web_pages(host, args.http_page_timeout)\n    logger_dns_probe = (\n        probe_logger_dns_read_only(host, min(args.timeout, 2.5))\n        if args.full\n        else {\n            "attempted": False,\n            "read_only": True,\n            "reason": "requires a full capture",\n            "dns_server_address_stored": False,\n        }\n    )\n    protocol_characterization = (\n''',
)

replace_once(
    tool,
    '''                "logger_web_anonymized_html_in_output": True,\n                "inverter_serial_prefix_characters": 3,\n''',
    '''                "logger_web_anonymized_html_in_output": True,\n                "logger_dns_address_in_output": False,\n                "inverter_serial_prefix_characters": 3,\n''',
)

replace_once(
    tool,
    '''        "logger_web": logger_web,\n        "protocol_characterization": protocol_characterization,\n''',
    '''        "logger_web": logger_web,\n        "logger_dns_probe": logger_dns_probe,\n        "protocol_characterization": protocol_characterization,\n''',
)

replace_once(
    tool,
    '''    print(f"Snapshots: {summary['snapshots']}")\n    print("Writes   : 0")\n''',
    '''    print(f"Snapshots: {summary['snapshots']}")\n    dns_probe = document.get("logger_dns_probe", {})\n    if dns_probe.get("attempted"):\n        if dns_probe.get("supported"):\n            print("DNS read : AT+WSDNS supported (address kept private)")\n        else:\n            print("DNS read : AT+WSDNS not confirmed")\n    print("Writes   : 0")\n''',
)

replace_once(
    tests,
    'self.assertEqual(TOOL.TOOL_VERSION, "2.7.0")',
    'self.assertEqual(TOOL.TOOL_VERSION, "2.7.1")',
)

replace_once(
    tests,
    '''    def test_capture_plans_stay_read_only(self) -> None:\n''',
    '''    def test_dns_probe_command_is_get_only(self) -> None:\n        self.assertEqual(TOOL.LOGGER_DNS_QUERY, b"AT+WSDNS\\n")\n        self.assertNotIn(b"=", TOOL.LOGGER_DNS_QUERY)\n\n    def test_dns_probe_response_is_privacy_safe(self) -> None:\n        summary = TOOL.summarize_logger_dns_response(\n            b"+ok=192.168.1.1,8.8.8.8\\r\\n"\n        )\n        self.assertTrue(summary["supported"])\n        self.assertTrue(summary["dns_server_present"])\n        self.assertEqual(summary["address_count"], 2)\n        self.assertEqual(summary["address_scopes"], ["private", "public"])\n        rendered = repr(summary)\n        self.assertNotIn("192.168.1.1", rendered)\n        self.assertNotIn("8.8.8.8", rendered)\n\n    def test_dns_probe_rejects_non_ok_response(self) -> None:\n        summary = TOOL.summarize_logger_dns_response(b"+ERR=-1\\r\\n")\n        self.assertFalse(summary["supported"])\n        self.assertFalse(summary["dns_server_present"])\n\n    def test_capture_plans_stay_read_only(self) -> None:\n''',
)

replace_once(
    tools_readme,
    "the current GUI is 1.4.0 and uses the 2.7.0 dump engine.",
    "the current GUI is 1.4.0 and uses the 2.7.1 dump engine.",
)
replace_once(
    tools_readme,
    '''Starting with dump engine 2.7.0, the standalone Python file checks the same `diagnostic-latest` manifest on startup, downloads a newer `tsun_dump.py` when available, verifies SHA-256, atomically replaces the current script and restarts. `--no-update` disables the check for one run and `--check-update` only reports availability. If the script location is not writable, the diagnostic continues with the local version and never requests `sudo`.\n''',
    '''Starting with dump engine 2.7.0, the standalone Python file checks the same `diagnostic-latest` manifest on startup, downloads a newer `tsun_dump.py` when available, verifies SHA-256, atomically replaces the current script and restarts. `--no-update` disables the check for one run and `--check-update` only reports availability. If the script location is not writable, the diagnostic continues with the local version and never requests `sudo`.\n\nDump engine **2.7.1** adds a full-mode, read-only `AT+WSDNS` capability probe over the logger's local UDP 48899 assistant interface. It sends only the getter form (no `=` and no configuration value), records whether the command is supported, and deliberately excludes the actual DNS server address from the shareable JSON. This is intended to verify whether a logger such as a TITAN / MP3000 exposes a configurable DNS setting before any Cloud Protection design is attempted.\n''',
)

replace_once(
    hardware_doc,
    "Current standalone diagnostic versions: **dump engine 2.7.0** · **Windows GUI 1.4.0**.",
    "Current standalone diagnostic versions: **dump engine 2.7.1** · **Windows GUI 1.4.0**.",
)
replace_once(
    hardware_doc,
    '''This web-page capture is diagnostic evidence only. It does not turn the Home Assistant integration into a web crawler and does not add any write path.\n\n### Python script — macOS, Linux and advanced users\n''',
    '''This web-page capture is diagnostic evidence only. It does not turn the Home Assistant integration into a web crawler and does not add any write path.\n\n### Read-only logger DNS capability probe\n\nDump engine **2.7.1** adds one deliberately narrow full-mode capability test for the logger DNS setting. Over the local UDP 48899 assistant interface it opens the normal diagnostic session and sends only `AT+WSDNS` **without an equals sign or value**. On logger families that implement the command, this is the documented getter form; the tool never sends `AT+WSDNS=<address>` and therefore never changes DNS configuration.\n\nThe JSON records whether the query was supported and only privacy-safe properties such as the number/scope of returned IPv4 addresses. The actual DNS server address is **not stored**. This probe is research evidence for a possible future TSUN Local Cloud/Firmware Protection feature; it is not itself a blocker and it does not modify the logger.\n\n### Python script — macOS, Linux and advanced users\n''',
)

replace_once(
    readme,
    "**Current public diagnostic versions:** Windows GUI **1.4.0** · dump engine **2.7.0**.",
    "**Current public diagnostic versions:** Windows GUI **1.4.0** · dump engine **2.7.1**.",
)
replace_once(
    readme,
    "`tsun_dump.py` **2.7.0** uses the same `diagnostic-latest` update channel.",
    "`tsun_dump.py` **2.7.1** uses the same `diagnostic-latest` update channel.",
)
replace_once(
    readme,
    '''The dump engine is firmware-resilient: it recognizes several Wi-Fi signal layouts (`%` and `dBm`) and can capture a bounded set of passive, same-logger web pages as **anonymized HTML evidence**. It never submits forms, follows external links or calls reboot/reset/update pages.\n''',
    '''The dump engine is firmware-resilient: it recognizes several Wi-Fi signal layouts (`%` and `dBm`) and can capture a bounded set of passive, same-logger web pages as **anonymized HTML evidence**. In full mode, 2.7.1 also performs a read-only `AT+WSDNS` capability query so we can verify whether a logger exposes its DNS setting without changing it; the returned DNS address is not stored. It never submits forms, follows external links or calls reboot/reset/update pages.\n''',
)

replace_once(
    test_page,
    "<strong>tsun_dump.py 2.7.0</strong>",
    "<strong>tsun_dump.py 2.7.1</strong>",
)
replace_once(
    test_page,
    '''The read-only engine discovers local TSUN loggers, identifies 1511 / 02B0 / 1097 protocol families, captures known-safe register ranges and gathers bounded passive logger metadata. It can recognize multiple Wi-Fi RSSI layouts in percent or dBm.''',
    '''The read-only engine discovers local TSUN loggers, identifies 1511 / 02B0 / 1097 protocol families, captures known-safe register ranges and gathers bounded passive logger metadata. It can recognize multiple Wi-Fi RSSI layouts in percent or dBm and, in full mode, test whether the logger answers the read-only `AT+WSDNS` DNS query without storing the returned DNS address.''',
)

print("Applied TSUN Local diagnostic 2.7.1 read-only DNS capability probe patch.")
