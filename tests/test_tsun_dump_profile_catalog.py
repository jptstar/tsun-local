from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "tsun_dump_profile_catalog_test_module", ROOT / "tools" / "tsun_dump.py"
)
assert SPEC is not None and SPEC.loader is not None
DUMP = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = DUMP
SPEC.loader.exec_module(DUMP)


class LoggerProfileCatalogTests(unittest.TestCase):
    def test_extracts_selected_and_embedded_tengsheng_profiles(self) -> None:
        document = """
        <script>
        var inv_tp = \"5393:Tengsheng_titan\";
        var inv_tp_seld = \"5393\";
        var inv_set = \"5393,1,1\";
        var profile_list = [\"688:Tengsheng_G3\", \"4247:Tengsheng_G4\"];
        </script>
        """
        result = DUMP.extract_logger_profile_candidates(document)
        self.assertEqual(result["selected_id"], "5393")
        self.assertEqual(result["selected_profile"]["name"], "Tengsheng_titan")
        self.assertEqual(
            [(item["id"], item["name"]) for item in result["profiles"]],
            [("688", "Tengsheng_G3"), ("4247", "Tengsheng_G4"), ("5393", "Tengsheng_titan")],
        )

    def test_extracts_html_option_without_treating_bare_numbers_as_profiles(self) -> None:
        document = """
        <select id=\"inv_tp_seld\">
          <option value=\"4247\">Tengsheng_G4</option>
          <option value=\"9999\">OtherVendor</option>
        </select>
        <script>var unrelated = 688;</script>
        """
        result = DUMP.extract_logger_profile_candidates(document)
        self.assertEqual(result["profiles"], [
            {"id": "4247", "name": "Tengsheng_G4", "raw": "4247:Tengsheng_G4"}
        ])

    def test_cross_page_wifi_priority_and_static_script_profile_discovery(self) -> None:
        documents = {
            "/index_cn.html": "<html><script src=\"/profiles.js\"></script>Wi-Fi signal: 15%</html>",
            "/status.html": "var cover_sta_rssi = \"54%\";",
            "/hide_set_edit.html": "var inv_tp=\"5393:Tengsheng_titan\"; var inv_tp_seld=\"5393\";",
            "/profiles.js": "var all_profiles=[\"688:Tengsheng_G3\",\"4247:Tengsheng_G4\"];",
        }

        def fake_http(_host: str, path: str, _timeout: float, authenticated: bool):
            if authenticated:
                return None
            return documents.get(path)

        with patch.object(DUMP, "_http_document", side_effect=fake_http):
            result = DUMP.capture_logger_web_pages("192.0.2.10", 0.1)

        self.assertEqual(result["summary"]["logger_wifi_signal"], 54)
        self.assertEqual(result["summary"]["logger_wifi_signal_source"], "/status.html:cover_sta_rssi")
        self.assertIn("/profiles.js", result["paths_attempted"])
        catalog = result["logger_profile_catalog"]
        self.assertEqual(catalog["selected_id"], "5393")
        self.assertEqual(catalog["profile_count"], 3)
        self.assertEqual([item["id"] for item in catalog["discovered_profiles"]], ["688", "4247", "5393"])
        g3 = next(item for item in catalog["discovered_profiles"] if item["id"] == "688")
        self.assertEqual(g3["sources"], ["/profiles.js"])
        self.assertFalse(catalog["javascript_executed"])
        self.assertFalse(catalog["configuration_write_performed"])


if __name__ == "__main__":
    unittest.main()
