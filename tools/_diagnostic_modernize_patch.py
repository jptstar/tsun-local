from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(f"Expected exactly one {label}, found {text.count(old)}")
    return text.replace(old, new, 1)


def replace_section(text: str, start: str, end: str, new: str, label: str) -> str:
    start_index = text.find(start)
    if start_index < 0:
        raise RuntimeError(f"Missing start marker for {label}")
    end_index = text.find(end, start_index)
    if end_index < 0:
        raise RuntimeError(f"Missing end marker for {label}")
    return text[:start_index] + new.rstrip() + "\n\n" + text[end_index:]


root = Path(__file__).parents[1]
dump_path = root / "tools" / "tsun_dump.py"
gui_path = root / "tools" / "tsun_diagnostic_gui.py"
test_path = root / "tests" / "test_tsun_dump_tool.py"

# ---------------------------------------------------------------------------
# tsun_dump.py: firmware-resilient local web evidence and Wi-Fi parsing
# ---------------------------------------------------------------------------
dump = dump_path.read_text(encoding="utf-8")
dump = replace_once(dump, 'TOOL_VERSION = "2.4.1"', 'TOOL_VERSION = "2.5.0"', "tool version")
dump = replace_once(
    dump,
    "import http.client\n",
    "import http.client\nfrom html.parser import HTMLParser\n",
    "HTML parser import",
)
dump = replace_once(
    dump,
    "from typing import Any, Callable, Iterable\n",
    "from typing import Any, Callable, Iterable\nfrom urllib.parse import urljoin, urlsplit\n",
    "URL parser imports",
)
dump = replace_once(
    dump,
    "MAX_HTTP_PAGE_SIZE = 512 * 1024\nMIN_SCAN_PREFIX = 24\n",
    "MAX_HTTP_PAGE_SIZE = 512 * 1024\nMAX_LOGGER_WEB_PATHS = 10\nMIN_SCAN_PREFIX = 24\n",
    "web path limit",
)
dump = replace_once(
    dump,
    'LOGGER_WEB_AUTH = base64.b64encode(b"admin:admin").decode("ascii")\n',
    'LOGGER_WEB_AUTH = base64.b64encode(b"admin:admin").decode("ascii")\n'
    '_ALLOWED_WEB_SUFFIXES = (".htm", ".html", ".shtml", ".xhtml", ".cgi", ".asp")\n'
    '_WEB_ACTION_TOKENS = (\n'
    '    "reboot", "restart", "reset", "factory", "restore", "upgrade",\n'
    '    "update", "flash", "upload", "delete", "format", "erase",\n'
    ')\n',
    "web discovery safety constants",
)

dump = replace_section(
    dump,
    "_WIFI_SIGNAL_PATTERNS = (\n",
    "_SENSITIVE_FIELD_NAME = (\n",
    '''_WIFI_SIGNAL_PATTERNS = (
    (
        "cover_sta_rssi",
        re.compile(
            r"\\bcover_sta_rssi\\b\\s*[:=]\\s*[\\\"']?\\s*"
            r"(?P<value>-?\\d{1,3})\\s*(?P<unit>dBm|%)?",
            re.IGNORECASE,
        ),
    ),
    (
        "sta_rssi",
        re.compile(
            r"\\bsta[_-]rssi\\b\\s*[:=]\\s*[\\\"']?\\s*"
            r"(?P<value>-?\\d{1,3})\\s*(?P<unit>dBm|%)?",
            re.IGNORECASE,
        ),
    ),
    (
        "wifi_rssi",
        re.compile(
            r"\\b(?:wifi|wlan)[_-]rssi\\b\\s*[:=]\\s*[\\\"']?\\s*"
            r"(?P<value>-?\\d{1,3})\\s*(?P<unit>dBm|%)?",
            re.IGNORECASE,
        ),
    ),
    (
        "wifi_signal",
        re.compile(
            r"\\b(?:cover[_-]sta[_-]signal|wifi[_-]signal|wlan[_-]signal|signal[_-]strength)\\b"
            r"\\s*[:=]\\s*[\\\"']?\\s*(?P<value>-?\\d{1,3})\\s*(?P<unit>dBm|%)?",
            re.IGNORECASE,
        ),
    ),
    (
        "visible_wifi_label",
        re.compile(
            r"(?:wi[\\s_-]?fi|wlan)[\\s\\S]{0,40}?"
            r"(?:signal(?:\\s*strength)?|rssi)[^\\d-]{0,20}"
            r"(?P<value>-?\\d{1,3})\\s*(?P<unit>dBm|%)?",
            re.IGNORECASE,
        ),
    ),
)''',
    "Wi-Fi parser patterns",
)

