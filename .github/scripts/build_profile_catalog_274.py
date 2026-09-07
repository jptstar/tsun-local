from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parents[2]
path = ROOT / "tools" / "tsun_dump.py"
text = path.read_text(encoding="utf-8")

text = text.replace('TOOL_VERSION = "2.7.3"', 'TOOL_VERSION = "2.7.4"', 1)
text = text.replace("MAX_LOGGER_WEB_PATHS = 10", "MAX_LOGGER_WEB_PATHS = 24", 1)

anchor = '''_RAW_PROFILE_PATTERNS = (\n    re.compile(\n        r"\\binv_tp\\b\\s*[:=]\\s*[\\\"']\\s*([^\\\"']{1,127}?)\\s*[\\\"']",\n        re.IGNORECASE,\n    ),\n)\n'''
addition = anchor + '''\n_LOGGER_PROFILE_PAIR_PATTERN = re.compile(\n    r"(?P<id>\\d{1,6})\\s*:\\s*(?P<name>Tengsheng_[A-Za-z0-9._-]{1,96})",\n    re.IGNORECASE,\n)\n_LOGGER_PROFILE_OPTION_PATTERN = re.compile(\n    r"<option[^>]+value\\s*=\\s*[\\\"'](?P<id>\\d{1,6})[\\\"'][^>]*>"\n    r"[\\s\\S]{0,160}?(?P<name>Tengsheng_[A-Za-z0-9._-]{1,96})",\n    re.IGNORECASE,\n)\n_LOGGER_PROFILE_SELECTED_ID_PATTERNS = (\n    re.compile(\n        r"\\binv_tp_seld\\b\\s*[:=]\\s*[\\\"']?\\s*(\\d{1,6})",\n        re.IGNORECASE,\n    ),\n    re.compile(\n        r"\\binv_set\\b\\s*[:=]\\s*[\\\"']?\\s*(\\d{1,6})(?:\\s*[,;])",\n        re.IGNORECASE,\n    ),\n)\n'''
if anchor not in text:
    raise SystemExit("raw profile anchor not found")
text = text.replace(anchor, addition, 1)

sensitive_anchor = '''\n_SENSITIVE_FIELD_NAME = (\n'''
priority = '''\n_WIFI_SIGNAL_PRIORITY = {\n    source: index for index, (source, _pattern) in enumerate(_WIFI_SIGNAL_PATTERNS)\n}\n\n_SENSITIVE_FIELD_NAME = (\n'''
if sensitive_anchor not in text:
    raise SystemExit("wifi priority anchor not found")
text = text.replace(sensitive_anchor, priority, 1)

