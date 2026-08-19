from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")


def patch_protocol_tables(path: str, rows: dict[str, dict[str, str]]) -> None:
    lines = read(path).splitlines()
    section: str | None = None
    out: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("### 1511 "):
            section = "1511"
        elif stripped.startswith("### 02B0 "):
            section = "02B0"
        elif stripped.startswith("### 1097 "):
            section = "1097"
        elif stripped.startswith("## ") and not stripped.startswith("### "):
            section = None

        if section in ("1511", "02B0"):
            if stripped.startswith("| 🚨"):
                line = rows[section]["diag"]
            elif stripped.startswith("| 🛡️"):
                line = rows[section]["advanced"]
        out.append(line)

    text = "\n".join(out) + "\n"
    # Normalize protocol-family presentation consistently with the main README.
    text = text.replace("GEN3 PLUS · **TSOL-MX500**", "GEN3 / GEN3 PLUS · **TSOL-MX500**")
    text = text.replace("### 02B0 · GEN3 PLUS", "### 02B0 · GEN3 / GEN3 PLUS")
    text = text.replace("### 1097 · GEN3 —", "### 1097 · GEN3 / GEN3 PLUS —")
    # Normalize the compact compatibility table where the localized file still uses GEN3 only.
    text = text.replace("| **1097** | GEN3 |", "| **1097** | GEN3 / GEN3 PLUS |")
    write(path, text)


localized_rows = {
    "docs/README_FR.md": {
        "1511": {
            "diag": "| 🚨 **Diagnostics** | Alarme onduleur · compteur et noms des alarmes actives · firmwares DSP/QCPU |",
            "advanced": "| 🛡️ **Avancé** | Seuils et temporisations de protection réseau · 10 diagnostics A1/21 supplémentaires en validation terrain · code pays/profil brut candidat · températures |",
        },
        "02B0": {
            "diag": "| 🚨 **Diagnostics** | Alarmes onduleur |",
            "advanced": "| 🛡️ **Avancé** | Diagnostics de protection réseau · Niveau de puissance (%) |",
        },
    },
    "docs/README_DE.md": {
        "1511": {
            "diag": "| 🚨 **Diagnose** | Wechselrichteralarm · Anzahl und Namen aktiver Alarme · DSP/QCPU-Firmwareversionen |",
            "advanced": "| 🛡️ **Erweitert** | Netzschutz-Schwellenwerte und Zeitdiagnosen · 10 zusätzliche A1/21-Feldvalidierungsdiagnosen · Rohwert für Land/Profil als Kandidat · Wechselrichter- und Umgebungstemperatur |",
        },
        "02B0": {
            "diag": "| 🚨 **Diagnose** | Wechselrichteralarme |",
            "advanced": "| 🛡️ **Erweitert** | Netzschutzdiagnosen · Leistungsniveau (%) |",
        },
    },
    "docs/README_ES.md": {
        "1511": {
            "diag": "| 🚨 **Diagnóstico** | Alarma del inversor · contador y nombres de alarmas activas · firmware DSP/QCPU |",
            "advanced": "| 🛡️ **Avanzado** | Umbrales y tiempos de protección de red · 10 diagnósticos A1/21 adicionales de validación en campo · candidato bruto país/perfil · temperaturas |",
        },
        "02B0": {
            "diag": "| 🚨 **Diagnóstico** | Alarmas del inversor |",
            "advanced": "| 🛡️ **Avanzado** | Diagnósticos de protección de red · Nivel de potencia (%) |",
        },
    },
    "docs/README_IT.md": {
        "1511": {
            "diag": "| 🚨 **Diagnostica** | Allarme inverter · conteggio e nomi allarmi attivi · firmware DSP/QCPU |",
            "advanced": "| 🛡️ **Avanzato** | Soglie e tempi di protezione rete · 10 diagnostiche A1/21 aggiuntive di validazione sul campo · candidato grezzo paese/profilo · temperature |",
        },
        "02B0": {
            "diag": "| 🚨 **Diagnostica** | Allarmi inverter |",
            "advanced": "| 🛡️ **Avanzato** | Diagnostica protezione rete · Livello di potenza (%) |",
        },
    },
    "docs/README_NL.md": {
        "1511": {
            "diag": "| 🚨 **Diagnostiek** | Omvormeralarm · aantal en namen van actieve alarmen · DSP/QCPU-firmwareversies |",
            "advanced": "| 🛡️ **Geavanceerd** | Netbeveiligingsdrempels en tijden · 10 extra A1/21-veldvalidatiediagnoses · ruwe land/profielkandidaat · temperaturen |",
        },
        "02B0": {
            "diag": "| 🚨 **Diagnostiek** | Omvormeralarmen |",
            "advanced": "| 🛡️ **Geavanceerd** | Netbeveiligingsdiagnostiek · Vermogensniveau (%) |",
        },
    },
    "docs/README_PL.md": {
        "1511": {
            "diag": "| 🚨 **Diagnostyka** | Alarm falownika · liczba i nazwy aktywnych alarmów · firmware DSP/QCPU |",
            "advanced": "| 🛡️ **Zaawansowane** | Progi i czasy ochrony sieci · 10 dodatkowych diagnostyk A1/21 do walidacji terenowej · surowy kandydat kraj/profil · temperatury |",
        },
        "02B0": {
            "diag": "| 🚨 **Diagnostyka** | Alarmy falownika |",
            "advanced": "| 🛡️ **Zaawansowane** | Diagnostyka ochrony sieci · Poziom mocy (%) |",
        },
    },
    "docs/README_ZH.md": {
        "1511": {
            "diag": "| 🚨 **诊断** | 逆变器告警 · 活动告警数量和名称 · DSP/QCPU 固件版本 |",
            "advanced": "| 🛡️ **高级** | 电网保护阈值与延时 · 10 项额外 A1/21 现场验证诊断 · 国家/配置原始候选值 · 温度 |",
        },
        "02B0": {
            "diag": "| 🚨 **诊断** | 逆变器告警 |",
            "advanced": "| 🛡️ **高级** | 电网保护诊断 · 功率水平 (%) |",
        },
    },
}

