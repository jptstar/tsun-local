from __future__ import annotations

from pathlib import Path
import re

FILES = {
    "README.md": {
        "compat": "Compatibility",
        "ha": "**Home Assistant 2026.3.0 or later.**",
        "headers": ("Protocol", "Family", "Validated hardware", "Status"),
        "validated": "Validated",
        "experimental": "Experimental",
        "tip": "**Not listed does not mean unsupported.** TSUN Local identifies compatibility primarily from the detected local protocol, not only from the commercial model name.",
        "details": "Likely compatible models by protocol",
        "likely": "Likely compatible",
        "new": "**New in 1.5.4:** 02B0 devices can expose inverter firmware, inverter temperature and additional read-only operating diagnostics.",
        "entity": "Full entity reference",
        "entity_link": "docs/ENTITIES.md",
        "play2_title": "Sunology PLAY2",
        "play2_intro": "**Sunology PLAY2 is validated on real Home Assistant hardware** through the local 02B0 / Solarman V5 path.",
        "play2_bullets": [
            "Automatic discovery and normal TSUN Local setup confirmed independently.",
            "Local and read-only: no cloud or inverter configuration writes.",
            "The exact MX400/MX450/MX500 hardware variant remains intentionally unspecified; the detected **02B0** protocol is authoritative.",
        ],
        "play2_details": "PLAY2 research details",
        "play2_details_link": "docs/PLAY2_LOCAL_RESEARCH.md",
        "play2_probe": "Optional read-only PLAY2 probe",
        "play2_probe_link": "tools/tsun_play2_probe.py",
        "contrib_heading": "Contributions & credits",
        "contrib_intro": "TSUN Local benefits from public protocol research and independent hardware testing. These credits describe reference work and validation only; they do not imply affiliation or endorsement.",
        "credits": [
            "**David Rapan / [`ha-solarman`](https://github.com/davidrapan/ha-solarman)** — independent public cross-reference used during selected Solarman / 02B0 register research.",
            "**Stefan Allius / [`tsun-gen3-proxy`](https://github.com/s-allius/tsun-gen3-proxy)** — public GEN3 / 1097 protocol and country/profile research used during experimental validation.",
            "**TheSmartGerman** — real-device testing that revealed the additional 1097 protocol family.",
            "**dca31** — independent Sunology PLAY2 validation through the normal TSUN Local Home Assistant flow.",
        ],
        "full_credits": "Full contributors & credits",
        "full_credits_link": "docs/contributors.html",
        "hacs_alt": "Add TSUN Local to HACS",
    },
    "docs/README_FR.md": {
        "compat": "Compatibilité",
        "ha": "**Home Assistant 2026.3.0 ou version ultérieure.**",
        "headers": ("Protocole", "Famille", "Matériel validé", "Statut"),
        "validated": "Validé",
        "experimental": "Expérimental",
        "tip": "**Un modèle non listé n’est pas forcément incompatible.** TSUN Local se base d’abord sur le protocole local détecté, pas uniquement sur le nom commercial.",
        "details": "Modèles probablement compatibles par protocole",
        "likely": "Probablement compatible",
        "new": "**Nouveau dans la 1.5.4 :** les appareils 02B0 peuvent exposer le firmware de l’onduleur, sa température et des diagnostics de fonctionnement supplémentaires en lecture seule.",
        "entity": "Liste complète des entités",
        "entity_link": "ENTITIES.md",
        "play2_title": "Sunology PLAY2",
        "play2_intro": "**Sunology PLAY2 est validé sur du matériel Home Assistant réel** via le chemin local 02B0 / Solarman V5.",
        "play2_bullets": [
            "Découverte automatique et ajout normal de TSUN Local confirmés indépendamment.",
            "Local et en lecture seule : aucun cloud et aucune écriture de configuration vers l’onduleur.",
            "La variante matérielle exacte MX400/MX450/MX500 reste volontairement non spécifiée ; le protocole **02B0** détecté fait foi.",
        ],
        "play2_details": "Détails de la recherche PLAY2",
        "play2_details_link": "PLAY2_LOCAL_RESEARCH.md",
        "play2_probe": "Sonde PLAY2 optionnelle en lecture seule",
        "play2_probe_link": "../tools/tsun_play2_probe.py",
        "contrib_heading": "Contributions et crédits",
        "contrib_intro": "TSUN Local bénéficie de recherches protocolaires publiques et de validations indépendantes sur matériel réel. Ces crédits décrivent des références et validations ; ils n’impliquent aucune affiliation ni approbation.",
        "credits": [
            "**David Rapan / [`ha-solarman`](https://github.com/davidrapan/ha-solarman)** — référence publique indépendante utilisée pour recouper certains registres Solarman / 02B0.",
            "**Stefan Allius / [`tsun-gen3-proxy`](https://github.com/s-allius/tsun-gen3-proxy)** — recherches publiques GEN3 / 1097 et country/profile utilisées pour la validation expérimentale.",
            "**TheSmartGerman** — test sur matériel réel ayant révélé la famille de protocole 1097.",
            "**dca31** — validation indépendante du Sunology PLAY2 via le parcours Home Assistant normal de TSUN Local.",
        ],
        "full_credits": "Tous les contributeurs et crédits",
        "full_credits_link": "contributors.html",
        "hacs_alt": "Ajouter TSUN Local à HACS",
    },
    "docs/README_DE.md": {
        "compat": "Kompatibilität",
        "ha": "**Home Assistant 2026.3.0 oder neuer.**",
        "headers": ("Protokoll", "Familie", "Validierte Hardware", "Status"),
        "validated": "Validiert",
        "experimental": "Experimentell",
        "tip": "**Nicht aufgeführt bedeutet nicht inkompatibel.** TSUN Local bewertet die Kompatibilität in erster Linie anhand des erkannten lokalen Protokolls und nicht nur anhand des Modellnamens.",
        "details": "Voraussichtlich kompatible Modelle nach Protokoll",
        "likely": "Voraussichtlich kompatibel",
        "new": "**Neu in 1.5.4:** 02B0-Geräte können Wechselrichter-Firmware, Wechselrichtertemperatur und zusätzliche schreibgeschützte Betriebsdiagnosen bereitstellen.",
        "entity": "Vollständige Entitätsreferenz",
        "entity_link": "ENTITIES.md",
        "play2_title": "Sunology PLAY2",
        "play2_intro": "**Sunology PLAY2 wurde auf echter Home-Assistant-Hardware validiert** – über den lokalen 02B0-/Solarman-V5-Pfad.",
        "play2_bullets": [
            "Automatische Erkennung und normaler TSUN-Local-Einrichtungsablauf wurden unabhängig bestätigt.",
            "Lokal und schreibgeschützt: keine Cloud und keine Konfigurationsschreibvorgänge zum Wechselrichter.",
            "Die genaue MX400/MX450/MX500-Hardwarevariante bleibt bewusst offen; maßgeblich ist das erkannte **02B0**-Protokoll.",
        ],
        "play2_details": "PLAY2-Forschungsdetails",
        "play2_details_link": "PLAY2_LOCAL_RESEARCH.md",
        "play2_probe": "Optionaler schreibgeschützter PLAY2-Test",
        "play2_probe_link": "../tools/tsun_play2_probe.py",
        "contrib_heading": "Beiträge und Credits",
        "contrib_intro": "TSUN Local profitiert von öffentlicher Protokollforschung und unabhängigen Hardwaretests. Die Nennung beschreibt Referenzarbeit und Validierung und bedeutet keine Zugehörigkeit oder Empfehlung.",
        "credits": [
            "**David Rapan / [`ha-solarman`](https://github.com/davidrapan/ha-solarman)** — unabhängige öffentliche Referenz für ausgewählte Solarman-/02B0-Register.",
            "**Stefan Allius / [`tsun-gen3-proxy`](https://github.com/s-allius/tsun-gen3-proxy)** — öffentliche GEN3-/1097- und Länder-/Profilforschung für experimentelle Validierung.",
            "**TheSmartGerman** — Realgerätetest, durch den die zusätzliche 1097-Protokollfamilie sichtbar wurde.",
            "**dca31** — unabhängige Sunology-PLAY2-Validierung über den normalen TSUN-Local-Home-Assistant-Ablauf.",
        ],
        "full_credits": "Alle Mitwirkenden und Credits",
        "full_credits_link": "contributors.html",
        "hacs_alt": "TSUN Local zu HACS hinzufügen",
    },
    "docs/README_ES.md": {
        "compat": "Compatibilidad",
        "ha": "**Home Assistant 2026.3.0 o posterior.**",
        "headers": ("Protocolo", "Familia", "Hardware validado", "Estado"),
        "validated": "Validado",
        "experimental": "Experimental",
        "tip": "**Que un modelo no aparezca no significa que sea incompatible.** TSUN Local se basa principalmente en el protocolo local detectado, no solo en el nombre comercial.",
        "details": "Modelos probablemente compatibles por protocolo",
        "likely": "Probablemente compatible",
        "new": "**Nuevo en 1.5.4:** los dispositivos 02B0 pueden exponer firmware y temperatura del inversor, además de diagnósticos de funcionamiento adicionales de solo lectura.",
        "entity": "Referencia completa de entidades",
        "entity_link": "ENTITIES.md",
        "play2_title": "Sunology PLAY2",
        "play2_intro": "**Sunology PLAY2 está validado en hardware Home Assistant real** mediante la ruta local 02B0 / Solarman V5.",
        "play2_bullets": [
            "Detección automática y configuración normal de TSUN Local confirmadas de forma independiente.",
            "Local y de solo lectura: sin nube y sin escrituras de configuración al inversor.",
            "La variante exacta MX400/MX450/MX500 se deja intencionadamente sin especificar; el protocolo **02B0** detectado es la referencia.",
        ],
        "play2_details": "Detalles de investigación PLAY2",
        "play2_details_link": "PLAY2_LOCAL_RESEARCH.md",
        "play2_probe": "Sonda PLAY2 opcional de solo lectura",
        "play2_probe_link": "../tools/tsun_play2_probe.py",
        "contrib_heading": "Contribuciones y créditos",
        "contrib_intro": "TSUN Local se beneficia de investigación pública de protocolos y validación independiente con hardware real. Estos créditos describen referencias y validaciones; no implican afiliación ni respaldo.",
        "credits": [
            "**David Rapan / [`ha-solarman`](https://github.com/davidrapan/ha-solarman)** — referencia pública independiente para contrastar determinados registros Solarman / 02B0.",
            "**Stefan Allius / [`tsun-gen3-proxy`](https://github.com/s-allius/tsun-gen3-proxy)** — investigación pública GEN3 / 1097 y country/profile usada en validación experimental.",
            "**TheSmartGerman** — pruebas con hardware real que revelaron la familia de protocolo 1097.",
            "**dca31** — validación independiente de Sunology PLAY2 mediante el flujo normal de TSUN Local en Home Assistant.",
        ],
        "full_credits": "Todos los colaboradores y créditos",
        "full_credits_link": "contributors.html",
        "hacs_alt": "Añadir TSUN Local a HACS",
    },
    "docs/README_IT.md": {
        "compat": "Compatibilità",
        "ha": "**Home Assistant 2026.3.0 o successivo.**",
        "headers": ("Protocollo", "Famiglia", "Hardware validato", "Stato"),
        "validated": "Validato",
        "experimental": "Sperimentale",
        "tip": "**Un modello non elencato non è necessariamente incompatibile.** TSUN Local si basa soprattutto sul protocollo locale rilevato, non solo sul nome commerciale.",
        "details": "Modelli probabilmente compatibili per protocollo",
        "likely": "Probabilmente compatibile",
        "new": "**Novità in 1.5.4:** i dispositivi 02B0 possono esporre firmware e temperatura dell’inverter, oltre a diagnostica operativa aggiuntiva in sola lettura.",
        "entity": "Riferimento completo delle entità",
        "entity_link": "ENTITIES.md",
        "play2_title": "Sunology PLAY2",
        "play2_intro": "**Sunology PLAY2 è validato su hardware Home Assistant reale** tramite il percorso locale 02B0 / Solarman V5.",
        "play2_bullets": [
            "Rilevamento automatico e normale configurazione TSUN Local confermati in modo indipendente.",
            "Locale e in sola lettura: nessun cloud e nessuna scrittura di configurazione sull’inverter.",
            "La variante hardware esatta MX400/MX450/MX500 resta volutamente non specificata; fa fede il protocollo **02B0** rilevato.",
        ],
        "play2_details": "Dettagli della ricerca PLAY2",
        "play2_details_link": "PLAY2_LOCAL_RESEARCH.md",
        "play2_probe": "Probe PLAY2 opzionale in sola lettura",
        "play2_probe_link": "../tools/tsun_play2_probe.py",
        "contrib_heading": "Contributi e crediti",
        "contrib_intro": "TSUN Local beneficia di ricerca pubblica sui protocolli e di validazione indipendente su hardware reale. I crediti descrivono riferimenti e verifiche e non implicano affiliazione o approvazione.",
        "credits": [
            "**David Rapan / [`ha-solarman`](https://github.com/davidrapan/ha-solarman)** — riferimento pubblico indipendente per il confronto di alcuni registri Solarman / 02B0.",
            "**Stefan Allius / [`tsun-gen3-proxy`](https://github.com/s-allius/tsun-gen3-proxy)** — ricerca pubblica GEN3 / 1097 e country/profile usata nella validazione sperimentale.",
            "**TheSmartGerman** — test su hardware reale che ha fatto emergere la famiglia di protocollo 1097.",
            "**dca31** — validazione indipendente di Sunology PLAY2 tramite il normale flusso TSUN Local in Home Assistant.",
        ],
        "full_credits": "Tutti i contributori e crediti",
        "full_credits_link": "contributors.html",
        "hacs_alt": "Aggiungi TSUN Local a HACS",
    },
    "docs/README_NL.md": {
        "compat": "Compatibiliteit",
        "ha": "**Home Assistant 2026.3.0 of nieuwer.**",
        "headers": ("Protocol", "Familie", "Gevalideerde hardware", "Status"),
        "validated": "Gevalideerd",
        "experimental": "Experimenteel",
        "tip": "**Niet vermeld betekent niet automatisch incompatibel.** TSUN Local baseert compatibiliteit vooral op het gedetecteerde lokale protocol en niet alleen op de commerciële modelnaam.",
        "details": "Waarschijnlijk compatibele modellen per protocol",
        "likely": "Waarschijnlijk compatibel",
        "new": "**Nieuw in 1.5.4:** 02B0-apparaten kunnen omvormerfirmware, omvormertemperatuur en extra alleen-lezen bedrijfsdiagnostiek tonen.",
        "entity": "Volledige entiteitenreferentie",
        "entity_link": "ENTITIES.md",
        "play2_title": "Sunology PLAY2",
        "play2_intro": "**Sunology PLAY2 is gevalideerd op echte Home Assistant-hardware** via het lokale 02B0 / Solarman V5-pad.",
        "play2_bullets": [
            "Automatische detectie en de normale TSUN Local-configuratie zijn onafhankelijk bevestigd.",
            "Lokaal en alleen-lezen: geen cloud en geen configuratieschrijfacties naar de omvormer.",
            "De exacte MX400/MX450/MX500-hardwarevariant blijft bewust ongespecificeerd; het gedetecteerde **02B0**-protocol is leidend.",
        ],
        "play2_details": "PLAY2-onderzoeksdetails",
        "play2_details_link": "PLAY2_LOCAL_RESEARCH.md",
        "play2_probe": "Optionele alleen-lezen PLAY2-probe",
        "play2_probe_link": "../tools/tsun_play2_probe.py",
        "contrib_heading": "Bijdragen en credits",
        "contrib_intro": "TSUN Local profiteert van openbaar protocolonderzoek en onafhankelijke hardwarevalidatie. Deze credits beschrijven referentiewerk en validatie en impliceren geen affiliatie of goedkeuring.",
        "credits": [
            "**David Rapan / [`ha-solarman`](https://github.com/davidrapan/ha-solarman)** — onafhankelijke openbare referentie voor geselecteerd Solarman-/02B0-registeronderzoek.",
            "**Stefan Allius / [`tsun-gen3-proxy`](https://github.com/s-allius/tsun-gen3-proxy)** — openbaar GEN3-/1097- en land-/profielonderzoek voor experimentele validatie.",
            "**TheSmartGerman** — real-hardwaretest waardoor de extra 1097-protocolfamilie werd ontdekt.",
            "**dca31** — onafhankelijke Sunology PLAY2-validatie via de normale TSUN Local Home Assistant-flow.",
        ],
        "full_credits": "Alle bijdragers en credits",
        "full_credits_link": "contributors.html",
        "hacs_alt": "TSUN Local toevoegen aan HACS",
    },
    "docs/README_PL.md": {
        "compat": "Kompatybilność",
        "ha": "**Home Assistant 2026.3.0 lub nowszy.**",
        "headers": ("Protokół", "Rodzina", "Zweryfikowany sprzęt", "Status"),
        "validated": "Zweryfikowany",
        "experimental": "Eksperymentalny",
        "tip": "**Brak modelu na liście nie oznacza braku zgodności.** TSUN Local określa kompatybilność głównie na podstawie wykrytego protokołu lokalnego, a nie tylko nazwy handlowej.",
        "details": "Prawdopodobnie kompatybilne modele według protokołu",
        "likely": "Prawdopodobnie kompatybilne",
        "new": "**Nowość w 1.5.4:** urządzenia 02B0 mogą udostępniać firmware i temperaturę falownika oraz dodatkową diagnostykę operacyjną tylko do odczytu.",
        "entity": "Pełna lista encji",
        "entity_link": "ENTITIES.md",
        "play2_title": "Sunology PLAY2",
        "play2_intro": "**Sunology PLAY2 został zweryfikowany na rzeczywistym sprzęcie Home Assistant** przez lokalną ścieżkę 02B0 / Solarman V5.",
        "play2_bullets": [
            "Automatyczne wykrywanie i standardowa konfiguracja TSUN Local zostały niezależnie potwierdzone.",
            "Lokalnie i tylko do odczytu: bez chmury i bez zapisu konfiguracji falownika.",
            "Dokładny wariant sprzętowy MX400/MX450/MX500 pozostaje celowo nieokreślony; rozstrzygający jest wykryty protokół **02B0**.",
        ],
        "play2_details": "Szczegóły badań PLAY2",
        "play2_details_link": "PLAY2_LOCAL_RESEARCH.md",
        "play2_probe": "Opcjonalny test PLAY2 tylko do odczytu",
        "play2_probe_link": "../tools/tsun_play2_probe.py",
        "contrib_heading": "Wkład i podziękowania",
        "contrib_intro": "TSUN Local korzysta z publicznych badań protokołów i niezależnej walidacji sprzętowej. Wymienione zasługi opisują źródła odniesienia i testy; nie oznaczają afiliacji ani poparcia.",
        "credits": [
            "**David Rapan / [`ha-solarman`](https://github.com/davidrapan/ha-solarman)** — niezależne publiczne źródło porównawcze dla wybranych rejestrów Solarman / 02B0.",
            "**Stefan Allius / [`tsun-gen3-proxy`](https://github.com/s-allius/tsun-gen3-proxy)** — publiczne badania GEN3 / 1097 oraz country/profile używane przy walidacji eksperymentalnej.",
            "**TheSmartGerman** — test na rzeczywistym sprzęcie, który ujawnił dodatkową rodzinę protokołu 1097.",
            "**dca31** — niezależna walidacja Sunology PLAY2 przez standardowy przepływ TSUN Local w Home Assistant.",
        ],
        "full_credits": "Pełna lista współtwórców i podziękowań",
        "full_credits_link": "contributors.html",
        "hacs_alt": "Dodaj TSUN Local do HACS",
    },
    "docs/README_ZH.md": {
        "compat": "兼容性",
        "ha": "**需要 Home Assistant 2026.3.0 或更高版本。**",
        "headers": ("协议", "系列", "已验证硬件", "状态"),
        "validated": "已验证",
        "experimental": "实验性",
        "tip": "**未列出的型号并不代表不兼容。** TSUN Local 主要依据检测到的本地协议判断兼容性，而不是只看商业型号名称。",
        "details": "按协议分类的可能兼容型号",
        "likely": "可能兼容",
        "new": "**1.5.4 新增：**02B0 设备可提供逆变器固件版本、逆变器温度以及更多只读运行诊断。",
        "entity": "完整实体参考",
        "entity_link": "ENTITIES.md",
        "play2_title": "Sunology PLAY2",
        "play2_intro": "**Sunology PLAY2 已在真实 Home Assistant 硬件上完成验证**，使用本地 02B0 / Solarman V5 路径。",
        "play2_bullets": [
            "自动发现和标准 TSUN Local 配置流程已由独立用户确认。",
            "完全本地、只读：不依赖云端，也不会向逆变器写入配置。",
            "具体 MX400/MX450/MX500 硬件变体仍有意不作推断；以检测到的 **02B0** 协议为准。",
        ],
        "play2_details": "PLAY2 研究详情",
        "play2_details_link": "PLAY2_LOCAL_RESEARCH.md",
        "play2_probe": "可选的只读 PLAY2 探测工具",
        "play2_probe_link": "../tools/tsun_play2_probe.py",
        "contrib_heading": "贡献与致谢",
        "contrib_intro": "TSUN Local 受益于公开协议研究和独立真实硬件验证。以下致谢仅说明参考工作和验证来源，不代表任何隶属或官方背书。",
        "credits": [
            "**David Rapan / [`ha-solarman`](https://github.com/davidrapan/ha-solarman)** — 在部分 Solarman / 02B0 寄存器研究中用作独立公开交叉参考。",
            "**Stefan Allius / [`tsun-gen3-proxy`](https://github.com/s-allius/tsun-gen3-proxy)** — 公开的 GEN3 / 1097 与国家/配置文件研究，用于实验性验证。",
            "**TheSmartGerman** — 真实设备测试揭示了额外的 1097 协议系列。",
            "**dca31** — 通过 TSUN Local 的标准 Home Assistant 流程独立验证 Sunology PLAY2。",
        ],
        "full_credits": "完整贡献者与致谢",
        "full_credits_link": "contributors.html",
        "hacs_alt": "将 TSUN Local 添加到 HACS",
    },
}