function_anchor = '''def _logger_web_metadata(document: str) -> dict[str, Any]:\n'''
profile_helpers = r'''def extract_logger_profile_candidates(document: str) -> dict[str, Any]:
    """Extract logger-internal Tengsheng profile IDs by static source inspection."""
    profiles: dict[tuple[str, str], dict[str, str]] = {}
    for pattern in (_LOGGER_PROFILE_PAIR_PATTERN, _LOGGER_PROFILE_OPTION_PATTERN):
        for match in pattern.finditer(document):
            profile_id = match.group("id").strip()
            name = match.group("name").strip()
            key = (profile_id, name.lower())
            profiles[key] = {
                "id": profile_id,
                "name": name,
                "raw": f"{profile_id}:{name}",
            }

    selected_id = _first_web_match(_LOGGER_PROFILE_SELECTED_ID_PATTERNS, document)
    raw_profile = _first_web_match(_RAW_PROFILE_PATTERNS, document)
    selected_profile: dict[str, str] | None = None
    if raw_profile:
        if match := _LOGGER_PROFILE_PAIR_PATTERN.search(raw_profile):
            selected_profile = {
                "id": match.group("id").strip(),
                "name": match.group("name").strip(),
                "raw": f"{match.group('id').strip()}:{match.group('name').strip()}",
            }
            selected_id = selected_id or selected_profile["id"]
            profiles[(selected_profile["id"], selected_profile["name"].lower())] = selected_profile

    return {
        "selected_id": selected_id,
        "selected_profile": selected_profile,
        "profiles": sorted(
            profiles.values(),
            key=lambda item: (int(item["id"]), item["name"].lower()),
        ),
        "evidence": {
            "inv_tp_seen": bool(re.search(r"\binv_tp\b", document, re.IGNORECASE)),
            "inv_tp_seld_seen": bool(re.search(r"\binv_tp_seld\b", document, re.IGNORECASE)),
            "inv_set_seen": bool(re.search(r"\binv_set\b", document, re.IGNORECASE)),
            "tengsheng_profile_seen": bool(_LOGGER_PROFILE_PAIR_PATTERN.search(document)),
        },
        "static_source_only": True,
        "javascript_executed": False,
    }


def _merge_logger_profile_catalog(
    catalog: dict[str, Any], document: str, source_path: str
) -> None:
    """Merge one HTML/JS source into the privacy-safe logger profile catalogue."""
    scan = extract_logger_profile_candidates(document)
    if catalog["selected_id"] is None and scan["selected_id"] is not None:
        catalog["selected_id"] = scan["selected_id"]
    if catalog["selected_profile"] is None and scan["selected_profile"] is not None:
        catalog["selected_profile"] = scan["selected_profile"]

    for key, value in scan["evidence"].items():
        catalog["evidence"][key] = bool(catalog["evidence"].get(key) or value)

    records = catalog["_records"]
    for profile in scan["profiles"]:
        record_key = f"{profile['id']}:{profile['name'].lower()}"
        if record_key not in records:
            records[record_key] = {**profile, "sources": []}
        if source_path not in records[record_key]["sources"]:
            records[record_key]["sources"].append(source_path)


def _finalize_logger_profile_catalog(catalog: dict[str, Any]) -> dict[str, Any]:
    """Return a stable JSON-ready catalogue with no internal aggregation fields."""
    profiles = sorted(
        catalog["_records"].values(),
        key=lambda item: (int(item["id"]), item["name"].lower()),
    )
    selected = catalog["selected_profile"]
    if selected is None and catalog["selected_id"] is not None:
        selected = next(
            (item for item in profiles if item["id"] == catalog["selected_id"]),
            None,
        )
    return {
        "selected_id": catalog["selected_id"],
        "selected_profile": selected,
        "discovered_profiles": profiles,
        "profile_count": len(profiles),
        "evidence": catalog["evidence"],
        "static_source_only": True,
        "javascript_executed": False,
        "form_submission_performed": False,
        "configuration_write_performed": False,
    }


'''
if function_anchor not in text:
    raise SystemExit("metadata function anchor not found")
text = text.replace(function_anchor, profile_helpers + function_anchor, 1)

summary_anchor = '''    summary: dict[str, Any] = {\n        "logger_firmware_version": None,\n        "logger_wifi_signal": None,\n        "logger_wifi_signal_unit": None,\n        "logger_wifi_signal_source": None,\n        "logger_raw_profile": None,\n        "logger_mac_oui": None,\n        "inverter_serial_prefix": None,\n    }\n\n    pending = list(dict.fromkeys(LOGGER_WEB_CAPTURE_PATHS))\n'''
summary_replacement = '''    summary: dict[str, Any] = {\n        "logger_firmware_version": None,\n        "logger_wifi_signal": None,\n        "logger_wifi_signal_unit": None,\n        "logger_wifi_signal_source": None,\n        "logger_raw_profile": None,\n        "logger_mac_oui": None,\n        "inverter_serial_prefix": None,\n    }\n    profile_catalog: dict[str, Any] = {\n        "selected_id": None,\n        "selected_profile": None,\n        "_records": {},\n        "evidence": {\n            "inv_tp_seen": False,\n            "inv_tp_seld_seen": False,\n            "inv_set_seen": False,\n            "tengsheng_profile_seen": False,\n        },\n    }\n\n    pending = list(dict.fromkeys(LOGGER_WEB_CAPTURE_PATHS))\n'''
if summary_anchor not in text:
    raise SystemExit("capture summary anchor not found")
