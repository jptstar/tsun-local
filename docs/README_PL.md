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
<h3 align="center">Twój falownik. Twoja sieć. Twoje dane.</h3>
<p align="center"><strong>Lokalnie. Tylko odczyt. Bez chmury. Bez proxy.</strong></p>
<p align="center">Bezpośredni lokalny dostęp do zgodnych mikrofalowników TSUN w Home Assistant.<br><strong>1.6.0</strong></p>

<p align="center">
  <a href="https://github.com/jptstar/tsun-local/releases"><img alt="GitHub Release" src="https://img.shields.io/github/v/release/jptstar/tsun-local"></a>
  <a href="https://github.com/hacs/integration"><img alt="HACS" src="https://img.shields.io/badge/HACS-Custom-41BDF5"></a>
  <a href="../LICENSE"><img alt="GPL-3.0-or-later" src="https://img.shields.io/badge/License-GPL--3.0--or--later-blue"></a>
</p>


---

## Kompatybilność

**Home Assistant 2026.3.0 lub nowszy.**

| Protokół | Rodzina | Zweryfikowany sprzęt | Status |
|:---:|---|---|:---:|
| **1511** | TITAN | **TSOL-MP3000** | ✅ **Zweryfikowany** |
| **02B0** | GEN3 / GEN3 PLUS | **TSOL-MX500** · **TSOL-MS800** · **Sunology PLAY2** | ✅ **Zweryfikowany** |
| **1097** | GEN3 / GEN3 PLUS | — | 🧪 **Eksperymentalny** |

> [!TIP]
> **Brak modelu na liście nie oznacza braku zgodności.** TSUN Local określa kompatybilność głównie na podstawie wykrytego protokołu lokalnego, a nie tylko nazwy handlowej.

<details>
<summary><strong>Prawdopodobnie kompatybilne modele według protokołu</strong></summary>

- **1511 — Prawdopodobnie kompatybilne:** `TSOL-MP2250` · `TSOL-MS3000` (TITAN)
- **02B0 — Prawdopodobnie kompatybilne:** `TSOL-MX450` · `TSOL-MX800` · `TSOL-MX1000` · `TSOL-MX3000` · `TSOL-MS1600` · `TSOL-MS1800` · `TSOL-MS2000` · odpowiednie warianty `-D`
- **1097 — Prawdopodobnie kompatybilne:** `TSOL-MS300` · `TSOL-MS350` · `TSOL-MS400` · `TSOL-MS600` · `TSOL-MS700` · `TSOL-MS800` · `TSOL-MS3000` · `TSOL-MX3000D`

</details>

📚 **[Walidacja MP3000 / TITAN](MP3000_FIELD_VALIDATION.md)**

