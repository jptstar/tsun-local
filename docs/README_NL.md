<p align="center">
  <a href="https://github.com/jptstar/tsun-local/blob/main/README.md">English</a> ·
  <a href="https://github.com/jptstar/tsun-local/blob/main/docs/README_FR.md">Français</a> ·
  <a href="https://github.com/jptstar/tsun-local/blob/main/docs/README_DE.md">Deutsch</a> ·
  <a href="https://github.com/jptstar/tsun-local/blob/main/docs/README_NL.md">Nederlands</a> ·
  <a href="https://github.com/jptstar/tsun-local/blob/main/docs/README_IT.md">Italiano</a> ·
  <a href="https://github.com/jptstar/tsun-local/blob/main/docs/README_ES.md">Español</a> ·
  <a href="https://github.com/jptstar/tsun-local/blob/main/docs/README_PL.md">Polski</a> ·
  <a href="https://github.com/jptstar/tsun-local/blob/main/docs/README_ZH.md">简体中文</a>
</p>

<p align="center">
  <img src="../custom_components/tsun_local/brand/icon@2x.png" width="160" alt="TSUN Local">
</p>

<h1 align="center">TSUN Local</h1>
<h3 align="center">Jouw omvormer. Jouw netwerk. Jouw data.</h3>
<p align="center"><strong>Lokaal. Alleen-lezen. Geen cloud. Geen proxy.</strong></p>
<p align="center">Directe lokale toegang tot compatibele TSUN-micro-omvormers in Home Assistant.<br><strong>1.5.1</strong></p>

<p align="center">
  <a href="https://github.com/jptstar/tsun-local/releases"><img alt="GitHub Release" src="https://img.shields.io/github/v/release/jptstar/tsun-local"></a>
  <a href="https://github.com/hacs/integration"><img alt="HACS" src="https://img.shields.io/badge/HACS-Custom-41BDF5"></a>
  <a href="../LICENSE"><img alt="GPL-3.0-or-later" src="https://img.shields.io/badge/License-GPL--3.0--or--later-blue"></a>
</p>

---

## Jouw TSUN-omvormer werkt mogelijk al

TSUN Local ondersteunt **drie lokale TSUN-protocolfamilies**.

| Protocol | Familie / gevalideerde referentie | Status |
|:---:|---|:---:|
| **1511** | TITAN · **TSOL-MP3000** | ✅ **Gevalideerd** |
| **02B0** | GEN3 / GEN3 PLUS · **TSOL-MX500** | ✅ **Gevalideerd** |
| **1097** | GEN3 / GEN3 PLUS | 🧪 **Experimenteel** |

> [!TIP]
> **Niet vermeld betekent niet automatisch niet ondersteund.** Als je omvormer **1511, 02B0 of 1097** gebruikt, kan hij al werken.

<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration">
    <img alt="TSUN Local toevoegen aan HACS" src="https://my.home-assistant.io/badges/hacs_repository.svg">
  </a>
</p>

---

## In één oogopslag

| | Wat TSUN Local beschikbaar stelt |
|---|---|
| ☀️ **PV** | Spanning · Stroom · Vermogen · Dagenergie · Totale energie |
| ⚡ **AC** | Spanning · Stroom · Frequentie · Vermogen · Dagenergie · Totale energie |
| 🚨 **Diagnostiek** | Actieve alarmen · Communicatie · Loggerinformatie |
| 🛡️ **Geavanceerd** | Netbeveiliging · Firmware · Omvormerdiagnostiek · Experimentele veldvalidatiegegevens |
| 🔒 **Veiligheid** | Alleen-lezen · Geen configuratieschrijfbewerkingen naar de omvormer |

📚 **[Volledige entiteitenreferentie per protocol](ENTITIES.md)**

---

## Compatibiliteit

**Home Assistant 2026.3.0 of nieuwer.**