dump = replace_section(
    dump,
    "def _logger_web_metadata(document: str) -> dict[str, Any]:\n",
    "def anonymize_web_document(document: str) -> str:\n",
    '''class _LocalLinkParser(HTMLParser):
    """Collect navigation targets from local logger HTML without executing anything."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.targets: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attribute = "href" if tag == "a" else "src" if tag in ("frame", "iframe") else None
        if attribute is None:
            return
        for name, value in attrs:
            if name.lower() == attribute and value:
                self.targets.append(value)
                break


def _safe_local_web_path(value: str, current_path: str, host: str) -> str | None:
    """Return a same-logger, GET-only page path suitable for bounded evidence capture."""
    value = value.strip()
    if not value or value.startswith("#"):
        return None
    try:
        target = urlsplit(urljoin(f"http://{host}{current_path}", value))
        port = target.port
    except ValueError:
        return None
    if target.scheme.lower() != "http" or target.hostname != host or port not in (None, 80):
        return None
    path = target.path or "/"
    if not path.startswith("/") or len(path) > 192:
        return None
    lowered = path.lower()
    if any(token in lowered for token in _WEB_ACTION_TOKENS):
        return None
    leaf = lowered.rsplit("/", 1)[-1]
    if "." in leaf and not any(leaf.endswith(suffix) for suffix in _ALLOWED_WEB_SUFFIXES):
        return None
    return path


def _discover_local_web_paths(document: str, current_path: str, host: str) -> list[str]:
    """Discover passive same-device HTML navigation links from one logger page."""
    parser = _LocalLinkParser()
    try:
        parser.feed(document)
        parser.close()
    except (ValueError, TypeError):
        return []
    result: list[str] = []
    for target in parser.targets:
        path = _safe_local_web_path(target, current_path, host)
        if path is not None and path not in result:
            result.append(path)
    return result


def _parse_wifi_signal_metadata(document: str) -> tuple[int | None, str | None, str | None]:
    """Extract Wi-Fi signal across known firmware layouts, preserving its unit and source."""
    for source, pattern in _WIFI_SIGNAL_PATTERNS:
        if match := pattern.search(document):
            candidate = int(match.group("value"))
            raw_unit = (match.groupdict().get("unit") or "").lower()
            if raw_unit == "dbm":
                if -120 <= candidate <= 0:
                    return candidate, "dBm", source
                continue
            if raw_unit == "%":
                if 0 <= candidate <= 100:
                    return candidate, "%", source
                continue
            if candidate < 0:
                if -120 <= candidate <= 0:
                    return candidate, "dBm", source
            elif candidate <= 100:
                return candidate, "%", source
    return None, None, None


def _logger_web_metadata(document: str) -> dict[str, Any]:
    """Extract non-identifying logger metadata plus a 3-character inverter prefix."""
    firmware: str | None = None
    for pattern in _FIRMWARE_PATTERNS:
        if match := pattern.search(document):
            firmware = match.group(1)
            break

    inverter_serial = _first_web_match(_INVERTER_SERIAL_PATTERNS, document)
    raw_profile = _first_web_match(_RAW_PROFILE_PATTERNS, document)
    wifi_signal, wifi_unit, wifi_source = _parse_wifi_signal_metadata(document)

    mac_match = _MAC_TOKEN.search(document)
    mac_oui = None
    if mac_match:
        mac_oui = ":".join(part.upper() for part in mac_match.groups()[:3])

    return {
        "logger_firmware_version": firmware,
        "logger_wifi_signal": wifi_signal,
        "logger_wifi_signal_unit": wifi_unit,
        "logger_wifi_signal_source": wifi_source,
        "logger_raw_profile": raw_profile,
        "logger_mac_oui": mac_oui,
        "inverter_serial_prefix": (inverter_serial[:3] if inverter_serial else None),
    }''',
    "logger web metadata helpers",
)

