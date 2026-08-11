# TSUN Local — Lokale Home Assistant-integratie

[Français](README.md) | [English](README_EN.md) | [Deutsch](README_DE.md) | [Nederlands](README_NL.md) | [Italiano](README_IT.md) | [Español](README_ES.md) | [Polski](README_PL.md) | [简体中文](README_ZH.md)

[![GitHub Release](https://img.shields.io/github/v/release/jptstar/tsun-local)](https://github.com/jptstar/tsun-local/releases)

<p align="center">
  <img src="https://raw.githubusercontent.com/jptstar/tsun-local/main/custom_components/tsun_local/brand/icon@2x.png" width="160" alt="Onafhankelijk TSUN Local-pictogram">
</p>

> **Onofficieel project** — Deze onafhankelijke community-integratie is niet ontwikkeld, goedgekeurd of onderhouden door TSUN en is op geen enkele wijze aan TSUN verbonden. TSUN en zijn productnamen blijven eigendom van hun respectieve rechthebbenden. Ondersteuningsverzoeken voor deze integratie moeten aan de auteur worden gericht, niet aan TSUN.

**TSUN Local** integreert compatibele TSUN-micro-omvormers rechtstreeks via het lokale netwerk in Home Assistant, zonder proxy of cloudservice. Versie 1.1.4 ondersteunt de op echte hardware gevalideerde **TSOL-MP3000** en **MX500**, plus andere **TITAN**-, **GEN3**- en **GEN3 PLUS**-modellen die nog op validatie wachten.

**Auteur: Jean-Philippe TESTART (jptstar)**

## Licentie

Copyright © 2026 Jean-Philippe TESTART (jptstar).

Dit project wordt verspreid onder de **GNU General Public License v3.0 of later** (`GPL-3.0-or-later`). Gewijzigde of opnieuw verspreide versies moeten aan deze licentie voldoen en de auteursrecht- en licentievermeldingen behouden. Zie [LICENSE](LICENSE).

De licentie dekt uitsluitend deze onafhankelijke implementatie. Zij verleent geen rechten op handelsmerken, logo’s, software of producten van TSUN. Dit project blijft onofficieel en niet verbonden aan TSUN.

## Versies

Gepubliceerde versies volgen `MAJOR.MINOR.PATCH`. HACS gebruikt GitHub Releases om updates aan te bieden. Zie het [wijzigingslogboek](CHANGELOG.md) voor details.

## Compatibiliteit

**Home Assistant 2026.3.0 of nieuwer**

### Legenda

- ✅ Compatibel en gevalideerd op echte hardware
- ❌ Adapter beschikbaar, hardwarevalidatie in afwachting
- ⛔ Momenteel niet ondersteund

### Micro-omvormers

| Familie | Modellen | Status |
|---|---|---|
| TITAN 2250 W–3000 W | **TSOL-MP3000** | ✅ Gevalideerd |
| TITAN 2250 W–3000 W | **TSOL-MP2250, TSOL-MS3000** | ❌ Validatie in afwachting |
| TITAN 3680 W–6000 W | **MP6000, MP5000, MP4600, MP4000, MP3750, MP3680** | ⛔ Niet ondersteund |
| GEN3 / GEN3 PLUS | **MS300, MS350, MS400, MS400-D** | ❌ Validatie in afwachting |
| GEN3 / GEN3 PLUS | **MS600, MS700, MS800, MS600-D, MS800-D** | ❌ Validatie in afwachting |
| GEN3 / GEN3 PLUS | **MS1600, MS1800, MS2000, MS2000-D** | ❌ Validatie in afwachting |
| GEN3 / GEN3 PLUS | **MS3000** | ❌ Validatie in afwachting |
| GEN3 / GEN3 PLUS | **MX500** | ✅ Gevalideerd |
| GEN3 / GEN3 PLUS | **MX450, MX1000** | ❌ Validatie in afwachting |
| GEN3 / GEN3 PLUS | **MX3000** | ⛔ Niet ondersteund |

De GEN3-/GEN3-PLUS-adapter detecteert dynamisch apparaten met **1, 2 of 4 PV-ingangen**.

De **MX3000** wordt niet ondersteund omdat de beschikbare registerkaart bij PV4 eindigt, terwijl dit model meer ingangen kan hebben.

### Andere apparaten

| Type | Modellen | Status |
|---|---|---|
| Opslagsysteem | **DC1000** | ⛔ Niet ondersteund |
| Slimme meters | **TSOL-MG3-MS, DDZY422-D2** | ⛔ Niet ondersteund |

## Installatie

### Met HACS

[![TSUN Local aan HACS toevoegen](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration)

Of handmatig toevoegen:

1. Open in HACS het menu **⋮** rechtsboven en kies **Aangepaste opslagplaatsen**.
2. Voeg `https://github.com/jptstar/tsun-local` toe met type **Integratie**.
3. Selecteer **Toevoegen** en open daarna **TSUN Local**.
4. Selecteer **Downloaden** en kies de nieuwste beschikbare versie.
5. Start Home Assistant opnieuw op.

Als de nieuwste versie niet verschijnt, open dan het menu van de opslagplaats en kies **Informatie bijwerken**.

### Handmatige installatie

1. Kopieer `custom_components/tsun_local` naar `/config/custom_components/`.
2. Start Home Assistant opnieuw op.
3. Open **Instellingen → Apparaten & diensten → Integratie toevoegen**.
4. Zoek naar **TSUN Local**.
5. Voer het IP-adres, de poort en de **Monitor SN / Logger SN op het etiket van de micro-omvormer** in.

Kies bij het toevoegen **Lokaal netwerk doorzoeken** of **Handmatige configuratie** en selecteer vervolgens **TITAN** voor de TSOL-MP3000 of **GEN3 / GEN3 PLUS** voor de MX500. Voer de **Monitor SN / Logger SN** van het etiket in. De zoekfunctie controleert alleen het lokale IPv4-netwerk op poort 8899 en verzendt geen gegevens naar kandidaatadressen.

## Meerdere apparaten

Meerdere compatibele micro-omvormers kunnen aan dezelfde Home Assistant-installatie worden toegevoegd. Voer voor elk apparaat **Integratie toevoegen** uit en geef het IP-adres en unieke SN op. Elke configuratie maakt een onafhankelijk apparaat met eigen entiteiten en een eigen communicatiecoördinator.

## Instellingen in Home Assistant

Open onder **Instellingen → Apparaten & diensten → TSUN Local** het menu van het betreffende apparaat:

- **Configureren** stelt het normale interval in van 10 seconden tot 5 minuten (standaard 30 seconden) en het offline-/nachtinterval van 1 tot 60 minuten (standaard 5 minuten);
- **Opnieuw configureren** wijzigt het IP-adres en de TCP-poort zonder entiteiten te verwijderen;
- elk apparaat heeft onafhankelijke pollingintervallen.

## Lokale werking en cloudisolatie

TSUN Local communiceert uitsluitend via het lokale netwerk en gebruikt geen cloudservice. De integratie wijzigt de cloudinstellingen van de firmware niet.

Om te voorkomen dat de micro-omvormer internet bereikt, maakt u in de router of firewall een regel die WAN-toegang blokkeert maar toegang tot het lokale netwerk en DHCP behoudt. Home Assistant moet het IP-adres van de micro-omvormer via TCP-poort **8899** kunnen blijven bereiken. Na installatie heeft HACS alleen internet nodig om updates te controleren en te downloaden.

## Nachtwerking

Wanneer de micro-omvormer niet meer wordt gevoed, markeert de integratie hem als offline zonder bij elke polling opnieuw een fout te melden:

- actuele metingen (spanning, stroom, vermogen en frequentie) worden niet beschikbaar zodat geen verouderde waarden worden getoond;
- dagelijkse en totale energietellers blijven beschikbaar met hun laatst bekende waarde;
- de diagnose **Communicatie** meldt offline;
- de teller voor opeenvolgende communicatiefouten keert terug naar nul wanneer de communicatie wordt hervat;
- het tijdstip van de laatste geslaagde communicatie blijft beschikbaar;
- nieuwe pogingen gebruiken het ingestelde offline-/nachtinterval;
- na het eerste geslaagde antwoord in de ochtend wordt het normale interval hersteld.

## Sensoren

De integratie maakt één apparaat met AC-metingen, 5 metingen voor elke gedetecteerde PV-ingang, de som van de gedetecteerde DC-vermogens, 4 diagnosesensoren en één verbindingsstatus.

Het aantal PV-ingangen is dynamisch: PV1 is na de eerste uitlezing beschikbaar; PV2 tot PV6 voor TITAN of PV2 tot PV4 voor GEN3/GEN3 PLUS worden toegevoegd zodra een geldige meting of energieteller wordt waargenomen. Een eenmaal gedetecteerde ingang blijft in Home Assistant geregistreerd.