text = text.replace(summary_anchor, summary_replacement, 1)

old_wifi = '''            if summary["logger_wifi_signal"] is None and metadata["logger_wifi_signal"] is not None:\n                summary["logger_wifi_signal"] = metadata["logger_wifi_signal"]\n                summary["logger_wifi_signal_unit"] = metadata["logger_wifi_signal_unit"]\n                source = metadata["logger_wifi_signal_source"] or "unknown"\n                summary["logger_wifi_signal_source"] = f"{path}:{source}"\n\n            interface = summarize_web_interface_read_only(document, path, host)\n'''
new_wifi = '''            if metadata["logger_wifi_signal"] is not None:\n                source = metadata["logger_wifi_signal_source"] or "unknown"\n                current = summary["logger_wifi_signal_source"]\n                current_source = (\n                    str(current).rsplit(":", 1)[-1] if current is not None else None\n                )\n                new_priority = _WIFI_SIGNAL_PRIORITY.get(source, 999)\n                current_priority = _WIFI_SIGNAL_PRIORITY.get(current_source, 999)\n                if summary["logger_wifi_signal"] is None or new_priority < current_priority:\n                    summary["logger_wifi_signal"] = metadata["logger_wifi_signal"]\n                    summary["logger_wifi_signal_unit"] = metadata["logger_wifi_signal_unit"]\n                    summary["logger_wifi_signal_source"] = f"{path}:{source}"\n\n            _merge_logger_profile_catalog(profile_catalog, document, path)\n\n            interface = summarize_web_interface_read_only(document, path, host)\n'''
if old_wifi not in text:
    raise SystemExit("wifi capture anchor not found")
text = text.replace(old_wifi, new_wifi, 1)

script_anchor = '''            if (\n                interface["forms"]\n                or interface["script_paths"]\n                or interface["javascript_handlers"]\n                or path in LOGGER_RESEARCH_PATHS\n            ):\n                interface_analysis.append(interface)\n\n            sanitized = anonymize_web_document(document)\n'''
script_replacement = '''            if (\n                interface["forms"]\n                or interface["script_paths"]\n                or interface["javascript_handlers"]\n                or path in LOGGER_RESEARCH_PATHS\n            ):\n                interface_analysis.append(interface)\n\n            # Static external scripts can carry the complete inverter profile table.\n            # Fetch only same-logger HTTP script paths discovered in already-read pages.\n            for script_path in interface["script_paths"]:\n                if script_path in queued or len(queued) >= MAX_LOGGER_WEB_PATHS:\n                    continue\n                queued.add(script_path)\n                pending.append(script_path)\n\n            sanitized = anonymize_web_document(document)\n'''
if script_anchor not in text:
    raise SystemExit("script queue anchor not found")
text = text.replace(script_anchor, script_replacement, 1)

return_anchor = '''        "summary": summary,\n        "interface_analysis": interface_analysis,\n        "pages": pages,\n'''
return_replacement = '''        "summary": summary,\n        "logger_profile_catalog": _finalize_logger_profile_catalog(profile_catalog),\n        "interface_analysis": interface_analysis,\n        "pages": pages,\n'''
if return_anchor not in text:
    raise SystemExit("logger web return anchor not found")
text = text.replace(return_anchor, return_replacement, 1)

privacy_anchor = '''            "same_logger_links_only": True,\n            "form_submission_performed": False,\n'''
privacy_replacement = '''            "same_logger_links_only": True,\n            "profile_catalog_names_and_ids_only": True,\n            "external_scripts_get_only": True,\n            "form_submission_performed": False,\n'''
if privacy_anchor not in text:
    raise SystemExit("privacy anchor not found")
text = text.replace(privacy_anchor, privacy_replacement, 1)

path.write_text(text, encoding="utf-8")