📚 **[TSOL-MX500 Home Assistant](https://jptstar.github.io/tsun-local/tsol-mx500-home-assistant.html)** · **[TSOL-MS800 Home Assistant](https://jptstar.github.io/tsun-local/tsol-ms800-home-assistant.html)**

**Nowość w 1.6.0:** **Odczyt adaptacyjny** jest domyślnie włączony i automatycznie dostosowuje interwał przy błędach komunikacji: 20 s normalnie, 30 s po błędzie i 300 s offline/noc.

📚 **[Pełna lista encji](ENTITIES.md)**

<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration">
    <img alt="Dodaj TSUN Local do HACS" src="https://my.home-assistant.io/badges/hacs_repository.svg">
  </a>
</p>

---


## W skrócie

| | Dane udostępniane przez TSUN Local |
|---|---|
| ☀️ **PV** | Napięcie · Prąd · Moc · Energia dzienna · Energia całkowita |
| ⚡ **AC** | Napięcie · Prąd · Częstotliwość · Moc · Energia dzienna · Energia całkowita |
| 🚨 **Diagnostyka** | Aktywne alarmy · Komunikacja · Informacje loggera |
| 🛡️ **Zaawansowane** | Ochrona sieci · Firmware · Diagnostyka falownika · Eksperymentalne dane walidacyjne |
| 🔒 **Bezpieczeństwo** | Tylko odczyt · Brak zapisu konfiguracji do falownika |

📚 **[Pełna lista encji według protokołu](ENTITIES.md)**


---


## 🚨 Alarmy MP3000

TSUN Local obsługuje pełne pole bitowe alarmów MP3000, zachowując kompaktowy interfejs Home Assistant. **Wszystkie 224 pozycje alarmów są zachowane i oceniane po aktywacji.**

**12 powiązań funkcjonalnych zaobserwowanych na sprzęcie** obejmuje niskie napięcie wejściowe PV i błędy DSP dla PV1–PV6. Pozostałe **212 pozycji** zachowuje stabilne neutralne identyfikatory TSUN Local do czasu fizycznej walidacji ich znaczenia.

Home Assistant udostępnia stan **Alarm falownika**, licznik **Aktywne alarmy** i czujnik **Nazwy aktywnych alarmów**. 14 pełnych surowych słów pozostaje dostępnych jako domyślnie wyłączona diagnostyka bez tworzenia 224 stałych encji.


---


> [!TIP]
> Aktywne alarmy są również wyświetlane jako **zlokalizowany czytelny tekst** ze stabilnym kodem pozycji, na przykład `Zbyt niskie napięcie sieci (02B0-A014)`. **Sunology PLAY2** korzysta z tego samego kompaktowego interfejsu alarmów 02B0; cztery surowe słowa ERR pozostają dostępne jako diagnostyka zaawansowana.

## 🛡️ Zaawansowana diagnostyka

Zaawansowane encje są celowo **domyślnie wyłączone**. Zależnie od protokołu obejmują wartości ochrony sieci, firmware, diagnostykę falownika i wybrane eksperymentalne dane walidacyjne.

Aby je włączyć:

**Ustawienia → Urządzenia i usługi → TSUN Local → Urządzenie → Encje → Wyłączone encje**

Eksperymentalne mapowania semantyczne pozostają wyraźnie oznaczone do czasu niezależnej walidacji. Nie zaimplementowano żadnych zapisów konfiguracji do falownika.

📚 **[Dowody walidacji MP3000](MP3000_FIELD_VALIDATION.md)**
📚 **[Pełna lista encji](ENTITIES.md)**


---


## Instalacja

### HACS

<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration">
    <img alt="Dodaj TSUN Local do HACS" src="https://my.home-assistant.io/badges/hacs_repository.svg">
  </a>
</p>

Możesz też dodać `https://github.com/jptstar/tsun-local` przez **HACS → Niestandardowe repozytoria → Integracja**, zainstalować **TSUN Local** i ponownie uruchomić Home Assistant.

### Ręcznie

Skopiuj `custom_components/tsun_local` do `/config/custom_components/`, uruchom ponownie Home Assistant, a następnie dodaj **TSUN Local** w **Ustawienia → Urządzenia i usługi**.


---


## Jak to działa

```text
Falownik TSUN
     │
     │ Sieć lokalna
     ▼
 TSUN Local
     │
     ▼
Home Assistant
```

**Bez chmury w ścieżce danych. Bez proxy. Bez zdalnej usługi runtime. Bez zapisu konfiguracji do falownika.**

Wyłącznie bezpośrednie lokalne odpytywanie.


---


## 🔬 Zweryfikuj inny model TSUN

TSUN Local zawiera samodzielne, bezpieczne dla prywatności i **ściśle tylko do odczytu** narzędzie do zrzutów sprzętowych.

**⬇️ [Pobierz `tsun_dump.py`](https://raw.githubusercontent.com/jptstar/tsun-local/main/tools/tsun_dump.py)**

Wystarczy Python 3.10+.

macOS / Linux:

```bash
cd ~/Downloads
python3 tsun_dump.py --full
```

Windows:

```powershell
py tsun_dump.py --full
```

Narzędzie może wykrywać zgodne loggery TSUN, rozpoznawać obsługiwane rodziny protokołów i tworzyć dla każdego urządzenia bezpieczny dla prywatności zrzut JSON. Nie implementuje żadnej operacji zapisu do falownika.

Dla VLAN, ukierunkowanego wykrywania, porównań przed/po i zaawansowanej walidacji:

📚 **[Przewodnik Hardware Validation Dump Tool](HARDWARE_DUMP.md)**

### Sunology PLAY2

**Sunology PLAY2 został zweryfikowany na rzeczywistym sprzęcie Home Assistant** przez lokalną ścieżkę 02B0 / Solarman V5.

- Automatyczne wykrywanie i standardowa konfiguracja TSUN Local zostały niezależnie potwierdzone.
- Lokalnie i tylko do odczytu: bez chmury i bez zapisu konfiguracji falownika.
- Dokładny wariant sprzętowy MX400/MX450/MX500 pozostaje celowo nieokreślony; rozstrzygający jest wykryty protokół **02B0**.

📚 **[Szczegóły badań PLAY2](PLAY2_LOCAL_RESEARCH.md)** · 🔬 **[Opcjonalny test PLAY2 tylko do odczytu](../tools/tsun_play2_probe.py)**

---


## Przetestuj falownik spoza listy

Jeśli TSUN Local wykryje `1511`, `02B0` lub `1097`, pozostaw integrację uruchomioną i sprawdź wykryte encje.

Najbardziej przydatne informacje to dokładny model, wykryty protokół, wersja firmware, liczba wejść PV i encje zwracające wiarygodne wartości.

> [!TIP]
> **Twój falownik może stać się kolejnym zweryfikowanym modelem.**


---


## Polityka walidacji

TSUN Local oddziela potwierdzoną obsługę sprzętu od eksperymentalnych badań protokołu.

Nazwy funkcjonalne i obsługa modeli są oznaczane jako zweryfikowane dopiero po powtarzalnych testach na rzeczywistym sprzęcie. Wartość zgodna jedynie z oczekiwanym profilem jest dowodem pomocniczym, a nie ostatecznym potwierdzeniem; eksperymentalne mapowania pozostają oznaczone do czasu jednoznacznej niezależnej obserwacji.


---

## Wkład i podziękowania

TSUN Local korzysta z publicznych badań protokołów i niezależnej walidacji sprzętowej. Wymienione zasługi opisują źródła odniesienia i testy; nie oznaczają afiliacji ani poparcia.

- **David Rapan / [`ha-solarman`](https://github.com/davidrapan/ha-solarman)** — niezależne publiczne źródło porównawcze dla wybranych rejestrów Solarman / 02B0.
- **Stefan Allius / [`tsun-gen3-proxy`](https://github.com/s-allius/tsun-gen3-proxy)** — publiczne badania GEN3 / 1097 oraz country/profile używane przy walidacji eksperymentalnej.
- **TheSmartGerman** — test na rzeczywistym sprzęcie, który ujawnił dodatkową rodzinę protokołu 1097.
- **dca31** — niezależna walidacja Sunology PLAY2 przez standardowy przepływ TSUN Local w Home Assistant.
- **Kmotr** — niezależna walidacja TSOL-MS800 z TSUN Local i zanonimizowaną diagnostyką Home Assistant.

📚 **[Pełna lista współtwórców i podziękowań](contributors.html)**

---


## Projekt

> [!IMPORTANT]
> **Nieoficjalny projekt społecznościowy.** TSUN Local jest niezależny i nie jest rozwijany, zatwierdzany, wspierany ani utrzymywany przez TSUN.

Utworzony i utrzymywany przez **Jean-Philippe TESTART · `jptstar`**
*Rozwijany i udostępniany dla zabawy, ciekawości technicznej i społeczności Home Assistant.*


---


## Licencja

Copyright © 2026 Jean-Philippe TESTART (`jptstar`).

Udostępniany na licencji **GNU General Public License v3.0 lub nowszej**. Zobacz [LICENSE](../LICENSE).