dump = replace_section(
    dump,
    "def capture_logger_web_pages(host: str, timeout: float) -> dict[str, Any]:\n",
    "def _web_identity_from_document(\n",
    '''def capture_logger_web_pages(host: str, timeout: float) -> dict[str, Any]:
    """Capture bounded anonymized logger pages, including safe local links."""
    pages: list[dict[str, Any]] = []
    summary: dict[str, Any] = {
        "logger_firmware_version": None,
        "logger_wifi_signal": None,
        "logger_wifi_signal_unit": None,
        "logger_wifi_signal_source": None,
        "logger_raw_profile": None,
        "logger_mac_oui": None,
        "inverter_serial_prefix": None,
    }

    pending = list(dict.fromkeys(LOGGER_WEB_CAPTURE_PATHS))
    queued = set(pending)
    attempted_paths: list[str] = []

    while pending and len(attempted_paths) < MAX_LOGGER_WEB_PATHS:
        path = pending.pop(0)
        attempted_paths.append(path)
        seen_hashes: set[str] = set()

        for authenticated in (False, True):
            document = _http_document(host, path, timeout, authenticated)
            if document is None:
                continue

            metadata = _logger_web_metadata(document)
            for key in (
                "logger_firmware_version",
                "logger_raw_profile",
                "logger_mac_oui",
                "inverter_serial_prefix",
            ):
                value = metadata[key]
                if summary[key] is None and value is not None:
                    summary[key] = value

            if summary["logger_wifi_signal"] is None and metadata["logger_wifi_signal"] is not None:
                summary["logger_wifi_signal"] = metadata["logger_wifi_signal"]
                summary["logger_wifi_signal_unit"] = metadata["logger_wifi_signal_unit"]
                source = metadata["logger_wifi_signal_source"] or "unknown"
                summary["logger_wifi_signal_source"] = f"{path}:{source}"

            sanitized = anonymize_web_document(document)
            digest = hashlib.sha256(sanitized.encode("utf-8")).hexdigest()
            if digest not in seen_hashes:
                seen_hashes.add(digest)
                pages.append(
                    {
                        "path": path,
                        "authenticated": authenticated,
                        "content_sha256": digest,
                        "content": sanitized,
                    }
                )

            for discovered in _discover_local_web_paths(document, path, host):
                if discovered in queued or len(queued) >= MAX_LOGGER_WEB_PATHS:
                    continue
                queued.add(discovered)
                pending.append(discovered)

    known = set(LOGGER_WEB_CAPTURE_PATHS)
    return {
        "attempted": True,
        "pages_found": len(pages),
        "page_paths_found": sorted({page["path"] for page in pages}),
        "paths_attempted": attempted_paths,
        "discovered_paths": [path for path in attempted_paths if path not in known],
        "summary": summary,
        "pages": pages,
        "privacy": {
            "raw_html_stored": False,
            "anonymized_html_stored": True,
            "logger_sn_stored": False,
            "host_ip_stored": False,
            "full_inverter_serial_stored": False,
            "inverter_serial_prefix_characters": 3,
            "full_mac_stored": False,
            "mac_oui_stored": True,
            "wifi_credentials_stored": False,
            "same_logger_links_only": True,
            "form_submission_performed": False,
            "max_page_paths": MAX_LOGGER_WEB_PATHS,
        },
    }''',
    "bounded logger web capture",
)

dump_path.write_text(dump, encoding="utf-8")