> [!NOTE]
> **✅ Gevalideerd** = bevestigd op echte hardware met TSUN Local.  
> **🔎 Waarschijnlijk compatibel** = de protocolfamilie wordt ondersteund, maar dit exacte model is nog niet gevalideerd.  
> **🧪 Experimenteel** = protocolondersteuning bestaat, maar meer validatie op echte apparaten is nog nodig.

### 1511 · TITAN — ✅ Gevalideerd

**✅ Gevalideerd**  
`TSOL-MP3000`

**🔎 Waarschijnlijk compatibel**  
`TSOL-MP2250` · `TSOL-MS3000` *(TITAN-generatie)*

Tot 6 PV-ingangen, AC/PV-telemetrie, energie, omvormerdiagnostiek, firmwareversies, alarmen en geavanceerde alleen-lezen netdiagnostiek.

📚 **[MP3000 / TITAN veldvalidatiedetails](MP3000_FIELD_VALIDATION.md)**

### 02B0 · GEN3 / GEN3 PLUS — ✅ Gevalideerd

**✅ Gevalideerd**  
`TSOL-MX500`

**🔎 Waarschijnlijk compatibel**  
`TSOL-MX450` · `TSOL-MX800` · `TSOL-MX1000` · `TSOL-MX3000`  
`TSOL-MS800` · `TSOL-MS1600` · `TSOL-MS1800` · `TSOL-MS2000`

Overeenkomstige `-D`-varianten kunnen waar van toepassing ook compatibel zijn.

Dynamische detectie van PV-ingangen, AC/PV-telemetrie, omvormeralarmen en geavanceerde alleen-lezen diagnostiek.

### 1097 · GEN3 / GEN3 PLUS — 🧪 Experimenteel

**🔎 Waarschijnlijk compatibel**  
`TSOL-MS300` · `TSOL-MS350` · `TSOL-MS400`  
`TSOL-MS600` · `TSOL-MS700` · `TSOL-MS800`  
`TSOL-MS3000` · `TSOL-MX3000D`

Protocolondersteuning is geïmplementeerd, maar meer validatie op echte apparaten is nodig.

> [!NOTE]
> Eén commerciële modelnaam kan meerdere hardware- of loggergeneraties omvatten. **Voor TSUN Local is het lokaal gedetecteerde protocol doorslaggevend voor compatibiliteit.**

---

## 🚨 MP3000-alarmen

TSUN Local ondersteunt het volledige MP3000-alarmbitveld en houdt de Home Assistant-interface compact. **Alle 224 alarmposities worden behouden en geëvalueerd wanneer ze actief worden.**

De **12 functionele koppelingen die op hardware zijn waargenomen** omvatten lage PV-ingangsspanning en PV-DSP-fouten voor PV1 tot en met PV6. De overige **212 posities** behouden stabiele neutrale TSUN Local-codes totdat hun functionele betekenis fysiek is gevalideerd.

Home Assistant toont één **Omvormeralarm**, een telling **Actieve alarmen** en een sensor **Namen actieve alarmen**. De 14 volledige ruwe woorden blijven beschikbaar als standaard uitgeschakelde diagnostiek, zonder 224 permanente entiteiten te maken.

---

## 🛡️ Geavanceerde diagnostiek

Geavanceerde entiteiten zijn bewust **standaard uitgeschakeld**. Afhankelijk van het protocol omvatten ze netbeveiligingswaarden, firmware- en omvormerdiagnostiek en geselecteerde experimentele veldvalidatiewaarden.

Inschakelen:

**Instellingen → Apparaten & diensten → TSUN Local → Apparaat → Entiteiten → Uitgeschakelde entiteiten**

Experimentele semantische koppelingen blijven expliciet gemarkeerd totdat ze onafhankelijk zijn gevalideerd. Er zijn geen configuratieschrijfbewerkingen naar de omvormer geïmplementeerd.

📚 **[MP3000 veldvalidatiebewijs](MP3000_FIELD_VALIDATION.md)**  
📚 **[Volledige entiteitenreferentie](ENTITIES.md)**

---

## Installatie