# Spanish, Italian, Dutch, Polish and Chinese are explicitly covered above.
# Use English wording only if a file not listed here, which should never happen.

LIKELY = {
    "1511": "`TSOL-MP2250` · `TSOL-MS3000` (TITAN)",
    "02B0": "`TSOL-MX450` · `TSOL-MX800` · `TSOL-MX1000` · `TSOL-MX3000` · `TSOL-MS800` · `TSOL-MS1600` · `TSOL-MS1800` · `TSOL-MS2000` · corresponding `-D` variants",
    "1097": "`TSOL-MS300` · `TSOL-MS350` · `TSOL-MS400` · `TSOL-MS600` · `TSOL-MS700` · `TSOL-MS800` · `TSOL-MS3000` · `TSOL-MX3000D`",
}


def compatibility_block(cfg: dict) -> str:
    p, f, h, s = cfg["headers"]
    return f"""## {cfg['compat']}

{cfg['ha']}

| {p} | {f} | {h} | {s} |
|:---:|---|---|:---:|
| **1511** | TITAN | **TSOL-MP3000** | ✅ **{cfg['validated']}** |
| **02B0** | GEN3 / GEN3 PLUS | **TSOL-MX500** · **Sunology PLAY2** | ✅ **{cfg['validated']}** |
| **1097** | GEN3 / GEN3 PLUS | — | 🧪 **{cfg['experimental']}** |

> [!TIP]
> {cfg['tip']}

<details>
<summary><strong>{cfg['details']}</strong></summary>

- **1511 — {cfg['likely']}:** {LIKELY['1511']}
- **02B0 — {cfg['likely']}:** {LIKELY['02B0']}
- **1097 — {cfg['likely']}:** {LIKELY['1097']}

</details>

{cfg['new']}  
📚 **[{cfg['entity']}]({cfg['entity_link']})**

<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration">
    <img alt="{cfg['hacs_alt']}" src="https://my.home-assistant.io/badges/hacs_repository.svg">
  </a>
</p>"""


