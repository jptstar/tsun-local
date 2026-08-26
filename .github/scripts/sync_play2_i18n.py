from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]

LANG = {
    "docs/README_DE.md": {
        "intro_old": "Direkter lokaler Zugriff auf kompatible TSUN-Mikrowechselrichter in Home Assistant.<br><strong>1.5.1</strong>",
        "intro_new": "Direkter lokaler Zugriff auf kompatible TSUN-Mikrowechselrichter und <strong>Sunology PLAY2</strong> in Home Assistant.<br><strong>1.5.2</strong>",
        "play2": "### ✅ Sunology PLAY2 — validiert\n\nEin echter **Sunology PLAY2** wurde im normalen TSUN-Local-Ablauf in Home Assistant automatisch und schnell erkannt und erfolgreich hinzugefügt. Der bestätigte lokale Pfad ist **LSW5BLE → TCP 8899 → Solarman V5 → 02B0 → Modbus RTU FC03**. Die genaue zugrunde liegende MX400/MX450/MX500-Hardwarevariante wird bewusst nicht geraten; das erkannte lokale Protokoll ist maßgeblich.\n",
        "alarm": "### 🚨 Klartext-Alarme — 1.5.3 Beta\n\nDie **1.5.3 Beta** erweitert die kompakte Alarmoberfläche auf 1511, 02B0 und 1097. Aktive Alarme erscheinen als lokalisierter Klartext mit stabilem Protokoll-/Positionscode, zum Beispiel `Grid undervoltage (02B0-A014)`. Unbekannte Positionen bleiben mit neutraler Bezeichnung sichtbar. Die Rohwörter bleiben als standardmäßig deaktivierte Diagnose erhalten.\n",
        "project_old": "TSUN Local ist unabhängig und wird weder von TSUN entwickelt, genehmigt, unterstützt noch gewartet.",
        "project_new": "TSUN Local ist unabhängig und wird weder von TSUN noch von Sunology entwickelt, genehmigt, unterstützt oder gewartet.",
    },
    "docs/README_ES.md": {
        "intro_old": "Acceso local directo a microinversores TSUN compatibles en Home Assistant.<br><strong>1.5.1</strong>",
        "intro_new": "Acceso local directo a microinversores TSUN compatibles y a <strong>Sunology PLAY2</strong> en Home Assistant.<br><strong>1.5.2</strong>",
        "play2": "### ✅ Sunology PLAY2 — validado\n\nUn **Sunology PLAY2** real fue detectado automática y rápidamente y se añadió correctamente mediante el flujo normal de TSUN Local en Home Assistant. La ruta local confirmada es **LSW5BLE → TCP 8899 → Solarman V5 → 02B0 → Modbus RTU FC03**. No se presupone una variante MX400/MX450/MX500 concreta; el protocolo local detectado es la referencia.\n",
        "alarm": "### 🚨 Alarmas en texto claro — beta 1.5.3\n\nLa **beta 1.5.3** amplía la interfaz compacta de alarmas a 1511, 02B0 y 1097. Las alarmas activas se muestran como texto localizado legible con un código estable de protocolo/posición, por ejemplo `Grid undervoltage (02B0-A014)`. Las posiciones desconocidas siguen visibles con texto neutro y las palabras brutas permanecen disponibles como diagnóstico desactivado por defecto.\n",
        "project_old": "TSUN Local es independiente y no está desarrollado, aprobado, respaldado ni mantenido por TSUN.",
        "project_new": "TSUN Local es independiente y no está desarrollado, aprobado, respaldado ni mantenido por TSUN ni por Sunology.",
    },
    "docs/README_IT.md": {
        "intro_old": "Accesso locale diretto ai microinverter TSUN compatibili in Home Assistant.<br><strong>1.5.1</strong>",
        "intro_new": "Accesso locale diretto ai microinverter TSUN compatibili e a <strong>Sunology PLAY2</strong> in Home Assistant.<br><strong>1.5.2</strong>",
        "play2": "### ✅ Sunology PLAY2 — validato\n\nUn vero **Sunology PLAY2** è stato rilevato automaticamente e rapidamente e aggiunto con successo tramite il normale flusso TSUN Local in Home Assistant. Il percorso locale confermato è **LSW5BLE → TCP 8899 → Solarman V5 → 02B0 → Modbus RTU FC03**. Non viene ipotizzata una specifica variante MX400/MX450/MX500: fa fede il protocollo locale rilevato.\n",
        "alarm": "### 🚨 Allarmi in testo chiaro — beta 1.5.3\n\nLa **beta 1.5.3** estende l'interfaccia compatta degli allarmi a 1511, 02B0 e 1097. Gli allarmi attivi vengono mostrati come testo localizzato leggibile con un codice stabile protocollo/posizione, ad esempio `Grid undervoltage (02B0-A014)`. Le posizioni sconosciute restano visibili con testo neutro e le parole grezze rimangono disponibili come diagnostica disabilitata per impostazione predefinita.\n",
        "project_old": "TSUN Local è indipendente e non è sviluppato, approvato, supportato o mantenuto da TSUN.",
        "project_new": "TSUN Local è indipendente e non è sviluppato, approvato, supportato o mantenuto da TSUN o Sunology.",
    },
    "docs/README_NL.md": {
        "intro_old": "Directe lokale toegang tot compatibele TSUN-micro-omvormers in Home Assistant.<br><strong>1.5.1</strong>",
        "intro_new": "Directe lokale toegang tot compatibele TSUN-micro-omvormers en <strong>Sunology PLAY2</strong> in Home Assistant.<br><strong>1.5.2</strong>",
        "play2": "### ✅ Sunology PLAY2 — gevalideerd\n\nEen echte **Sunology PLAY2** werd automatisch en snel gedetecteerd en succesvol toegevoegd via de normale TSUN Local-flow in Home Assistant. Het bevestigde lokale pad is **LSW5BLE → TCP 8899 → Solarman V5 → 02B0 → Modbus RTU FC03**. Er wordt bewust geen specifieke MX400/MX450/MX500-variant aangenomen; het gedetecteerde lokale protocol is leidend.\n",
        "alarm": "### 🚨 Alarmen in duidelijke tekst — 1.5.3 bèta\n\nDe **1.5.3 bèta** breidt de compacte alarminterface uit naar 1511, 02B0 en 1097. Actieve alarmen verschijnen als gelokaliseerde duidelijke tekst met een stabiele protocol-/positiecode, bijvoorbeeld `Grid undervoltage (02B0-A014)`. Onbekende posities blijven zichtbaar met neutrale tekst en de ruwe woorden blijven beschikbaar als standaard uitgeschakelde diagnose.\n",
        "project_old": "TSUN Local is onafhankelijk en wordt niet ontwikkeld, goedgekeurd, ondersteund of onderhouden door TSUN.",
        "project_new": "TSUN Local is onafhankelijk en wordt niet ontwikkeld, goedgekeurd, ondersteund of onderhouden door TSUN of Sunology.",
    },
    "docs/README_PL.md": {
        "intro_old": "Bezpośredni lokalny dostęp do zgodnych mikroinwerterów TSUN w Home Assistant.<br><strong>1.5.1</strong>",
        "intro_new": "Bezpośredni lokalny dostęp do zgodnych mikroinwerterów TSUN i <strong>Sunology PLAY2</strong> w Home Assistant.<br><strong>1.5.2</strong>",
        "play2": "### ✅ Sunology PLAY2 — zwalidowany\n\nPrawdziwy **Sunology PLAY2** został automatycznie i szybko wykryty oraz poprawnie dodany przez standardowy proces TSUN Local w Home Assistant. Potwierdzona lokalna ścieżka to **LSW5BLE → TCP 8899 → Solarman V5 → 02B0 → Modbus RTU FC03**. Nie zakładamy konkretnego wariantu MX400/MX450/MX500; decydujący jest wykryty lokalny protokół.\n",
        "alarm": "### 🚨 Alarmy w czytelnym tekście — beta 1.5.3\n\n**Beta 1.5.3** rozszerza kompaktowy interfejs alarmów na 1511, 02B0 i 1097. Aktywne alarmy są prezentowane jako zlokalizowany czytelny tekst ze stabilnym kodem protokołu/pozycji, np. `Grid undervoltage (02B0-A014)`. Nieznane pozycje pozostają widoczne z neutralnym opisem, a surowe słowa nadal są dostępne jako domyślnie wyłączona diagnostyka.\n",
        "project_old": "TSUN Local jest niezależny i nie jest rozwijany, zatwierdzany, wspierany ani utrzymywany przez TSUN.",
        "project_new": "TSUN Local jest niezależny i nie jest rozwijany, zatwierdzany, wspierany ani utrzymywany przez TSUN ani Sunology.",
    },
    "docs/README_ZH.md": {
        "intro_old": "在 Home Assistant 中直接本地访问兼容的 TSUN 微型逆变器。<br><strong>1.5.1</strong>",
        "intro_new": "在 Home Assistant 中直接本地访问兼容的 TSUN 微型逆变器和 <strong>Sunology PLAY2</strong>。<br><strong>1.5.2</strong>",
        "play2": "### ✅ Sunology PLAY2 — 已验证\n\n真实 **Sunology PLAY2** 已通过 Home Assistant 中标准 TSUN Local 流程实现自动快速发现并成功添加。确认的本地链路为 **LSW5BLE → TCP 8899 → Solarman V5 → 02B0 → Modbus RTU FC03**。项目不会猜测具体的 MX400/MX450/MX500 内部变体；以检测到的本地协议为准。\n",
        "alarm": "### 🚨 易读文本告警 — 1.5.3 测试版\n\n**1.5.3 测试版**将精简告警界面扩展到 1511、02B0 和 1097。活动告警以本地化易读文本显示，并保留稳定的协议/位置代码，例如 `Grid undervoltage (02B0-A014)`。未知位置仍以中性描述显示，原始告警字继续作为默认禁用的高级诊断保留。\n",
        "project_old": "TSUN Local 是独立项目，并非由 TSUN 开发、批准、认可或维护。",
        "project_new": "TSUN Local 是独立项目，并非由 TSUN 或 Sunology 开发、批准、认可或维护。",
    },
}