# ---------------------------------------------------------------------------
# Windows GUI: clearer 1 → 2 → 3 flow and safer details expansion
# ---------------------------------------------------------------------------
gui = gui_path.read_text(encoding="utf-8")
gui = replace_once(gui, 'APP_VERSION = "1.1.0"', 'APP_VERSION = "1.2.0"', "GUI version")
gui = replace_once(gui, '"step_title": "Avant de commencer",', '"step_title": "1 · Désactivez TSUN Local",', "French step title")
gui = replace_once(gui, '"run": "Lancer le diagnostic",', '"run": "2 · Lancer le diagnostic",', "French run label")
gui = replace_once(gui, '"output_title": "Rapport",', '"output_title": "3 · Rapport à envoyer",', "French report title")
gui = replace_once(gui, '"auto_title": "Détection automatique",', '"auto_title": "Tout est automatique",', "French auto title")
gui = replace_once(gui, '"step_title": "Before you start",', '"step_title": "1 · Disable TSUN Local",', "English step title")
gui = replace_once(gui, '"run": "Run diagnostic",', '"run": "2 · Run diagnostic",', "English run label")
gui = replace_once(gui, '"output_title": "Report",', '"output_title": "3 · Report to send",', "English report title")
gui = replace_once(gui, '"auto_title": "Automatic discovery",', '"auto_title": "Automatic by default",', "English auto title")
gui = replace_section(
    gui,
    "    def _toggle_details(self) -> None:\n",
    "    def _copy_email(self) -> None:\n",
    '''    def _toggle_details(self) -> None:
        self.details_visible = not self.details_visible
        if self.details_visible:
            self.log_card.pack(fill="both", expand=True, pady=(0, 14), after=self.details_button)
            self.details_button.configure(text=self.t["details_hide"])
        else:
            self.log_card.pack_forget()
            self.details_button.configure(text=self.t["details_show"])''',
    "details toggle",
)
gui_path.write_text(gui, encoding="utf-8")

# ---------------------------------------------------------------------------
# Tests: lock in firmware variants, unit semantics and safe local discovery
# ---------------------------------------------------------------------------
tests = test_path.read_text(encoding="utf-8")
tests = replace_once(tests, 'self.assertEqual(TOOL.TOOL_VERSION, "2.4.1")', 'self.assertEqual(TOOL.TOOL_VERSION, "2.5.0")', "test tool version")
tests = replace_once(
    tests,
    '        self.assertEqual(metadata["logger_wifi_signal"], -70)\n',
    '        self.assertEqual(metadata["logger_wifi_signal"], -70)\n'
    '        self.assertEqual(metadata["logger_wifi_signal_unit"], "dBm")\n'
    '        self.assertEqual(metadata["logger_wifi_signal_source"], "cover_sta_rssi")\n',
    "Wi-Fi metadata assertions",
)
tests = replace_once(
    tests,
    "    def test_capture_plans_stay_read_only(self) -> None:\n",
    '''    def test_wifi_signal_variants_keep_unit_and_source(self) -> None:
        percent = TOOL._logger_web_metadata('var wifi_signal="72%";')
        self.assertEqual(percent["logger_wifi_signal"], 72)
        self.assertEqual(percent["logger_wifi_signal_unit"], "%")
        self.assertEqual(percent["logger_wifi_signal_source"], "wifi_signal")

        dbm = TOOL._logger_web_metadata('<div>WiFi Signal: -67 dBm</div>')
        self.assertEqual(dbm["logger_wifi_signal"], -67)
        self.assertEqual(dbm["logger_wifi_signal_unit"], "dBm")
        self.assertEqual(dbm["logger_wifi_signal_source"], "visible_wifi_label")

    def test_logger_web_link_discovery_is_local_bounded_and_passive(self) -> None:
        document = (
            '<a href="/wifi_status.html">WiFi</a>'
            '<a href="device.html">Device</a>'
            '<iframe src="/info.cgi"></iframe>'
            '<a href="/reboot.cgi">Reboot</a>'
            '<a href="https://example.com/status.html">External</a>'
            '<a href="javascript:reset()">JS</a>'
            '<a href="/image.png">Image</a>'
        )
        paths = TOOL._discover_local_web_paths(
            document, "/index.html", "192.168.1.25"
        )
        self.assertEqual(paths, ["/wifi_status.html", "/device.html", "/info.cgi"])
        self.assertEqual(TOOL.MAX_LOGGER_WEB_PATHS, 10)

    def test_capture_plans_stay_read_only(self) -> None:
''',
    "new firmware-resilience tests",
)
test_path.write_text(tests, encoding="utf-8")