def play2_block(cfg: dict) -> str:
    bullets = "\n".join(f"- {item}" for item in cfg["play2_bullets"])
    return f"""### {cfg['play2_title']}

{cfg['play2_intro']}

{bullets}

📚 **[{cfg['play2_details']}]({cfg['play2_details_link']})** · 🔬 **[{cfg['play2_probe']}]({cfg['play2_probe_link']})**"""


def contributions_block(cfg: dict) -> str:
    bullets = "\n".join(f"- {item}" for item in cfg["credits"])
    return f"""## {cfg['contrib_heading']}

{cfg['contrib_intro']}

{bullets}

📚 **[{cfg['full_credits']}]({cfg['full_credits_link']})**"""


for name, cfg in FILES.items():
    path = Path(name)
    text = path.read_text(encoding="utf-8")

    # Keep the visible stable version synchronized.
    text, count = re.subn(r"(<br><strong>)\d+\.\d+\.\d+(</strong>)", r"\g<1>1.5.4\g<2>", text, count=1)
    if count != 1 and "<strong>1.5.4</strong>" not in text:
        raise SystemExit(f"{name}: stable version marker not found")

    parts = text.split("\n---\n")
    if len(parts) < 8:
        raise SystemExit(f"{name}: unexpected README section structure ({len(parts)} blocks)")
    if not parts[1].lstrip().startswith("## "):
        raise SystemExit(f"{name}: first content block is not a level-2 section")
    if "02B0" not in parts[3] or "1511" not in parts[3] or "1097" not in parts[3]:
        raise SystemExit(f"{name}: detailed compatibility block not found at expected position")

    # One clean compatibility section instead of a teaser + a second long duplicate.
    parts[1] = compatibility_block(cfg)
    del parts[3]

    # Keep PLAY2 concise in every language; detailed transport research stays in the dedicated doc.
    dump_index = next((i for i, part in enumerate(parts) if "tsun_dump.py" in part), None)
    if dump_index is None:
        raise SystemExit(f"{name}: hardware dump section not found")
    part = parts[dump_index]
    play2 = play2_block(cfg)
    if re.search(r"\n### [^\n]*PLAY2[^\n]*\n", part, flags=re.I):
        part = re.sub(r"\n### [^\n]*PLAY2[^\n]*\n.*\Z", "\n\n" + play2, part, flags=re.I | re.S)
    else:
        part = part.rstrip() + "\n\n" + play2
    parts[dump_index] = part

    # Synchronize visible credits in every README.
    contrib_index = next((i for i, part in enumerate(parts) if "tsun-gen3-proxy" in part and part.lstrip().startswith("## ")), None)
    if contrib_index is None:
        raise SystemExit(f"{name}: contributions block not found")
    parts[contrib_index] = contributions_block(cfg)

    text = "\n---\n".join(parts).rstrip() + "\n"

    # Final consistency checks.
    if text.count("## " + cfg["compat"]) != 1:
        raise SystemExit(f"{name}: compatibility section count is not exactly one")
    for required in ("Sunology PLAY2", "1.5.4", "ha-solarman", "tsun-gen3-proxy", "dca31", "TheSmartGerman"):
        if required not in text:
            raise SystemExit(f"{name}: missing {required}")
    if name == "README.md" and "sensor_list=0x02B0" in text:
        raise SystemExit("README.md: verbose PLAY2 transport implementation detail still present")

    path.write_text(text, encoding="utf-8")
    print(f"refreshed {name}")