for path, rows in localized_rows.items():
    patch_protocol_tables(path, rows)

# Stable public landing page: remove leftover beta wording and align alarm evidence terminology.
path = "docs/index.html"
text = read(path)
replacements = {
    '<a href="#beta">1.5.1 beta</a>': '<a href="#release">1.5.1</a>',
    '<section id="beta">': '<section id="release">',
    "Validated example": "Hardware-observed example",
    ">VALIDATED<": ">OBSERVED<",
    "12 validated · 84 require control-hardware validation": "12 hardware-observed · 84 require control-hardware validation",
    "No alarm regression in the beta feature set": "No alarm regression in 1.5.1",
    "The new beta diagnostics do not create duplicate alarm entities.": "The 1.5.1 diagnostics do not create duplicate alarm entities.",
    "What is beta in 1.5.1?": "What is new in 1.5.1?",
    "the new MP3000 semantic diagnostics are intentionally labelled as field-validation candidates.": "the additional MP3000 semantic diagnostics remain explicitly labelled as field-validation candidates until independently confirmed.",
}
for old, new in replacements.items():
    text = text.replace(old, new)
write(path, text)

# Visual entity page: align counts and stable wording.
path = "docs/entities.html"
text = read(path)
replacements = {
    "105 entities with 6 PV inputs": "108 entities with 6 PV inputs",
    "New semantic diagnostics in beta": "Field-validation diagnostics",
    "Wi-Fi signal fix in 1.5.1-beta.4": "Wi-Fi signal fix in 1.5.1",
    "Device and logger</td><td>5</td><td>Serial numbers, logger firmware, MAC and Wi-Fi": "Device and logger</td><td>8</td><td>Serial numbers, logger/DSP/QCPU firmware, MAC and Wi-Fi",
    "physically verified alarm mappings": "hardware-observed alarm mappings",
}
for old, new in replacements.items():
    text = text.replace(old, new)
