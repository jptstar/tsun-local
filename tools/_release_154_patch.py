from __future__ import annotations

import json
from pathlib import Path
import re

ROOT = Path(__file__).parents[1]
VERSION = "1.5.4"

README_NOTES = {
    "README.md": "TSUN Local 1.5.4 adds inverter temperature, inverter firmware version and additional read-only 02B0 operating/configuration diagnostics, including a raw product-compliance profile value.",
    "docs/README_FR.md": "TSUN Local 1.5.4 ajoute la température de l’onduleur, la version du firmware de l’onduleur et des diagnostics 02B0 supplémentaires en lecture seule, dont une valeur brute de conformité produit.",
    "docs/README_DE.md": "TSUN Local 1.5.4 ergänzt Wechselrichtertemperatur, Wechselrichter-Firmwareversion und zusätzliche schreibgeschützte 02B0-Betriebs- und Konfigurationsdiagnosen, einschließlich eines rohen Produktkonformitätswerts.",
    "docs/README_ES.md": "TSUN Local 1.5.4 añade la temperatura del inversor, la versión de firmware del inversor y diagnósticos 02B0 adicionales de solo lectura, incluido un valor bruto de conformidad del producto.",
    "docs/README_IT.md": "TSUN Local 1.5.4 aggiunge temperatura dell’inverter, versione firmware dell’inverter e ulteriori diagnostiche 02B0 in sola lettura, incluso un valore grezzo di conformità del prodotto.",
    "docs/README_NL.md": "TSUN Local 1.5.4 voegt omvormertemperatuur, omvormerfirmwareversie en extra alleen-lezen 02B0-bedrijfs- en configuratiediagnostiek toe, inclusief een ruwe productconformiteitswaarde.",
    "docs/README_PL.md": "TSUN Local 1.5.4 dodaje temperaturę falownika, wersję oprogramowania falownika oraz dodatkową diagnostykę 02B0 tylko do odczytu, w tym surową wartość zgodności produktu.",
    "docs/README_ZH.md": "TSUN Local 1.5.4 新增逆变器温度、逆变器固件版本以及更多只读 02B0 运行/配置诊断，其中包括原始产品合规类型值。",
}


def update_readme(path: Path, note: str) -> None:
    text = path.read_text(encoding="utf-8")
    text = text.replace("<strong>1.5.3</strong>", f"<strong>{VERSION}</strong>", 1)
    if note not in text:
        match = re.search(r"(### 02B0[^\n]*\n.*?)(\n### 1097)", text, flags=re.S)
        if match is None:
            raise RuntimeError(f"02B0 section not found in {path}")
        updated = match.group(1).rstrip() + "\n\n" + note + "\n"
        text = text[: match.start(1)] + updated + text[match.end(1) :]
    path.write_text(text, encoding="utf-8")


def update_entities_md() -> None:
    path = ROOT / "docs/ENTITIES.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace("## 02B0 advanced diagnostics\n", "## 02B0 advanced diagnostics — 1.5.4\n", 1)
    anchor = "| `output_coefficient` | Power level | % |"
    rows = """| `inverter_temperature` | Inverter temperature | °C |
| `inverter_firmware_version` | Inverter firmware version | text |
| `boot_status_raw` | Raw boot status | raw |
| `dsp_status_raw` | Raw DSP status | raw |
| `work_mode_raw` | Raw work mode | raw |
| `output_shutdown_raw` | Raw output shutdown status | raw |
| `rated_level_raw` | Raw rated level | raw |
| `input_coefficient` | Input coefficient | % |
| `product_compliance_type_raw` | Product compliance type (raw) | raw |"""
    if "`product_compliance_type_raw`" not in text:
        if anchor not in text:
            raise RuntimeError("02B0 advanced diagnostics anchor not found")
        text = text.replace(anchor, anchor + "\n" + rows, 1)
        note = (
            "\n> [!NOTE]\n"
            "> `product_compliance_type_raw` is intentionally exposed as a raw diagnostic. "
            "TSUN Local does not translate this 02B0 value into a country or grid profile until independent hardware correlation confirms its semantics.\n"
        )
        insert_at = text.index("\n---\n\n# 1097", text.index(rows))
        text = text[:insert_at] + note + text[insert_at:]
    path.write_text(text, encoding="utf-8")


