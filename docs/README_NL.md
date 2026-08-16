<p align="center">
  <a href="https://github.com/jptstar/tsun-local/blob/beta-1097/README.md">English</a> ·
  <a href="https://github.com/jptstar/tsun-local/blob/beta-1097/docs/README_FR.md">Français</a> ·
  <a href="https://github.com/jptstar/tsun-local/blob/beta-1097/docs/README_DE.md">Deutsch</a> ·
  <a href="https://github.com/jptstar/tsun-local/blob/beta-1097/docs/README_NL.md">Nederlands</a> ·
  <a href="https://github.com/jptstar/tsun-local/blob/beta-1097/docs/README_IT.md">Italiano</a> ·
  <a href="https://github.com/jptstar/tsun-local/blob/beta-1097/docs/README_ES.md">Español</a> ·
  <a href="https://github.com/jptstar/tsun-local/blob/beta-1097/docs/README_PL.md">Polski</a> ·
  <a href="https://github.com/jptstar/tsun-local/blob/beta-1097/docs/README_ZH.md">简体中文</a>
</p>

<p align="center">
  <img src="../custom_components/tsun_local/brand/icon@2x.png" width="160" alt="TSUN Local">
</p>

<h1 align="center">TSUN Local</h1>
<h3 align="center">Jouw omvormer. Jouw netwerk. Jouw data.</h3>
<p align="center"><strong>Lokaal. Alleen-lezen. Geen cloud. Geen proxy.</strong></p>
<p align="center">Directe lokale toegang tot compatibele TSUN-micro-omvormers in Home Assistant.<br><strong>1.4.0-beta.8</strong></p>

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
| **02B0** | GEN3 PLUS · **TSOL-MX500** | ✅ **Gevalideerd** |
| **1097** | GEN3 | 🧪 **Experimenteel** |

> [!TIP]
> **Niet vermeld betekent niet automatisch niet ondersteund.** Als je omvormer **1511, 02B0 of 1097** gebruikt, kan hij al werken.

<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration">
    <img alt="TSUN Local toevoegen aan HACS" src="https://my.home-assistant.io/badges/hacs_repository.svg">
  </a>
</p>

<p align="center"><strong>Installeer het. Laat TSUN Local het protocol herkennen. Bekijk wat je omvormer beschikbaar stelt.</strong></p>

---

## In één oogopslag

| | Wat TSUN Local beschikbaar stelt |
|---|---|
| ☀️ **PV** | Spanning · Stroom · Vermogen · Dagenergie · Totale energie |
| ⚡ **AC** | Spanning · Stroom · Frequentie · Vermogen · Dagenergie · Totale energie |
| 🚨 **Diagnostiek** | Alarmen · Communicatie · Loggerinformatie |
| 🛡️ **Geavanceerd** | Netbeveiliging · Omvormerdiagnostiek · Standaard uitgeschakeld |
| 🔒 **Veiligheid** | Alleen-lezen · Geen configuratieschrijfbewerkingen naar de omvormer |

---

## Compatibiliteit

**Home Assistant 2026.3.0 of nieuwer.**

> [!NOTE]
> **✅ Gevalideerd** = bevestigd op echte hardware met TSUN Local.  
> **🔎 Waarschijnlijk compatibel** = de protocolfamilie wordt ondersteund, maar dit exacte model is nog niet met TSUN Local gevalideerd.  
> **🧪 Experimenteel** = protocolondersteuning bestaat, maar meer validatie op echte apparaten is nog nodig.

### 1511 · TITAN — ✅ Gevalideerd

**✅ Gevalideerd**  
`TSOL-MP3000`

**🔎 Waarschijnlijk compatibel**  
`TSOL-MP2250` · `TSOL-MS3000` *(TITAN-generatie)*

| | Beschikbare data |
|---|---|
| ☀️ **PV** | Tot 6 ingangen · Spanning · Stroom · Vermogen · Dag- & totale energie |
| ⚡ **AC** | Spanning · Stroom · Frequentie · Vermogen · Dag- & totale energie |
| 🚨 **Diagnostiek** | Omvormeralarmen |
| 🛡️ **Geavanceerd** | Netbeveiligingsdrempels en tijdsdiagnostiek |

### 02B0 · GEN3 PLUS — ✅ Gevalideerd

**✅ Gevalideerd**  
`TSOL-MX500`

**🔎 Waarschijnlijk compatibel**  
`TSOL-MX450` · `TSOL-MX800` · `TSOL-MX1000` · `TSOL-MX3000`  
`TSOL-MS800` · `TSOL-MS1600` · `TSOL-MS1800` · `TSOL-MS2000`  
Overeenkomstige `-D`-varianten kunnen waar van toepassing ook compatibel zijn.