write(path, text)

# Tighten stable documentation regression checks.
metadata_path = ROOT / "tests" / "test_metadata.py"
metadata = metadata_path.read_text(encoding="utf-8")
needle = '        self.assertNotIn("Profile-only data", entities)\n'
extra = (
    '        self.assertNotIn("1.5.1 beta", index)\n'
    '        self.assertNotIn("1.5.1-beta", index)\n'
    '        self.assertNotIn("105 entities with 6 PV inputs", entities)\n'
    '        self.assertNotIn("New semantic diagnostics in beta", entities)\n'
    '        self.assertIn("108 entities with 6 PV inputs", entities)\n'
    '        self.assertIn("Device and logger</td><td>8</td>", entities)\n'
)
if extra not in metadata:
    if needle not in metadata:
        raise SystemExit("metadata insertion point not found")
    metadata = metadata.replace(needle, needle + extra, 1)
metadata_path.write_text(metadata, encoding="utf-8")

# Localized README structural regression: stable version, correct 1511 firmware row,
# and no DSP/QCPU firmware row inside the 02B0 section.
localized_test = '''from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).parents[1]

FILES = (
    "README_FR.md",
    "README_DE.md",
    "README_ES.md",
    "README_IT.md",
    "README_NL.md",
    "README_PL.md",
    "README_ZH.md",
)


class Stable151LocalizedReadmeTests(unittest.TestCase):
    def test_all_localized_readmes_describe_stable_151(self) -> None:
        for filename in FILES:
            text = (ROOT / "docs" / filename).read_text(encoding="utf-8")
            self.assertIn("<strong>1.5.1</strong>", text, filename)
            self.assertIn("DSP", text, filename)
            self.assertIn("QCPU1", text, filename)
            self.assertIn("QCPU2", text, filename)

    def test_dsp_qcpu_firmware_is_1511_only(self) -> None:
        for filename in FILES:
            text = (ROOT / "docs" / filename).read_text(encoding="utf-8")
            start_1511 = text.index("### 1511")
            start_02b0 = text.index("### 02B0", start_1511)
            start_1097 = text.index("### 1097", start_02b0)
            section_1511 = text[start_1511:start_02b0]
            section_02b0 = text[start_02b0:start_1097]
            self.assertIn("DSP", section_1511, filename)
            self.assertIn("QCPU", section_1511, filename)
            self.assertNotIn("DSP", section_02b0, filename)
            self.assertNotIn("QCPU", section_02b0, filename)

    def test_removed_1511_power_candidate_is_not_back_in_localized_tables(self) -> None:
        candidate_words = (
            "niveau de puissance candidat",
            "leistungsniveau (kandidat)",
            "nivel de potencia (candidato)",
            "livello di potenza (candidato)",
            "vermogensniveau (kandidaat)",
            "poziom mocy (kandydat)",
            "功率水平（候选）",
        )
        for filename in FILES:
            text = (ROOT / "docs" / filename).read_text(encoding="utf-8")
            start_1511 = text.index("### 1511")
            start_02b0 = text.index("### 02B0", start_1511)
            section_1511 = text[start_1511:start_02b0].lower()
            for phrase in candidate_words:
                self.assertNotIn(phrase.lower(), section_1511, filename)


if __name__ == "__main__":
    unittest.main()
'''
(ROOT / "tests" / "test_stable_151_localized_readmes.py").write_text(localized_test, encoding="utf-8")

# Fail fast if stable public pages still expose stale beta/count strings.
index = read("docs/index.html")
entities = read("docs/entities.html")
for forbidden in ("1.5.1 beta", "1.5.1-beta"):
    if forbidden in index:
        raise SystemExit(f"Stale stable-site text: {forbidden}")
for forbidden in ("1.5.1-beta", "105 entities with 6 PV inputs", "New semantic diagnostics in beta"):
    if forbidden in entities:
        raise SystemExit(f"Stale entity-site text: {forbidden}")

print("Cleaned stable 1.5.1 documentation")