### HACS

<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration">
    <img alt="TSUN Local toevoegen aan HACS" src="https://my.home-assistant.io/badges/hacs_repository.svg">
  </a>
</p>

Of voeg `https://github.com/jptstar/tsun-local` toe via **HACS → Aangepaste repositories → Integratie**, installeer **TSUN Local** en herstart Home Assistant.

### Handmatig

Kopieer `custom_components/tsun_local` naar `/config/custom_components/`, herstart Home Assistant en voeg daarna **TSUN Local** toe via **Instellingen → Apparaten & diensten**.

---

## Hoe het werkt

```text
TSUN-omvormer
     │
     │ Lokaal netwerk
     ▼
 TSUN Local
     │
     ▼
Home Assistant
```

**Geen cloud in het datapad. Geen proxy. Geen externe runtime-service. Geen configuratieschrijfbewerkingen naar de omvormer.**

Alleen directe lokale polling.

---

## 🔬 Een ander TSUN-model valideren

TSUN Local bevat een zelfstandig, privacyvriendelijk en **strikt alleen-lezen** hardware-dumpprogramma.

**⬇️ [`tsun_dump.py` downloaden](https://raw.githubusercontent.com/jptstar/tsun-local/main/tools/tsun_dump.py)**

Python 3.10+ is voldoende.

macOS / Linux:

```bash
cd ~/Downloads
python3 tsun_dump.py --full
```

Windows:

```powershell
py tsun_dump.py --full
```

Het programma kan compatibele TSUN-loggers ontdekken, ondersteunde protocolfamilies herkennen en per apparaat een privacyvriendelijke JSON-dump maken. Er is geen schrijfoperatie naar de omvormer geïmplementeerd.

Voor VLANs, gerichte ontdekking, voor/na-vergelijkingen en geavanceerde validatie:

📚 **[Handleiding Hardware Validation Dump Tool](HARDWARE_DUMP.md)**

---

## Een niet-vermelde omvormer testen

Als TSUN Local `1511`, `02B0` of `1097` detecteert, laat de integratie draaien en controleer de ontdekte entiteiten.

Nuttige feedback bevat het exacte model, het gedetecteerde protocol, de firmwareversie, het aantal PV-ingangen en welke entiteiten plausibele waarden tonen.

> [!TIP]
> **Jouw omvormer kan het volgende gevalideerde model worden.**

---

## Validatiebeleid

TSUN Local scheidt bevestigde hardwareondersteuning van experimenteel protocolonderzoek.

Functionele namen en modelondersteuning worden pas als gevalideerd aangeduid na reproduceerbare controles op echte hardware. Een waarde die alleen bij een verwacht profiel past, geldt als aanwijzing en niet als bewijs; experimentele koppelingen blijven gemarkeerd totdat een onafhankelijke waarneming ze eenduidig onderscheidt.

---

## Bijdragen

TSUN Local profiteert van openbaar protocolonderzoek en communitytests op echte hardware.

- **Stefan Allius / `s-allius/tsun-gen3-proxy`** — openbaar GEN3-/1097-protocolonderzoek als referentie voor geselecteerde experimentele koppelingen.
- **TheSmartGerman** — compatibiliteitsfeedback op echte hardware.

Gedetailleerde herkomst en validatiebewijzen worden bij het relevante protocolonderzoek gedocumenteerd.

---

## Project

> [!IMPORTANT]
> **Onofficieel communityproject.** TSUN Local is onafhankelijk en wordt niet ontwikkeld, goedgekeurd, ondersteund of onderhouden door TSUN.

Gemaakt en onderhouden door **Jean-Philippe TESTART · `jptstar`**  
*Ontwikkeld en gedeeld voor plezier, technische nieuwsgierigheid en de Home Assistant-community.*

---

## Licentie

Copyright © 2026 Jean-Philippe TESTART (`jptstar`).

Uitgegeven onder de **GNU General Public License v3.0 of later**. Zie [LICENSE](../LICENSE).