test_path = ROOT / "tests" / "test_tsun_dump_profile_catalog.py"
test_path.write_text('''from __future__ import annotations\n\nimport importlib.util\nfrom pathlib import Path\nimport sys\nimport unittest\nfrom unittest.mock import patch\n\nROOT = Path(__file__).parents[1]\nSPEC = importlib.util.spec_from_file_location(\n    "tsun_dump_profile_catalog_test_module", ROOT / "tools" / "tsun_dump.py"\n)\nassert SPEC is not None and SPEC.loader is not None\nDUMP = importlib.util.module_from_spec(SPEC)\nsys.modules[SPEC.name] = DUMP\nSPEC.loader.exec_module(DUMP)\n\n\nclass LoggerProfileCatalogTests(unittest.TestCase):\n    def test_extracts_selected_and_embedded_tengsheng_profiles(self) -> None:\n        document = """\n        <script>\n        var inv_tp = \\\"5393:Tengsheng_titan\\\";\n        var inv_tp_seld = \\\"5393\\\";\n        var inv_set = \\\"5393,1,1\\\";\n        var profile_list = [\\\"688:Tengsheng_G3\\\", \\\"4247:Tengsheng_G4\\\"];\n        </script>\n        """\n        result = DUMP.extract_logger_profile_candidates(document)\n        self.assertEqual(result["selected_id"], "5393")\n        self.assertEqual(result["selected_profile"]["name"], "Tengsheng_titan")\n        self.assertEqual(\n            [(item["id"], item["name"]) for item in result["profiles"]],\n            [("688", "Tengsheng_G3"), ("4247", "Tengsheng_G4"), ("5393", "Tengsheng_titan")],\n        )\n\n    def test_extracts_html_option_without_treating_bare_numbers_as_profiles(self) -> None:\n        document = """\n        <select id=\\\"inv_tp_seld\\\">\n          <option value=\\\"4247\\\">Tengsheng_G4</option>\n          <option value=\\\"9999\\\">OtherVendor</option>\n        </select>\n        <script>var unrelated = 688;</script>\n        """\n        result = DUMP.extract_logger_profile_candidates(document)\n        self.assertEqual(result["profiles"], [\n            {"id": "4247", "name": "Tengsheng_G4", "raw": "4247:Tengsheng_G4"}\n        ])\n\n    def test_cross_page_wifi_priority_and_static_script_profile_discovery(self) -> None:\n        documents = {\n            "/index_cn.html": "<html><script src=\\\"/profiles.js\\\"></script>Wi-Fi signal: 15%</html>",\n            "/status.html": "var cover_sta_rssi = \\\"54%\\\";",\n            "/hide_set_edit.html": "var inv_tp=\\\"5393:Tengsheng_titan\\\"; var inv_tp_seld=\\\"5393\\\";",\n            "/profiles.js": "var all_profiles=[\\\"688:Tengsheng_G3\\\",\\\"4247:Tengsheng_G4\\\"];",\n        }\n\n        def fake_http(_host: str, path: str, _timeout: float, authenticated: bool):\n            if authenticated:\n                return None\n            return documents.get(path)\n\n        with patch.object(DUMP, "_http_document", side_effect=fake_http):\n            result = DUMP.capture_logger_web_pages("192.0.2.10", 0.1)\n\n        self.assertEqual(result["summary"]["logger_wifi_signal"], 54)\n        self.assertEqual(result["summary"]["logger_wifi_signal_source"], "/status.html:cover_sta_rssi")\n        self.assertIn("/profiles.js", result["paths_attempted"])\n        catalog = result["logger_profile_catalog"]\n        self.assertEqual(catalog["selected_id"], "5393")\n        self.assertEqual(catalog["profile_count"], 3)\n        self.assertEqual([item["id"] for item in catalog["discovered_profiles"]], ["688", "4247", "5393"])\n        g3 = next(item for item in catalog["discovered_profiles"] if item["id"] == "688")\n        self.assertEqual(g3["sources"], ["/profiles.js"])\n        self.assertFalse(catalog["javascript_executed"])\n        self.assertFalse(catalog["configuration_write_performed"])\n\n\nif __name__ == "__main__":\n    unittest.main()\n''', encoding="utf-8")