def update_entities_html() -> None:
    path = ROOT / "docs/entities.html"
    text = path.read_text(encoding="utf-8")
    head_end = text.index("</head>")
    head = text[:head_end].replace("1.5.3", VERSION)
    text = head + text[head_end:]
    text = text.replace('<span class="badge stable">1.5.3 STABLE</span>', f'<span class="badge stable">{VERSION} STABLE</span>', 1)
    text = text.replace("TSUN Local 1.5.3 unifies the compact alarm interface", "TSUN Local keeps the compact alarm interface", 1)
    marker = "<section><h2>1097 · GEN3 / GEN3 PLUS</h2>"
    block = """
  <section><span class="badge stable">NEW IN 1.5.4</span><h2>02B0 diagnostics added in 1.5.4</h2><p class="intro">Nine additional read-only 02B0 diagnostics are now exposed. Expert/raw values remain disabled by default where appropriate.</p><table><thead><tr><th>Entity</th><th>Meaning</th><th>Type</th></tr></thead><tbody><tr><td><code>inverter_temperature</code></td><td>Inverter temperature</td><td>°C</td></tr><tr><td><code>inverter_firmware_version</code></td><td>Inverter firmware version</td><td>text</td></tr><tr><td><code>boot_status_raw</code></td><td>Boot status</td><td>raw</td></tr><tr><td><code>dsp_status_raw</code></td><td>DSP status</td><td>raw</td></tr><tr><td><code>work_mode_raw</code></td><td>Work mode</td><td>raw</td></tr><tr><td><code>output_shutdown_raw</code></td><td>Output shutdown status</td><td>raw</td></tr><tr><td><code>rated_level_raw</code></td><td>Rated level</td><td>raw</td></tr><tr><td><code>input_coefficient</code></td><td>Input coefficient</td><td>%</td></tr><tr><td><code>product_compliance_type_raw</code></td><td>Product compliance type</td><td>raw</td></tr></tbody></table><div class="note warning"><code>product_compliance_type_raw</code> is kept raw and is not presented as a country/grid profile until independently validated.</div></section>

"""
    if "02B0 diagnostics added in 1.5.4" not in text:
        if marker not in text:
            raise RuntimeError("entities.html 1097 marker not found")
        text = text.replace(marker, block + marker, 1)
    path.write_text(text, encoding="utf-8")


def update_index_html() -> None:
    path = ROOT / "docs/index.html"
    text = path.read_text(encoding="utf-8")
    head_end = text.index("</head>")
    head = text[:head_end].replace("1.5.3", VERSION)
    text = head + text[head_end:]
    old = re.compile(
        r'<aside class="preview-card" aria-label="TSUN Local 1\.5\.3 highlights">.*?</aside>',
        flags=re.S,
    )
    new = '''<aside class="preview-card" aria-label="TSUN Local 1.5.4 highlights">
        <span class="preview-kicker">NEW IN 1.5.4</span>
        <h3>More 02B0 diagnostics</h3>
        <div class="preview-primary">
          <strong>Temperature, inverter firmware and additional read-only diagnostics</strong>
          <span>02B0 devices now expose nine additional operating and configuration diagnostics without adding any inverter write operation.</span>
        </div>
        <div class="preview-stats">
          <div class="preview-stat"><strong>9</strong><span>new 02B0 diagnostic entities</span></div>
          <div class="preview-stat"><strong>0</strong><span>new write operations<br>read-only by design</span></div>
        </div>
        <div class="preview-note">Product compliance type remains raw until its country/grid-profile meaning is independently validated.</div>
      </aside>'''
    text, count = old.subn(new, text, count=1)
    if count != 1:
        raise RuntimeError("1.5.3 preview card not found in index.html")
    path.write_text(text, encoding="utf-8")


def update_play2_html() -> None:
    path = ROOT / "docs/sunology-play2.html"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "VALIDATED ON REAL PLAY2 HARDWARE",
        "VALIDATED ON REAL SUNOLOGY PLAY2 HARDWARE",
        1,
    )
    path.write_text(text, encoding="utf-8")