> [!NOTE]
> Publiek GEN3 PLUS-onderzoek koppelt deze apparaten doorgaans aan de serienummerfamilie **Y17 / Y47**. Dat helpt om modellen te onderscheiden waarvan dezelfde naam ook bij oudere GEN3-varianten voorkomt.

| | Beschikbare data |
|---|---|
| ☀️ **PV** | Dynamische detectie van PV-ingangen · Spanning · Stroom · Vermogen · Energie |
| ⚡ **AC** | Spanning · Stroom · Frequentie · Vermogen · Energie |
| 🚨 **Diagnostiek** | Omvormeralarmen |
| 🛡️ **Geavanceerd** | Netbeveiligingsdiagnostiek · Uitgangscoëfficiënt |

### 1097 · GEN3 — 🧪 Experimenteel

**🔎 Waarschijnlijk compatibel**  
`TSOL-MS300` · `TSOL-MS350` · `TSOL-MS400`  
`TSOL-MS600` · `TSOL-MS700` · `TSOL-MS800`  
`TSOL-MS3000`

> [!NOTE]
> Publiek GEN3-onderzoek koppelt deze apparaten doorgaans aan de serienummerfamilie **R17 / R47**. Compatibiliteit met TSUN Local-protocol **1097** blijft experimenteel totdat deze op meer echte hardware is bevestigd.

| | Beschikbare data |
|---|---|
| ☀️ **PV** | Standaard PV-telemetrie |
| ⚡ **AC** | Standaard omvormer-/AC-telemetrie |
| 🚨 **Diagnostiek** | Beschikbare omvormerdiagnostiek |
| 🛡️ **Geavanceerd** | Protocolversie · Omvormerversie · Temperatuur · Isolatie RX/RY · Ruwe land/profielwaarde · Ontwerpvermogen |

> **🔎 Waarschijnlijk compatibel betekent niet gevalideerd.** Het betekent dat TSUN Local de relevante protocolfamilie al implementeert, waardoor het apparaat een sterke compatibiliteitskandidaat is.

---

## 🛡️ Geavanceerde diagnostiek

Geavanceerde entiteiten zijn bewust **standaard uitgeschakeld**. Zo blijft de normale apparaatpagina overzichtelijk terwijl technische informatie beschikbaar blijft wanneer dat nodig is.

Inschakelen:

**Instellingen → Apparaten & diensten → TSUN Local → Apparaat → Entiteiten → Uitgeschakelde entiteiten**

Er zijn geen configuratieschrijfbewerkingen naar de omvormer geïmplementeerd.

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

## Test een ander TSUN-model

Je omvormer hoeft niet hierboven te staan.

Als TSUN Local een van deze protocollen herkent:

```text
1511
02B0
1097
```

laat de integratie draaien en controleer welke entiteiten worden ontdekt.

> [!TIP]
> **Jouw omvormer kan het volgende gevalideerde model worden.** Nuttige feedback bevat het exacte model, het gedetecteerde protocol, het aantal PV-ingangen, de firmwareversie en welke entiteiten plausibele waarden tonen.

---

## TSUN Local 1.4

### Een bredere TSUN Local

Versie 1.4 brengt TSUN Local van afzonderlijke bekende modellen naar **compatibiliteit op protocolfamilieniveau**.

| | |
|---|---|
| 🔌 | **1511 · 02B0 · 1097** |
| 🔍 | Automatische protocolidentificatie |
| ☀️ | Progressieve / dynamische detectie van PV-ingangen |
| 📊 | Uitgebreide lokale telemetrie |
| 🛡️ | Geavanceerde alleen-lezen diagnostiek |
| 🌍 | 8 talen |
| 🧪 | Eenvoudiger testen van nieuwe TSUN-modellen |

---

## Reverse engineering & validatie

De 1511- en 02B0-implementaties worden ontwikkeld via **onafhankelijke lokale protocolanalyse, observatie van echte apparaten en hardwarevalidatie**.

De experimentele 1097-mapping is mede gebaseerd op openbaar protocolonderzoek van **Stefan Allius / `s-allius/tsun-gen3-proxy`** en vervolgens aangepast voor direct lokaal gebruik in TSUN Local.

Compatibiliteitskandidaten worden bewust apart aangeduid van daadwerkelijk gevalideerde hardware.

---

## Project

> [!IMPORTANT]
> **Onofficieel communityproject.** TSUN Local is onafhankelijk en wordt niet ontwikkeld, goedgekeurd, ondersteund of onderhouden door TSUN.

Gemaakt en onderhouden door **Jean-Philippe TESTART · `jptstar`**  
*Gebouwd en gedeeld voor plezier, technische nieuwsgierigheid en de Home Assistant-community.*

---

## Licentie

Copyright © 2026 Jean-Philippe TESTART (`jptstar`).

Uitgebracht onder de **GNU General Public License v3.0 of later**. Zie [LICENSE](../LICENSE).