for path, cfg in LANG.items():
    p = ROOT / path
    text = p.read_text(encoding="utf-8")
    if cfg["intro_old"] not in text:
        raise SystemExit(f"Missing intro anchor in {path}")
    text = text.replace(cfg["intro_old"], cfg["intro_new"], 1)

    # Promote PLAY2 in the compact protocol table and the detailed 02B0 validated list.
    text = text.replace("**TSOL-MX500**", "**TSOL-MX500 · Sunology PLAY2**", 1)
    text = text.replace("`TSOL-MX500`", "`TSOL-MX500` · `Sunology PLAY2`", 1)

    # Insert the validation note after the existing 02B0 paragraph and before 1097.
    idx = text.find("\n### 1097")
    if idx == -1:
        raise SystemExit(f"Missing 1097 anchor in {path}")
    text = text[:idx] + "\n\n" + cfg["play2"] + text[idx:]

    # Add the beta alarm communication immediately after the existing stable MP3000 alarm section.
    adv = text.find("\n## 🛡️")
    if adv == -1:
        raise SystemExit(f"Missing advanced diagnostics anchor in {path}")
    text = text[:adv] + "\n\n" + cfg["alarm"] + text[adv:]

    if cfg["project_old"] in text:
        text = text.replace(cfg["project_old"], cfg["project_new"], 1)

    if "**dca31**" not in text:
        marker = "- **TheSmartGerman**"
        pos = text.find(marker)
        if pos != -1:
            end = text.find("\n", pos)
            text = text[: end + 1] + "- **dca31** — independent Sunology PLAY2 / Home Assistant validation.\n" + text[end + 1 :]

    p.write_text(text, encoding="utf-8")

# Self-remove together with the one-shot workflow before the final commit.
for relative in (".github/scripts/sync_play2_i18n.py", ".github/workflows/sync-play2-i18n.yml"):
    target = ROOT / relative
    if target.exists():
        target.unlink()