def update_changelog() -> None:
    path = ROOT / "CHANGELOG.md"
    text = path.read_text(encoding="utf-8")
    if "## [1.5.4]" in text:
        return
    marker = "## [1.5.3] - 2026-08-27"
    section = """## [1.5.4] - 2026-08-27

### Added

- Extend protocol 02B0 with inverter temperature from register `0x300C` (`raw - 40 °C`) and the inverter firmware version from `0x3008`.
- Add read-only 02B0 operating/configuration diagnostics: boot status, DSP status, work mode, output shutdown status, rated level, input coefficient and raw product compliance type.
- Decode the 02B0 input coefficient as `raw × 100 / 1024 %`.

### Changed

- Expose `product_compliance_type_raw` without assigning a country/grid-profile meaning until independent hardware correlation validates the semantic mapping.
- Refresh the entity reference, public website version/highlights and all eight README languages for 1.5.4.

### Safety

- All new 02B0 access uses Modbus function 03 and remains strictly read-only.
- Existing 02B0 PV/AC energy scaling and 32-bit total-energy decoding are unchanged.
- No inverter configuration, country/profile, protection-setting or control write is added.

"""
    if marker not in text:
        raise RuntimeError("CHANGELOG 1.5.3 marker not found")
    text = text.replace(marker, section + marker, 1)
    path.write_text(text, encoding="utf-8")


def create_release_notes() -> None:
    path = ROOT / "docs/releases/1.5.4.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """# TSUN Local 1.5.4

TSUN Local 1.5.4 expands the validated 02B0 local path with additional **read-only** inverter diagnostics.

## New 02B0 entities

- `inverter_temperature` — inverter temperature (`0x300C`, `raw - 40 °C`)
- `inverter_firmware_version` — inverter firmware version (`0x3008`)
- `boot_status_raw` — boot status (`0x2000`)
- `dsp_status_raw` — DSP status (`0x2001`)
- `work_mode_raw` — work mode (`0x2003`)
- `output_shutdown_raw` — output shutdown status (`0x2006`)
- `rated_level_raw` — rated level (`0x2008`)
- `input_coefficient` — input coefficient (`0x2009`, `raw × 100 / 1024 %`)
- `product_compliance_type_raw` — product compliance type (`0x2010`, raw)

`product_compliance_type_raw` is deliberately not translated into a country/grid profile yet. The register is exposed for diagnostics and cross-device validation only.

## Safety and compatibility

- Strictly local and read-only.
- New register reads use Modbus function 03 only.
- No inverter configuration writes are introduced.
- Existing 02B0 AC/PV measurement and energy decoding is unchanged.
- Documentation, entity reference, website highlights and all eight README languages are synchronized with 1.5.4.
""",
        encoding="utf-8",
    )


def update_release_test() -> None:
    old = ROOT / "tests/test_release_153_web.py"
    new = ROOT / "tests/test_release_154_web.py"
    text = old.read_text(encoding="utf-8") if old.exists() else new.read_text(encoding="utf-8")
    text = text.replace("Release153WebTests", "Release154WebTests")
    text = text.replace("test_manifest_is_stable_153", "test_manifest_is_stable_154")
    text = text.replace('self.assertEqual("1.5.3", manifest["version"])', 'self.assertEqual("1.5.4", manifest["version"])')
    text = text.replace("test_public_pages_do_not_advertise_beta_153", "test_public_pages_do_not_advertise_beta_154")
    text = text.replace('self.assertNotIn("1.5.3 beta", text, filename)', 'self.assertNotIn("1.5.4 beta", text, filename)')
    text = text.replace('self.assertNotIn("1.5.3-beta", text, filename)', 'self.assertNotIn("1.5.4-beta", text, filename)')
    needle = '        self.assertIn("contributors.html", text)\n'
    extra = '        self.assertIn("NEW IN 1.5.4", text)\n        self.assertIn("product_compliance_type_raw", (DOCS / "entities.html").read_text(encoding="utf-8"))\n'
    if extra.strip() not in text:
        text = text.replace(needle, needle + extra, 1)
    new.write_text(text, encoding="utf-8")
    if old.exists() and old != new:
        old.unlink()


def validate_json() -> None:
    component = ROOT / "custom_components/tsun_local"
    json.loads((component / "manifest.json").read_text(encoding="utf-8"))
    json.loads((component / "strings.json").read_text(encoding="utf-8"))
    for path in (component / "translations").glob("*.json"):
        json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    for relpath, note in README_NOTES.items():
        update_readme(ROOT / relpath, note)
    update_entities_md()
    update_entities_html()
    update_index_html()
    update_play2_html()
    update_changelog()
    create_release_notes()
    update_release_test()
    validate_json()


if __name__ == "__main__":
    main()
