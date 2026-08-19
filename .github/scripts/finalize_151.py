from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPONENT = ROOT / "custom_components" / "tsun_local"
VERSION = "1.5.1"
DATE = "2026-08-19"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")


def replace(path: str, old: str, new: str, *, required: bool = False) -> None:
    text = read(path)
    if required and old not in text:
        raise SystemExit(f"Expected text not found in {path}: {old!r}")
    write(path, text.replace(old, new))


# Stable version metadata.
manifest_path = COMPONENT / "manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["version"] = VERSION
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

# Canonical firmware entity names. Technical IDs remain stable English.
strings_path = COMPONENT / "strings.json"
strings = json.loads(strings_path.read_text(encoding="utf-8"))
sensors = strings["entity"]["sensor"]
sensors["dsp_firmware_version"] = {"name": "DSP firmware version"}
sensors["qcpu1_firmware_version"] = {"name": "QCPU1 firmware version"}
sensors["qcpu2_firmware_version"] = {"name": "QCPU2 firmware version"}
strings_path.write_text(json.dumps(strings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

firmware_names = {
    "en.json": {
        "dsp_firmware_version": "DSP firmware version",
        "qcpu1_firmware_version": "QCPU1 firmware version",
        "qcpu2_firmware_version": "QCPU2 firmware version",
    },
    "fr.json": {
        "dsp_firmware_version": "Version du firmware DSP",
        "qcpu1_firmware_version": "Version du firmware QCPU1",
        "qcpu2_firmware_version": "Version du firmware QCPU2",
    },
    "de.json": {
        "dsp_firmware_version": "DSP-Firmwareversion",
        "qcpu1_firmware_version": "QCPU1-Firmwareversion",
        "qcpu2_firmware_version": "QCPU2-Firmwareversion",
    },
    "es.json": {
        "dsp_firmware_version": "Versión del firmware DSP",
        "qcpu1_firmware_version": "Versión del firmware QCPU1",
        "qcpu2_firmware_version": "Versión del firmware QCPU2",
    },
    "it.json": {
        "dsp_firmware_version": "Versione firmware DSP",
        "qcpu1_firmware_version": "Versione firmware QCPU1",
        "qcpu2_firmware_version": "Versione firmware QCPU2",
    },
    "nl.json": {
        "dsp_firmware_version": "DSP-firmwareversie",
        "qcpu1_firmware_version": "QCPU1-firmwareversie",
        "qcpu2_firmware_version": "QCPU2-firmwareversie",
    },
    "pl.json": {
        "dsp_firmware_version": "Wersja oprogramowania DSP",
        "qcpu1_firmware_version": "Wersja oprogramowania QCPU1",
        "qcpu2_firmware_version": "Wersja oprogramowania QCPU2",
    },
    "zh-Hans.json": {
        "dsp_firmware_version": "DSP 固件版本",
        "qcpu1_firmware_version": "QCPU1 固件版本",
        "qcpu2_firmware_version": "QCPU2 固件版本",
    },
}
for filename, names in firmware_names.items():
    path = COMPONENT / "translations" / filename
    data = json.loads(path.read_text(encoding="utf-8"))
    translated = data["entity"]["sensor"]
    for key, name in names.items():
        translated[key] = {"name": name}
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# README / documentation version promotion.
doc_files = [
    "README.md",
    "docs/README_FR.md",
    "docs/README_DE.md",
    "docs/README_ES.md",
    "docs/README_IT.md",
    "docs/README_NL.md",
    "docs/README_PL.md",
    "docs/README_ZH.md",
    "docs/ENTITIES.md",
    "docs/MP3000_FIELD_VALIDATION.md",
    "docs/PENDING_1.5.1.md",
    "docs/index.html",
    "docs/entities.html",
]
for path in doc_files:
    text = read(path)
    text = text.replace("1.5.1-beta.4", VERSION)
    text = text.replace("?include_prereleases", "")
    write(path, text)

# English README: final stable presentation and stricter evidence wording.
path = "README.md"
text = read(path)
text = text.replace(
    "## 🧪 1.5.1 beta: MP3000 field validation",
    "## 1.5.1: MP3000 field validation and diagnostics",
)
text = text.replace(
    "The 1.5.1 beta keeps the 1.5.0 alarm interface unchanged and adds read-only evidence gathered from complete native MP3000/TITAN dumps.",
    "TSUN Local 1.5.1 combines the complete 1.5.0 MP3000 alarm interface with the read-only diagnostics, localization fixes and firmware decoding validated throughout the 1.5.1 beta cycle.",
)
text = text.replace("| | 1.5.1 |", "| | 1.5.1 |")
text = text.replace("The **12 validated functional mappings**", "The **12 hardware-observed functional mappings**")
text = text.replace("12 validated · 84 require control-hardware validation", "12 hardware-observed · 84 require control-hardware validation")
write(path, text)

# French README: remove the old beta subsection and replace stale 1511 summary.
path = "docs/README_FR.md"
text = read(path)
text = text.replace(
    "| 🚨 **Diagnostics** | Alarme onduleur · compteur et liste des alarmes actives |",
    "| 🚨 **Diagnostics** | Alarme onduleur · compteur et noms des alarmes actives · firmwares DSP/QCPU |",
)
text = text.replace(
    "| 🛡️ **Avancé** | Seuils et temporisations de protection réseau · 10 diagnostics A1/21 supplémentaires en validation terrain · code pays/profil brut candidat · températures · niveau de puissance candidat |",
    "| 🛡️ **Avancé** | Seuils et temporisations de protection réseau · 10 diagnostics A1/21 supplémentaires en validation terrain · code pays/profil brut candidat · températures |",
)
text = text.replace("Les **12 correspondances fonctionnelles validées**", "Les **12 correspondances fonctionnelles observées sur matériel**")
fr_section = '''## 🆕 TSUN Local 1.5.1

La version **1.5.1** regroupe les évolutions de la 1.5.0 et des quatre bêtas 1.5.1 dans une version stable :

- catalogue MP3000 complet de **224 positions d’alarme**, avec **12 correspondances fonctionnelles observées sur matériel** et 212 positions conservées avec un libellé neutre ;
- capteur dédié **Noms des alarmes actives**, localisé et directement exploitable dans Home Assistant ;
- correction du signal Wi-Fi du logger : la recherche continue jusqu’à `/status.html` lorsqu’une première page valide ne contient pas le RSSI ;
- **10 diagnostics A1/21** MP3000 supplémentaires et le code pays/profil brut candidat, tous en lecture seule ;
- correction de `0x07EF` : `4000 → 40,00 %/Hz` avec le facteur candidat `×0,01` ;
- versions firmware locales **DSP V1.1.72**, **QCPU1 V1.1.54** et **QCPU2 V1.1.54** ; FCPU reste volontairement absent tant que son registre 1511 local n’est pas identifié ;
- suppression du précédent candidat non validé de niveau de puissance MP3000 ;
- IDs techniques conservés en anglais et noms d’entités traduits dans les huit langues de TSUN Local.

Pour les correspondances sémantiques A1/21 encore en validation, le statut reste :

**LIVE DEVICE READ CONFIRMED; CONFIGURATION CHANGE VALIDATION PENDING**

Les candidats `0x07F1`, `0x07F2`, `0x07F7–0x07F9`, `0x080B–0x080E`, `0x07ED`, `0x0809` et `0x0BD2` restent documentés comme recherche et ne sont pas publiés comme entités sémantiques tant qu’une validation indépendante n’est pas disponible.

📚 Voir **[MP3000 / TITAN 1511 — diagnostics de validation terrain](MP3000_FIELD_VALIDATION.md)**.
'''
text = re.sub(
    r"## 🧪 TSUN Local 1\.5\.1 beta 1\n.*?(?=\n---\n\n## 🛡️ Diagnostics avancés)",
    fr_section.rstrip(),
    text,
    flags=re.S,
)
write(path, text)

# Localized long-form README refreshes. These versions previously still described 1.5.0.
localized = {
    "docs/README_DE.md": {
        "version_old": "<strong>1.5.0</strong>",
        "diag_old": "| 🚨 **Diagnose** | Wechselrichteralarme |",
        "diag_new": "| 🚨 **Diagnose** | Wechselrichteralarm · Anzahl und Namen aktiver Alarme · DSP/QCPU-Firmwareversionen |",
        "adv_old": "| 🛡️ **Erweitert** | Netzschutz-Schwellenwerte und Zeitdiagnostik · Wechselrichtertemperatur · Umgebungstemperatur des Wechselrichters · Leistungsniveau (Kandidat) |",
        "adv_new": "| 🛡️ **Erweitert** | Netzschutz-Schwellenwerte und Zeitdiagnostik · 10 zusätzliche A1/21-Feldvalidierungsdiagnosen · Rohwert für Land/Profil als Kandidat · Wechselrichter- und Umgebungstemperatur |",
        "alarm_old": "**12 funktionale Zuordnungen** sind validiert",
        "alarm_new": "**12 funktionale Zuordnungen** wurden auf realer Hardware beobachtet",
        "section": '''## 🆕 TSUN Local 1.5.1

**1.5.1** fasst die komplette MP3000-Alarmoberfläche aus 1.5.0 und alle Korrekturen aus beta1 bis beta4 in einer stabilen Version zusammen:

- alle **224 MP3000-Alarmpositionen** bleiben erhalten; 12 funktionale Zuordnungen beruhen auf direkten Hardware-Beobachtungen;
- eigener Sensor für **aktive Alarmnamen** mit lokalisierter Anzeige;
- korrigierter Logger-WLAN-RSSI-Fallback bis `/status.html`;
- 10 zusätzliche schreibgeschützte A1/21-Feldvalidierungsdiagnosen plus Rohwert für Land/Profil;
- `0x07EF`: `4000 → 40,00 %/Hz` mit dem Kandidatenfaktor `×0,01`;
- lokale Firmwareversionen **DSP V1.1.72**, **QCPU1 V1.1.54** und **QCPU2 V1.1.54**; FCPU wird ohne identifiziertes lokales Register nicht geraten;
- der frühere unbestätigte MP3000-Leistungsniveau-Kandidat bleibt entfernt;
- technische Entity-IDs bleiben Englisch, Anzeigenamen sind in allen acht Sprachen übersetzt.

Für noch nicht unabhängig bestätigte A1/21-Zuordnungen gilt weiterhin: **LIVE DEVICE READ CONFIRMED; CONFIGURATION CHANGE VALIDATION PENDING**.
''',
    },
    "docs/README_ES.md": {
        "version_old": "<strong>1.5.0</strong>",
        "diag_old": "| 🚨 **Diagnóstico** | Alarmas del inversor |",
        "diag_new": "| 🚨 **Diagnóstico** | Alarma del inversor · contador y nombres de alarmas activas · firmware DSP/QCPU |",
        "adv_old": "| 🛡️ **Avanzado** | Umbrales de protección de red y temporizaciones · Temperatura del inversor · Temperatura ambiente del inversor · Nivel de potencia (candidato) |",
        "adv_new": "| 🛡️ **Avanzado** | Umbrales y tiempos de protección de red · 10 diagnósticos A1/21 adicionales de validación en campo · candidato bruto país/perfil · temperaturas |",
        "alarm_old": "Hay **12 correspondencias funcionales validadas**",
        "alarm_new": "Hay **12 correspondencias funcionales observadas en hardware real**",
        "section": '''## 🆕 TSUN Local 1.5.1

La versión **1.5.1** reúne la interfaz completa de alarmas MP3000 de 1.5.0 y las correcciones de beta1 a beta4 en una versión estable:

- se conservan las **224 posiciones de alarma MP3000**; 12 correspondencias funcionales proceden de observaciones directas en hardware;
- sensor dedicado de **nombres de alarmas activas**, localizado para Home Assistant;
- corrección del RSSI Wi-Fi del logger con búsqueda hasta `/status.html`;
- 10 diagnósticos A1/21 adicionales de solo lectura y candidato bruto país/perfil;
- `0x07EF`: `4000 → 40,00 %/Hz` con factor candidato `×0,01`;
- firmware local **DSP V1.1.72**, **QCPU1 V1.1.54** y **QCPU2 V1.1.54**; FCPU no se publica sin un registro 1511 local identificado;
- el antiguo candidato no validado de nivel de potencia MP3000 permanece eliminado;
- IDs técnicos en inglés y nombres visibles traducidos en los ocho idiomas.

Las asignaciones A1/21 aún no confirmadas de forma independiente mantienen el estado: **LIVE DEVICE READ CONFIRMED; CONFIGURATION CHANGE VALIDATION PENDING**.
''',
    },
    "docs/README_IT.md": {
        "version_old": "<strong>1.5.0</strong>",
        "diag_old": "| 🚨 **Diagnostica** | Allarmi inverter |",
        "diag_new": "| 🚨 **Diagnostica** | Allarme inverter · conteggio e nomi allarmi attivi · firmware DSP/QCPU |",
        "adv_old": "| 🛡️ **Avanzato** | Soglie di protezione rete e temporizzazioni · Temperatura inverter · Temperatura ambiente inverter · Livello di potenza (candidato) |",
        "adv_new": "| 🛡️ **Avanzato** | Soglie e tempi di protezione rete · 10 diagnostiche A1/21 aggiuntive di validazione sul campo · candidato grezzo paese/profilo · temperature |",
        "alarm_old": "**12 corrispondenze funzionali** sono convalidate",
        "alarm_new": "**12 corrispondenze funzionali** sono state osservate direttamente su hardware reale",
        "section": '''## 🆕 TSUN Local 1.5.1

La versione **1.5.1** riunisce l’interfaccia completa degli allarmi MP3000 della 1.5.0 e le correzioni da beta1 a beta4 in una versione stabile:

- tutte le **224 posizioni di allarme MP3000** restano disponibili; 12 corrispondenze funzionali derivano da osservazioni dirette sull’hardware;
- sensore dedicato per i **nomi degli allarmi attivi**, localizzato in Home Assistant;
- correzione del fallback RSSI Wi-Fi del logger fino a `/status.html`;
- 10 diagnostiche A1/21 aggiuntive in sola lettura e candidato grezzo paese/profilo;
- `0x07EF`: `4000 → 40,00 %/Hz` con fattore candidato `×0,01`;
- firmware locale **DSP V1.1.72**, **QCPU1 V1.1.54** e **QCPU2 V1.1.54**; FCPU non viene pubblicato senza un registro 1511 locale identificato;
- il precedente candidato non validato del livello di potenza MP3000 resta rimosso;
- ID tecnici in inglese e nomi visualizzati tradotti in tutte le otto lingue.

Le assegnazioni A1/21 non ancora confermate indipendentemente mantengono lo stato: **LIVE DEVICE READ CONFIRMED; CONFIGURATION CHANGE VALIDATION PENDING**.
''',
    },
    "docs/README_NL.md": {
        "version_old": "<strong>1.5.0</strong>",
        "diag_old": "| 🚨 **Diagnostiek** | Omvormeralarmen |",
        "diag_new": "| 🚨 **Diagnostiek** | Omvormeralarm · aantal en namen van actieve alarmen · DSP/QCPU-firmwareversies |",
        "adv_old": "| 🛡️ **Geavanceerd** | Netbeveiligingsdrempels en tijdsdiagnostiek · Omvormertemperatuur · Omgevingstemperatuur omvormer · Vermogensniveau (kandidaat) |",
        "adv_new": "| 🛡️ **Geavanceerd** | Netbeveiligingsdrempels en tijden · 10 extra A1/21-veldvalidatiediagnoses · ruwe land/profielkandidaat · temperaturen |",
        "alarm_old": "**12 functionele koppelingen** zijn gevalideerd",
        "alarm_new": "**12 functionele koppelingen** zijn rechtstreeks op echte hardware waargenomen",
        "section": '''## 🆕 TSUN Local 1.5.1

Versie **1.5.1** bundelt de volledige MP3000-alarminterface uit 1.5.0 en de correcties van beta1 tot en met beta4 in één stabiele release:

- alle **224 MP3000-alarmposities** blijven beschikbaar; 12 functionele koppelingen zijn gebaseerd op directe hardwarewaarnemingen;
- aparte sensor voor **namen van actieve alarmen**, gelokaliseerd voor Home Assistant;
- gecorrigeerde logger-wifi-RSSI-fallback tot `/status.html`;
- 10 extra alleen-lezen A1/21-veldvalidatiediagnoses plus ruwe land/profielkandidaat;
- `0x07EF`: `4000 → 40,00 %/Hz` met kandidaatfactor `×0,01`;
- lokale firmware **DSP V1.1.72**, **QCPU1 V1.1.54** en **QCPU2 V1.1.54**; FCPU wordt niet gepubliceerd zonder geïdentificeerd lokaal 1511-register;
- de eerdere onbevestigde MP3000-vermogensniveaukandidaat blijft verwijderd;
- technische entity-ID’s blijven Engels en zichtbare namen zijn in alle acht talen vertaald.

Voor A1/21-toewijzingen die nog niet onafhankelijk zijn bevestigd blijft de status: **LIVE DEVICE READ CONFIRMED; CONFIGURATION CHANGE VALIDATION PENDING**.
''',
    },
    "docs/README_PL.md": {
        "version_old": "<strong>1.5.0</strong>",
        "diag_old": "| 🚨 **Diagnostyka** | Alarmy falownika |",
        "diag_new": "| 🚨 **Diagnostyka** | Alarm falownika · liczba i nazwy aktywnych alarmów · firmware DSP/QCPU |",
        "adv_old": "| 🛡️ **Zaawansowane** | Progi ochrony sieci i czasy · Temperatura falownika · Temperatura otoczenia falownika · Poziom mocy (kandydat) |",
        "adv_new": "| 🛡️ **Zaawansowane** | Progi i czasy ochrony sieci · 10 dodatkowych diagnostyk A1/21 do walidacji terenowej · surowy kandydat kraj/profil · temperatury |",
        "alarm_old": "**12 powiązań funkcjonalnych** zostało zweryfikowanych",
        "alarm_new": "**12 powiązań funkcjonalnych** zaobserwowano bezpośrednio na rzeczywistym sprzęcie",
        "section": '''## 🆕 TSUN Local 1.5.1

Wersja **1.5.1** łączy pełny interfejs alarmów MP3000 z 1.5.0 oraz poprawki od beta1 do beta4 w jednym stabilnym wydaniu:

- zachowane są wszystkie **224 pozycje alarmów MP3000**; 12 powiązań funkcjonalnych opiera się na bezpośrednich obserwacjach sprzętowych;
- osobny czujnik **nazw aktywnych alarmów**, zlokalizowany w Home Assistant;
- poprawiony odczyt RSSI Wi-Fi loggera z przejściem do `/status.html`;
- 10 dodatkowych diagnostyk A1/21 tylko do odczytu oraz surowy kandydat kraj/profil;
- `0x07EF`: `4000 → 40,00 %/Hz` ze współczynnikiem kandydata `×0,01`;
- lokalne wersje firmware **DSP V1.1.72**, **QCPU1 V1.1.54** i **QCPU2 V1.1.54**; FCPU nie jest publikowany bez zidentyfikowanego lokalnego rejestru 1511;
- wcześniejszy niepotwierdzony kandydat poziomu mocy MP3000 pozostaje usunięty;
- techniczne identyfikatory encji pozostają angielskie, a nazwy wyświetlane są przetłumaczone na wszystkie osiem języków.

Dla mapowań A1/21 bez niezależnego potwierdzenia nadal obowiązuje status: **LIVE DEVICE READ CONFIRMED; CONFIGURATION CHANGE VALIDATION PENDING**.
''',
    },
    "docs/README_ZH.md": {
        "version_old": "<strong>1.5.0</strong>",
        "diag_old": "| 🚨 **诊断** | 逆变器告警 |",
        "diag_new": "| 🚨 **诊断** | 逆变器告警 · 活动告警数量和名称 · DSP/QCPU 固件版本 |",
        "adv_old": "| 🛡️ **高级** | 电网保护阈值与延时 · 逆变器温度 · 逆变器环境温度 · 功率水平（候选） |",
        "adv_new": "| 🛡️ **高级** | 电网保护阈值与延时 · 10 项额外 A1/21 现场验证诊断 · 国家/配置原始候选值 · 温度 |",
        "alarm_old": "已有 **12 个功能对应关系**通过验证",
        "alarm_new": "已有 **12 个功能对应关系**来自真实硬件上的直接观察",
        "section": '''## 🆕 TSUN Local 1.5.1

**1.5.1** 将 1.5.0 的完整 MP3000 告警界面与 beta1 至 beta4 的修正合并为一个稳定版本：

- 保留全部 **224 个 MP3000 告警位置**；其中 12 个功能对应关系来自直接硬件观察；
- 新增独立的**活动告警名称**传感器，并随 Home Assistant 语言本地化；
- 修正 logger Wi-Fi RSSI 回退读取，可继续读取到 `/status.html`；
- 新增 10 项只读 A1/21 现场验证诊断以及国家/配置原始候选值；
- `0x07EF`：`4000 → 40.00 %/Hz`，候选比例为 `×0.01`；
- 本地固件版本 **DSP V1.1.72**、**QCPU1 V1.1.54**、**QCPU2 V1.1.54**；在未找到本地 1511 寄存器前不发布 FCPU；
- 之前未确认的 MP3000 功率水平候选实体保持删除；
- 技术 entity ID 保持英文，显示名称覆盖全部八种语言。

尚未独立确认的 A1/21 语义映射继续使用状态：**LIVE DEVICE READ CONFIRMED; CONFIGURATION CHANGE VALIDATION PENDING**。
''',
    },
}
for path, cfg in localized.items():
    text = read(path)
    text = text.replace(cfg["version_old"], f"<strong>{VERSION}</strong>", 1)
    text = text.replace(cfg["diag_old"], cfg["diag_new"])
    text = text.replace(cfg["adv_old"], cfg["adv_new"])
    text = text.replace(cfg["alarm_old"], cfg["alarm_new"])
    text = text.replace("GEN3 PLUS · **TSOL-MX500**", "GEN3 / GEN3 PLUS · **TSOL-MX500**")
    text = text.replace("### 02B0 · GEN3 PLUS", "### 02B0 · GEN3 / GEN3 PLUS")
    text = text.replace("### 1097 · GEN3 —", "### 1097 · GEN3 / GEN3 PLUS —")
    if "## 🆕 TSUN Local 1.5.1" not in text:
        marker = "\n---\n\n## 🚨"
        if marker not in text:
            raise SystemExit(f"Alarm section marker not found in {path}")
        text = text.replace(marker, "\n---\n\n" + cfg["section"].rstrip() + marker, 1)
    write(path, text)

# Entity reference and field-validation docs promoted from beta wording.
path = "docs/ENTITIES.md"
text = read(path)
text = text.replace("The maximum 1.5.1 MP3000 configuration", "The maximum 1.5.1 MP3000 configuration")
text = text.replace("In 1.5.1-beta.4,", "In 1.5.1,")
text = text.replace("## 1511 field-validation diagnostics — 1.5.1 beta", "## 1511 field-validation diagnostics — 1.5.1")
text = text.replace("12 validated · 84 require control-hardware validation", "12 hardware-observed · 84 require control-hardware validation")
text = text.replace("The 12 validated mappings", "The 12 hardware-observed mappings")
write(path, text)

for path in ("docs/MP3000_FIELD_VALIDATION.md", "docs/PENDING_1.5.1.md"):
    text = read(path)
    text = text.replace("1.5.1 beta", "1.5.1")
    text = text.replace("1.5.1-beta.4", VERSION)
    write(path, text)

# Public website: stable wording, current counts, stable release link.
path = "docs/index.html"
text = read(path)
text = text.replace("🧪 NEW IN 1.5.1 BETA 4", "NEW IN 1.5.1")
text = text.replace("1.5.1 beta: MP3000 field-validation update", "1.5.1: MP3000 field-validation update")
text = text.replace(
    "The 1.5.0 presentation and alarm architecture stay intact. Beta 3 consolidates the MP3000 diagnostics, localized alarm-name entity and logger RSSI fixes.",
    "Version 1.5.1 consolidates the complete MP3000 alarm interface, field-validation diagnostics, localized alarm-name entity, logger RSSI fix and local DSP/QCPU firmware diagnostics.",
)
text = text.replace("What is beta in 1.5.1?", "What is new in 1.5.1?")
text = text.replace("functional names validated", "hardware-observed mappings")
text = text.replace("12 validated positions and 212 pending positions", "12 hardware-observed positions and 212 pending positions")
text = text.replace("<span class=\"number\">12</span><span class=\"label\">functional names validated</span>", "<span class=\"number\">12</span><span class=\"label\">hardware-observed mappings</span>")
write(path, text)

path = "docs/entities.html"
text = read(path)
text = text.replace("Explore 105 TSOL-MP3000 Home Assistant entities", "Explore 108 TSOL-MP3000 Home Assistant entities")
text = text.replace("1.5.1 exposes up to 105 MP3000 Home Assistant entities", "1.5.1 exposes up to 108 MP3000 Home Assistant entities")
text = text.replace("physically verified alarm mappings", "hardware-observed alarm mappings")
text = text.replace("12 verified", "12 observed")
write(path, text)

# Keep website favicon synchronized with the integration brand icon.
brand_icon = COMPONENT / "brand" / "icon.png"
docs_icon = ROOT / "docs" / "icon.png"
docs_icon.write_bytes(brand_icon.read_bytes())

# Stable cumulative changelog entry. Beta sections remain as historical detail.
changelog_path = ROOT / "CHANGELOG.md"
changelog = changelog_path.read_text(encoding="utf-8")
section = f'''## [{VERSION}] - {DATE}

### Added

- Publish the complete MP3000/1511 alarm interface from 1.5.0: all 224 source positions remain covered without creating 224 permanent Home Assistant entities.
- Keep 12 alarm mappings based on direct physical observations for PV input undervoltage and PV DSP faults across PV1–PV6; all other positions remain neutral until independently confirmed.
- Add a dedicated localized `active_alarm_names` sensor while keeping stable A001–A224 identifiers internal/diagnostic.
- Add ten read-only MP3000/TITAN A1/21 field-validation diagnostics plus the raw 1511 country/profile candidate.
- Add local MP3000 firmware sensors for DSP (`V1.1.72`), QCPU1 (`V1.1.54`) and QCPU2 (`V1.1.54`). FCPU remains intentionally unexposed until a local register is identified.

### Fixed

- Fix logger Wi-Fi RSSI fallback so a valid page without RSSI no longer prevents reading `/status.html`.
- Correct MP3000 `0x07EF` raw `4000` to candidate `40.00 %/Hz` (`×0.01`).
- Remove the discarded MP3000 `output_coefficient_candidate` / Power level candidate entity and clean its beta registry entry.
- Keep unknown user-facing alarm text free of internal Axxx codes while retaining those identifiers for diagnostics.

### Changed

- Keep technical entity IDs stable in English and provide display-name coverage in English, French, German, Spanish, Italian, Dutch, Polish and Simplified Chinese.
- Refresh the main README, all seven localized READMEs, technical entity reference, public website and visual entity page for the stable 1.5.1 feature set.
- Keep reactive-mode, GFCI, calibration, anti-reflux/zero-export, reduction-signal and insulation correlations in the research backlog only; they are not promoted to semantic Home Assistant entities without independent validation.
- MP3000 maximum presentation with six detected PV inputs is 108 entities: 59 enabled by default and 49 advanced/disabled by default.

### HACS / branding

- Keep HACS metadata aligned with Home Assistant 2026.3.0 or later.
- Verify local `brand/icon.png`, `brand/icon@2x.png`, `brand/logo.png`, `brand/logo@2x.png` assets and keep the website favicon synchronized with the integration icon.

### Safety

- All inverter diagnostics, alarm data and firmware reads remain local and read-only.
- No inverter configuration, protection-setting, country/profile or control write is added.

'''
if f"## [{VERSION}]" not in changelog:
    marker = "## [1.5.1-beta.4]"
    if marker not in changelog:
        raise SystemExit("beta4 changelog marker not found")
    changelog = changelog.replace(marker, section + marker, 1)
changelog_path.write_text(changelog, encoding="utf-8")

# Final cumulative stable release notes: 1.5.0 + beta1 + beta2 + beta3 + beta4.
release_notes = '''# TSUN Local 1.5.1

TSUN Local 1.5.1 is the stable consolidation of the MP3000 alarm work introduced in 1.5.0 and the complete 1.5.1 beta cycle (beta1 through beta4). The integration remains fully local and read-only.

## Highlights

- **Complete MP3000 alarm interface:** all **224** positions from the fourteen 16-bit alarm words remain covered, counted and visible when active.
- **12 hardware-observed functional mappings** cover low PV input voltage and PV DSP faults for PV1 through PV6. The other positions stay neutral until independently confirmed.
- **Active alarm names** now have a dedicated localized Home Assistant sensor in addition to the inverter-alarm state and active-alarm count.
- **Logger Wi-Fi RSSI fallback fixed:** a valid page without RSSI no longer stops the search before `/status.html`.
- **Ten additional MP3000 A1/21 field-validation diagnostics** plus the raw country/profile candidate are available as read-only advanced diagnostics.
- **MP3000 firmware diagnostics:** DSP `V1.1.72`, QCPU1 `V1.1.54` and QCPU2 `V1.1.54` are decoded from local 1511 words. FCPU is deliberately not guessed.
- **Eight-language coverage** is enforced for entity names and alarm presentation while technical entity IDs remain stable in English.

## MP3000 alarms — from 1.5.0

The 1511/TITAN alarm catalogue covers all 224 source-bit positions without creating a permanent entity for every bit. Home Assistant exposes a compact alarm interface:

- **Inverter alarm** binary sensor;
- **Active alarms** numeric count;
- dedicated **Active alarm names** localized text sensor;
- fourteen complete raw alarm words as advanced diagnostics, disabled by default.

The observed low-solar `0x2000 / 8192` position remains counted and visible. When it is the only non-fault observation, the operating-state sensor reports **Standby — low solar input**. Its exact functional meaning remains under control-hardware validation.

## MP3000 field diagnostics — from beta1

Ten additional A1/21 values are exposed as disabled-by-default field-validation diagnostics. The raw country/profile candidate is exposed from `2000 / 0x07D0`; the France-configured MP3000 reads `8`.

The adjacent `0x07D1 = 80` and `0x07D2 = 80` remain documented as the leading pair for the two 40.0 s connection/reconnection settings with candidate `×0.5 s` scaling, but their individual order is not guessed.

For these semantic field mappings the evidence status remains deliberately explicit:

**LIVE DEVICE READ CONFIRMED; CONFIGURATION CHANGE VALIDATION PENDING**

## Localization and candidate cleanup — from beta2

The unvalidated MP3000/1511 `output_coefficient_candidate` / Power level candidate was removed rather than presented as a semantic entity. Technical entity IDs remain stable in English while display names are covered in:

- English;
- French;
- German;
- Spanish;
- Italian;
- Dutch;
- Polish;
- Simplified Chinese.

Regression tests enforce complete translation-key coverage for all published entities.

## Active alarm presentation and 0x07EF correction — from beta3

A dedicated `active_alarm_names` sensor makes localized alarm text directly visible and usable in Home Assistant. Internal A001–A224 codes stay available for diagnostics instead of being exposed as the primary unknown-alarm wording.

MP3000 `0x07EF` raw `4000` is decoded with candidate factor `×0.01`, giving **40.00 %/Hz**.

## Local DSP/QCPU firmware — from beta4

Three firmware words are now decoded from live local 1511 blocks:

| Entity | Local register | Raw | Display |
|---|---:|---:|---|
| DSP firmware version | `3008 / 0x0BC0` | `0x1172` | `V1.1.72` |
| QCPU1 firmware version | `3622 / 0x0E26` | `0x1154` | `V1.1.54` |
| QCPU2 firmware version | `3822 / 0x0EEE` | `0x1154` | `V1.1.54` |

FCPU remains intentionally absent because no local 1511 register has been identified for it.

## Research kept out of semantic entities

The strongest remaining MP3000 correlations stay documented for research rather than being published as confirmed entities:

- `0x07F1` → reactive-mode candidate (`0x0066`);
- `0x07F2` → GFCI-enable candidate (`1000`);
- `0x07F7 / 0x07F8` → K1/K2 candidate pair (`1024 / 1024`), order unresolved;
- `0x07F9` → K3 candidate (`1003`);
- `0x080D` → anti-current / anti-reflux delay candidate (`10 s`);
- `0x080B–0x080E` → promising anti-reflux / zero-export cluster;
- `0x07ED` → leading overfrequency-reduction enable/signal candidate;
- `0x0809` → unidentified enable/status flag;
- `0x0BD2` → dynamic insulation-measurement candidate, not assigned to Rx/Ry.

No configuration-change validation has promoted these candidates to semantic Home Assistant entities.

## Home Assistant, HACS and public presentation

- Home Assistant **2026.3.0 or later**.
- HACS metadata is validated for the stable release.
- Main README and all seven localized READMEs are refreshed for 1.5.1.
- Technical `ENTITIES.md`, the public website and the visual entity reference are synchronized with **108 maximum MP3000 entities**, **59 enabled by default** and **49 advanced/disabled by default**.
- Local Home Assistant brand assets (`icon.png`, `icon@2x.png`, `logo.png`, `logo@2x.png`) are retained and checked; the website icon is synchronized with the integration icon.

## Compatibility

- **1511 / TITAN:** validated on TSOL-MP3000.
- **02B0 / GEN3 / GEN3 PLUS:** validated on TSOL-MX500.
- **1097 / GEN3 / GEN3 PLUS:** experimental.

## Safety

- All inverter data access remains local and read-only.
- Logger metadata uses local HTTP GET only.
- No inverter configuration, protection-setting, country/profile or control write is added.
- No cloud service or proxy is required in the Home Assistant data path.

---

**Full changelog:** https://github.com/jptstar/tsun-local/blob/main/CHANGELOG.md

**Project:** https://github.com/jptstar/tsun-local

**Website:** https://jptstar.github.io/tsun-local/
'''
write("docs/releases/1.5.1.md", release_notes)

# Stable-version tests and public-site assertions.
path = "tests/test_release_141_field_updates.py"
text = read(path).replace(
    'self.assertEqual(manifest["version"], "1.5.1-beta.4")',
    'self.assertEqual(manifest["version"], "1.5.1")',
)
write(path, text)

path = "tests/test_metadata.py"
text = read(path)
text = text.replace(
    'self.assertIn("1.5.1 beta: MP3000 field-validation update", index)',
    'self.assertIn("1.5.1: MP3000 field-validation update", index)',
)
text = text.replace(
    'self.assertIn("functional names validated", index)',
    'self.assertIn("hardware-observed mappings", index)',
)
text = text.replace(
    'self.assertIn("physically verified alarm mappings", entities)',
    'self.assertIn("hardware-observed alarm mappings", entities)',
)
brand_test = '''\n    def test_brand_assets_and_web_icon_are_synchronized(self) -> None:\n        brand = INTEGRATION / "brand"\n        expected = ("icon.png", "icon@2x.png", "logo.png", "logo@2x.png")\n        for name in expected:\n            data = (brand / name).read_bytes()\n            self.assertTrue(data.startswith(b"\\x89PNG\\r\\n\\x1a\\n"), name)\n            self.assertGreater(len(data), 1024, name)\n        self.assertEqual((brand / "icon.png").read_bytes(), (brand / "logo.png").read_bytes())\n        self.assertEqual((brand / "icon@2x.png").read_bytes(), (brand / "logo@2x.png").read_bytes())\n        self.assertEqual((ROOT / "docs" / "icon.png").read_bytes(), (brand / "icon.png").read_bytes())\n\n'''
if "def test_brand_assets_and_web_icon_are_synchronized" not in text:
    text = text.replace("\n\nif __name__ == \"__main__\":", brand_test + "\nif __name__ == \"__main__\":")
write(path, text)

# Explicit regression for the new firmware entities in all eight languages.
firmware_test = '''from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).parents[1]
COMPONENT = ROOT / "custom_components" / "tsun_local"

EXPECTED = {
    "en.json": ("DSP firmware version", "QCPU1 firmware version", "QCPU2 firmware version"),
    "fr.json": ("Version du firmware DSP", "Version du firmware QCPU1", "Version du firmware QCPU2"),
    "de.json": ("DSP-Firmwareversion", "QCPU1-Firmwareversion", "QCPU2-Firmwareversion"),
    "es.json": ("Versión del firmware DSP", "Versión del firmware QCPU1", "Versión del firmware QCPU2"),
    "it.json": ("Versione firmware DSP", "Versione firmware QCPU1", "Versione firmware QCPU2"),
    "nl.json": ("DSP-firmwareversie", "QCPU1-firmwareversie", "QCPU2-firmwareversie"),
    "pl.json": ("Wersja oprogramowania DSP", "Wersja oprogramowania QCPU1", "Wersja oprogramowania QCPU2"),
    "zh-Hans.json": ("DSP 固件版本", "QCPU1 固件版本", "QCPU2 固件版本"),
}
KEYS = ("dsp_firmware_version", "qcpu1_firmware_version", "qcpu2_firmware_version")


class FirmwareLocalizationTests(unittest.TestCase):
    def test_firmware_entities_have_all_eight_localized_names(self) -> None:
        strings = json.loads((COMPONENT / "strings.json").read_text(encoding="utf-8"))
        sensors = strings["entity"]["sensor"]
        self.assertEqual(tuple(sensors[key]["name"] for key in KEYS), EXPECTED["en.json"])
        for filename, expected in EXPECTED.items():
            translated = json.loads(
                (COMPONENT / "translations" / filename).read_text(encoding="utf-8")
            )["entity"]["sensor"]
            self.assertEqual(tuple(translated[key]["name"] for key in KEYS), expected)

    def test_firmware_entity_ids_remain_stable_english(self) -> None:
        source = (COMPONENT / "sensor.py").read_text(encoding="utf-8")
        for key in KEYS:
            self.assertIn(f'key="{key}"', source)
            self.assertIn(f'suggested_object_id="{key}"', source)
            self.assertIn(f'translation_key="{key}"', source)


if __name__ == "__main__":
    unittest.main()
'''
write("tests/test_firmware_localization.py", firmware_test)

# HACS metadata must remain current and minimal.
hacs = json.loads(read("hacs.json"))
if hacs.get("name") != "TSUN Local" or hacs.get("homeassistant") != "2026.3.0":
    raise SystemExit(f"Unexpected hacs.json: {hacs!r}")

# Final sanity checks before CI.
required_paths = [
    "docs/releases/1.5.1.md",
    "docs/index.html",
    "docs/entities.html",
    "custom_components/tsun_local/brand/icon.png",
    "custom_components/tsun_local/brand/icon@2x.png",
    "custom_components/tsun_local/brand/logo.png",
    "custom_components/tsun_local/brand/logo@2x.png",
]
for path in required_paths:
    if not (ROOT / path).is_file():
        raise SystemExit(f"Missing release asset: {path}")

print("Prepared stable TSUN Local 1.5.1")
