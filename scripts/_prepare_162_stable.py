from __future__ import annotations

from pathlib import Path
import json

ROOT = Path(__file__).parents[1]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit(f"Expected exactly one match in {path}: {old[:80]!r}; got {text.count(old)}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


sensor = ROOT / "custom_components/tsun_local/sensor.py"
replace_once(
    sensor,
    "from homeassistant.core import HomeAssistant, callback\n",
    "from homeassistant.core import HomeAssistant, callback\nfrom homeassistant.exceptions import HomeAssistantError\n",
)
replace_once(
    sensor,
    "from homeassistant.util import dt as dt_util\n",
    "from homeassistant.util import dt as dt_util\nfrom homeassistant.util.unit_conversion import EnergyConverter\n",
)
replace_once(
    sensor,
    "from .daily_energy import DailyEnergyTracker, energy_value\n",
    "from .daily_energy import (\n    DailyEnergyTracker,\n    energy_value,\n    repair_legacy_daily_state,\n)\n",
)
replace_once(
    sensor,
    "\n\n@dataclass(frozen=True, kw_only=True)\nclass TsunSensorDescription",
    '''\n\ndef _restored_energy_kwh(state: Any) -> float | None:\n    \"\"\"Return a restored Home Assistant energy state normalized to native kWh.\n\n    Home Assistant stores the entity state in the user-selected display unit.\n    TSUN Local decoders and the daily tracker use kWh internally, so restoring\n    the numeric state without its unit can introduce a x1000 Wh/kWh error.\n    \"\"\"\n    value = energy_value(state.state)\n    if value is None:\n        return None\n    unit = state.attributes.get(\"unit_of_measurement\")\n    if unit in (None, UnitOfEnergy.KILO_WATT_HOUR):\n        return value\n    try:\n        return float(\n            EnergyConverter.convert(\n                value, unit, UnitOfEnergy.KILO_WATT_HOUR\n            )\n        )\n    except (HomeAssistantError, TypeError, ValueError):\n        # An unknown historic unit is safer to ignore than to reinterpret.\n        return None\n\n\n@dataclass(frozen=True, kw_only=True)\nclass TsunSensorDescription''',
)
replace_once(
    sensor,
    "                state_value = energy_value(last_state.state)\n",
    "                state_value = _restored_energy_kwh(last_state)\n",
)
replace_once(
    sensor,
    '''            current_raw, current_total = self._current_daily_inputs(\n                require_online=True\n            )\n            self._daily_tracker.restore(\n''',
    '''            current_raw, current_total = self._current_daily_inputs(\n                require_online=True\n            )\n            if (\n                state_value is not None\n                and last_state is not None\n                and last_state.attributes.get(\"tracking_source\")\n                == \"total_delta_with_daily_fallback\"\n                and \"tracking_version\" not in last_state.attributes\n            ):\n                state_value = repair_legacy_daily_state(\n                    state_value,\n                    current_total_energy=current_total,\n                    restored_total_energy=restored_total,\n                )\n            self._daily_tracker.restore(\n''',
)
replace_once(
    sensor,
    "        self._restored_energy_value = energy_value(last_state.state)\n",
    "        self._restored_energy_value = _restored_energy_kwh(last_state)\n",
)


daily = ROOT / "custom_components/tsun_local/daily_energy.py"
replace_once(
    daily,
    "\n\n@dataclass(slots=True)\nclass DailyEnergyTracker",
    '''\n\n# Supported TSUN Local micro-inverters cannot physically produce 100 kWh in\n# one local day. This conservative ceiling is used only to repair clearly\n# impossible 1.6.1 states that were already contaminated by the Wh/kWh\n# restore regression. Plausible values are never guessed or rewritten.\nLEGACY_DAILY_SANITY_LIMIT_KWH = 100.0\n\n\ndef repair_legacy_daily_state(\n    state_value: float,\n    *,\n    current_total_energy: float | None,\n    restored_total_energy: float | None,\n) -> float:\n    \"\"\"Repair only unambiguous 1.6.1 x1000 daily-energy contamination.\"\"\"\n    if state_value < 0:\n        return 0.0\n    candidate = state_value / 1000.0\n\n    # A daily value above this ceiling is impossible for supported hardware.\n    if (\n        state_value >= LEGACY_DAILY_SANITY_LIMIT_KWH\n        and candidate < LEGACY_DAILY_SANITY_LIMIT_KWH\n    ):\n        return candidate\n\n    # Daily energy can never exceed the lifetime total. If only the /1000\n    # candidate satisfies that invariant, the legacy scale error is certain.\n    for total in (current_total_energy, restored_total_energy):\n        if total is None or total < 0:\n            continue\n        if state_value > total + 1e-6 and candidate <= total + 1e-6:\n            return candidate\n\n    return state_value\n\n\n@dataclass(slots=True)\nclass DailyEnergyTracker''',
)
replace_once(
    daily,
    '''        attributes: dict[str, Any] = {\n            "tracking_date": self.local_date.isoformat(),\n            "tracking_source": "total_delta_with_daily_fallback",\n        }\n''',
    '''        attributes: dict[str, Any] = {\n            "tracking_date": self.local_date.isoformat(),\n            "tracking_source": "total_delta_with_daily_fallback",\n            "tracking_version": 2,\n        }\n''',
)


test_daily = ROOT / "tests/test_daily_energy_tracker.py"
text = test_daily.read_text(encoding="utf-8")
text = text.replace(
    "DailyEnergyTracker = MODULE.DailyEnergyTracker\n",
    "DailyEnergyTracker = MODULE.DailyEnergyTracker\nrepair_legacy_daily_state = MODULE.repair_legacy_daily_state\n",
    1,
)
needle = "\n\nif __name__ == \"__main__\":\n"
if needle not in text:
    raise SystemExit("test_daily_energy_tracker.py footer not found")
new_tests = '''\n    def test_repairs_gross_161_wh_kwh_contamination(self) -> None:\n        self.assertAlmostEqual(\n            repair_legacy_daily_state(\n                190.27,\n                current_total_energy=42.0,\n                restored_total_energy=41.99,\n            ),\n            0.19027,\n        )\n\n    def test_repairs_legacy_daily_value_that_exceeds_lifetime_total(self) -> None:\n        self.assertAlmostEqual(\n            repair_legacy_daily_state(\n                50.0,\n                current_total_energy=12.0,\n                restored_total_energy=11.99,\n            ),\n            0.05,\n        )\n\n    def test_keeps_plausible_legacy_daily_value(self) -> None:\n        self.assertEqual(\n            repair_legacy_daily_state(\n                5.0,\n                current_total_energy=120.0,\n                restored_total_energy=119.9,\n            ),\n            5.0,\n        )\n\n    def test_tracker_metadata_marks_normalized_restore_version(self) -> None:\n        tracker = DailyEnergyTracker(date(2026, 9, 12), value=1.25)\n        self.assertEqual(tracker.state_attributes()[\"tracking_version\"], 2)\n'''
text = text.replace(needle, new_tests + needle, 1)
test_daily.write_text(text, encoding="utf-8")


test_contract = ROOT / "tests/test_energy_restore_contract.py"
text = test_contract.read_text(encoding="utf-8")
needle = "\n\nif __name__ == \"__main__\":\n"
if needle not in text:
    raise SystemExit("test_energy_restore_contract.py footer not found")
contract_tests = '''\n    def test_restored_energy_is_normalized_from_display_unit_to_kwh(self) -> None:\n        source = (ROOT / \"custom_components/tsun_local/sensor.py\").read_text(\n            encoding=\"utf-8\"\n        )\n        self.assertIn(\"def _restored_energy_kwh\", source)\n        self.assertIn(\"EnergyConverter.convert\", source)\n        self.assertIn('state.attributes.get(\"unit_of_measurement\")', source)\n        self.assertIn(\"UnitOfEnergy.KILO_WATT_HOUR\", source)\n        self.assertNotIn(\"state_value = energy_value(last_state.state)\", source)\n        self.assertNotIn(\"_restored_energy_value = energy_value(last_state.state)\", source)\n\n    def test_161_contamination_is_only_repaired_without_v2_tracker_metadata(self) -> None:\n        source = (ROOT / \"custom_components/tsun_local/sensor.py\").read_text(\n            encoding=\"utf-8\"\n        )\n        self.assertIn(\"repair_legacy_daily_state\", source)\n        self.assertIn('\\\"tracking_version\\\" not in last_state.attributes', source)\n'''
text = text.replace(needle, contract_tests + needle, 1)
test_contract.write_text(text, encoding="utf-8")


manifest_path = ROOT / "custom_components/tsun_local/manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["version"] = "1.6.2"
manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


changelog = ROOT / "CHANGELOG.md"
text = changelog.read_text(encoding="utf-8")
old = '''## [Unreleased]\n\n### Changed\n\n- Map MP3000 / 1511 `alarm_global_1_raw = 8192` (`0x2000`, bit 13) to the localized alarm **Low solar input** with stable code `1511-A030`. Keep the existing non-fault handling when this low-solar status is the only active bit.\n- Add a protocol-aware `country_profile` diagnostic that keeps the numeric code and appends a native country/grid-profile name when known, including 1511 evidence for `2 (Deutschland)`, `6 (Polska)` and `8 (France)`.\n- Reduce Home Assistant Activity noise across 1511, 02B0 and 1097 by publishing the visible `communication_last_success` timestamp at most every five minutes, hiding it and raw `*_raw` diagnostics from normal UI visibility while keeping exact last-success timing in diagnostics; existing entries are migrated once and user unhide choices are respected afterwards.\n'''
new = '''## [Unreleased]\n\n## [1.6.2] - 2026-09-12\n\n### Fixed\n\n- Normalize restored Home Assistant energy states from their stored display unit to TSUN Local's native kWh before reusing them, preventing Wh/kWh scale corruption after an update or restart.\n- Apply the same restore-unit protection to AC and PV energy entities across 1511, 02B0 and 1097.\n- Repair only clearly impossible 1.6.1 daily-energy states already contaminated by the x1000 restore regression; plausible values are left untouched and normal midnight rollover remains authoritative.\n\n### Changed\n\n- Map MP3000 / 1511 `alarm_global_1_raw = 8192` (`0x2000`, bit 13) to the localized alarm **Low solar input** with stable code `1511-A030`. Keep the existing non-fault handling when this low-solar status is the only active bit.\n- Add a protocol-aware `country_profile` diagnostic that keeps the numeric code and appends a native country/grid-profile name when known, including 1511 evidence for `2 (Deutschland)`, `6 (Polska)` and `8 (France)`.\n- Reduce Home Assistant Activity noise across 1511, 02B0 and 1097 by publishing the visible `communication_last_success` timestamp at most every five minutes, hiding it and raw `*_raw` diagnostics from normal UI visibility while keeping exact last-success timing in diagnostics; existing entries are migrated once and user unhide choices are respected afterwards.\n\n### Validation\n\n- Add regression coverage for restored Wh/kWh energy states, clearly contaminated 1.6.1 daily states, plausible legacy values, and tracker metadata versioning.\n- Run the complete unit-test suite, HACS validation and Home Assistant Hassfest on the final stable source before publication.\n'''
if text.count(old) != 1:
    raise SystemExit("Expected Unreleased block not found exactly once")
changelog.write_text(text.replace(old, new, 1), encoding="utf-8")


release_notes = ROOT / "docs/releases/1.6.2.md"
release_notes.write_text('''# TSUN Local 1.6.2\n\nTSUN Local 1.6.2 stabilizes daily-energy restoration and promotes the validated 1.6.2 beta work to stable.\n\n## Critical daily-energy restore fix\n\n- Restored Home Assistant energy states are now converted from the stored display unit (for example Wh) to TSUN Local's native kWh before they are reused.\n- This prevents the 1.6.1 update/restart regression where a value such as `190 Wh` could be interpreted as `190 kWh`.\n- AC and PV daily/total energy restoration uses the same unit-safe path for 1511, 02B0 and 1097.\n- Clearly impossible 1.6.1 daily values already affected by the x1000 regression are repaired conservatively; plausible values are never guessed.\n- Home Assistant local midnight remains the only displayed daily-energy boundary. Hardware/logger counter resets continue to be handled with total-energy deltas.\n\n## Activity and diagnostics\n\n- `communication_last_success` is published to the UI at most every five minutes while exact poll timing remains in diagnostics.\n- Raw `*_raw` diagnostics and the last-success timestamp stay available but are hidden from normal UI visibility by default.\n- Meaningful communication, adaptive polling, operating-state and decoded alarm entities remain visible.\n\n## Country / grid profile\n\n- Adds protocol-aware `country_profile` presentation as `code (native name)`.\n- 1511 evidence includes `2 (Deutschland)`, `6 (Polska)` and `8 (France)`.\n- 02B0 and 1097 keep their protocol-specific profile sources. Unknown values remain numeric rather than guessed.\n\n## Alarm decoding\n\n- MP3000 / 1511 `A030` (`8192 / 0x2000` in global alarm word 1) is decoded as **Low solar input**.\n\n## Validation\n\nThe stable source is published only after the complete unit-test suite, HACS validation and Home Assistant Hassfest pass. TSUN Local remains local and strictly read-only.\n''', encoding="utf-8")


# Promote the public stable version markers without rewriting historical notes.
for rel in [Path("README.md"), *(Path("docs") / name for name in (
    "README_FR.md", "README_DE.md", "README_ES.md", "README_IT.md",
    "README_NL.md", "README_PL.md", "README_ZH.md",
))]:
    path = ROOT / rel
    t = path.read_text(encoding="utf-8")
    t = t.replace("<strong>1.6.1</strong>", "<strong>1.6.2</strong>", 1)
    path.write_text(t, encoding="utf-8")

index = ROOT / "docs/index.html"
t = index.read_text(encoding="utf-8")
t = t.replace("TSUN Local 1.6.1", "TSUN Local 1.6.2")
t = t.replace("NEW IN 1.6.1", "NEW IN 1.6.2")
index.write_text(t, encoding="utf-8")

web_test = ROOT / "tests/test_release_154_web.py"
t = web_test.read_text(encoding="utf-8")
t = t.replace('self.assertIn("NEW IN 1.6.1", index)', 'self.assertIn("NEW IN 1.6.2", index)')
t = t.replace('self.assertIn("NEW IN 1.6.1", text)', 'self.assertIn("NEW IN 1.6.2", text)')
web_test.write_text(t, encoding="utf-8")

print("Prepared TSUN Local 1.6.2 stable source")
