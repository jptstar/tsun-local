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
<h3 align="center">Twój falownik. Twoja sieć. Twoje dane.</h3>
<p align="center"><strong>Lokalnie. Tylko odczyt. Bez chmury. Bez proxy.</strong></p>
<p align="center">Bezpośredni lokalny dostęp do zgodnych mikrofalowników TSUN w Home Assistant.<br><strong>1.4.0-beta.8</strong></p>

<p align="center">
  <a href="https://github.com/jptstar/tsun-local/releases"><img alt="GitHub Release" src="https://img.shields.io/github/v/release/jptstar/tsun-local"></a>
  <a href="https://github.com/hacs/integration"><img alt="HACS" src="https://img.shields.io/badge/HACS-Custom-41BDF5"></a>
  <a href="../LICENSE"><img alt="GPL-3.0-or-later" src="https://img.shields.io/badge/License-GPL--3.0--or--later-blue"></a>
</p>

---

## Twój falownik TSUN może już działać

TSUN Local obsługuje **trzy rodziny lokalnych protokołów TSUN**.

| Protokół | Rodzina / zweryfikowany model referencyjny | Status |
|:---:|---|:---:|
| **1511** | TITAN · **TSOL-MP3000** | ✅ **Zweryfikowany** |
| **02B0** | GEN3 PLUS · **TSOL-MX500** | ✅ **Zweryfikowany** |
| **1097** | GEN3 | 🧪 **Eksperymentalny** |

> [!TIP]
> **Brak na liście nie oznacza braku obsługi.** Jeśli falownik korzysta z **1511, 02B0 lub 1097**, może już działać.

<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration">
    <img alt="Dodaj TSUN Local do HACS" src="https://my.home-assistant.io/badges/hacs_repository.svg">
  </a>
</p>

<p align="center"><strong>Zainstaluj. Pozwól TSUN Local rozpoznać protokół. Sprawdź, jakie dane udostępnia falownik.</strong></p>

---

## W skrócie

| | Dane udostępniane przez TSUN Local |
|---|---|
| ☀️ **PV** | Napięcie · Prąd · Moc · Energia dzienna · Energia całkowita |
| ⚡ **AC** | Napięcie · Prąd · Częstotliwość · Moc · Energia dzienna · Energia całkowita |
| 🚨 **Diagnostyka** | Alarmy · Komunikacja · Informacje loggera |
| 🛡️ **Zaawansowane** | Ochrona sieci · Diagnostyka falownika · Domyślnie wyłączone |
| 🔒 **Bezpieczeństwo** | Tylko odczyt · Brak zapisu konfiguracji do falownika |

---

## Kompatybilność

**Home Assistant 2026.3.0 lub nowszy.**

> [!NOTE]
> **✅ Zweryfikowany** = potwierdzony na rzeczywistym sprzęcie z TSUN Local.  
> **🔎 Prawdopodobnie kompatybilny** = rodzina protokołu jest obsługiwana, ale ten konkretny model nie został jeszcze zweryfikowany z TSUN Local.  
> **🧪 Eksperymentalny** = obsługa protokołu istnieje, ale wymaga dalszej walidacji na rzeczywistych urządzeniach.

### 1511 · TITAN — ✅ Zweryfikowany

**✅ Zweryfikowany**  
`TSOL-MP3000`

**🔎 Prawdopodobnie kompatybilny**  
`TSOL-MP2250` · `TSOL-MS3000` *(generacja TITAN)*

| | Dostępne dane |
|---|---|
| ☀️ **PV** | Do 6 wejść · Napięcie · Prąd · Moc · Energia dzienna i całkowita |
| ⚡ **AC** | Napięcie · Prąd · Częstotliwość · Moc · Energia dzienna i całkowita |
| 🚨 **Diagnostyka** | Alarmy falownika |
| 🛡️ **Zaawansowane** | Progi ochrony sieci i diagnostyka czasów |

### 02B0 · GEN3 PLUS — ✅ Zweryfikowany

**✅ Zweryfikowany**  
`TSOL-MX500`

**🔎 Prawdopodobnie kompatybilny**  
`TSOL-MX450` · `TSOL-MX800` · `TSOL-MX1000` · `TSOL-MX3000`  
`TSOL-MS800` · `TSOL-MS1600` · `TSOL-MS1800` · `TSOL-MS2000`  
Odpowiadające warianty `-D` również mogą być kompatybilne, jeśli występują.

> [!NOTE]
> Publiczne badania GEN3 PLUS zwykle wiążą te urządzenia z rodziną numerów seryjnych **Y17 / Y47**. Pomaga to odróżnić modele, których nazwy występują również w starszych wariantach GEN3.

| | Dostępne dane |
|---|---|
| ☀️ **PV** | Dynamiczne wykrywanie wejść PV · Napięcie · Prąd · Moc · Energia |
| ⚡ **AC** | Napięcie · Prąd · Częstotliwość · Moc · Energia |
| 🚨 **Diagnostyka** | Alarmy falownika |
| 🛡️ **Zaawansowane** | Diagnostyka ochrony sieci · Współczynnik wyjściowy |

### 1097 · GEN3 — 🧪 Eksperymentalny

**🔎 Prawdopodobnie kompatybilny**  
`TSOL-MS300` · `TSOL-MS350` · `TSOL-MS400`  
`TSOL-MS600` · `TSOL-MS700` · `TSOL-MS800`  
`TSOL-MS3000`

> [!NOTE]
> Publiczne badania GEN3 zwykle wiążą te urządzenia z rodziną numerów seryjnych **R17 / R47**. Kompatybilność z protokołem **1097** w TSUN Local pozostaje eksperymentalna do czasu potwierdzenia na większej liczbie rzeczywistych urządzeń.

> **Wkład społeczności:** **TheSmartGerman** przyczynił się do obsługi 1097 poprzez testy na rzeczywistym sprzęcie i informacje zwrotne dotyczące kompatybilności.

| | Dostępne dane |
|---|---|
| ☀️ **PV** | Standardowa telemetria PV |
| ⚡ **AC** | Standardowa telemetria falownika / AC |
| 🚨 **Diagnostyka** | Dostępna diagnostyka falownika |
| 🛡️ **Zaawansowane** | Wersja protokołu · Wersja falownika · Temperatura · Izolacja RX/RY · Surowa wartość kraju/profilu · Moc projektowa |

> **🔎 Prawdopodobnie kompatybilny nie oznacza zweryfikowany.** Oznacza to, że TSUN Local implementuje już odpowiednią rodzinę protokołu, więc urządzenie jest dobrym kandydatem do kompatybilności.

---

## 🛡️ Zaawansowana diagnostyka

Zaawansowane encje są celowo **domyślnie wyłączone**. Dzięki temu standardowa strona urządzenia pozostaje przejrzysta, a informacje techniczne są dostępne w razie potrzeby.

Aby je włączyć:

**Ustawienia → Urządzenia i usługi → TSUN Local → Urządzenie → Encje → Wyłączone encje**

Nie zaimplementowano żadnych zapisów konfiguracji do falownika.

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

## Przetestuj inny model TSUN

Twój falownik nie musi znajdować się na powyższej liście.

Jeśli TSUN Local rozpozna jeden z tych protokołów:

```text
1511
02B0
1097
```

pozostaw integrację uruchomioną i sprawdź wykryte encje.

> [!TIP]
> **Twój falownik może zostać kolejnym zweryfikowanym modelem.** Przydatne informacje to dokładny model, wykryty protokół, liczba wejść PV, wersja firmware i encje zwracające wiarygodne wartości.

---

## TSUN Local 1.4

### Szerszy TSUN Local

Wersja 1.4 przenosi TSUN Local z obsługi pojedynczych znanych modeli w stronę **kompatybilności na poziomie rodzin protokołów**.

| | |
|---|---|
| 🔌 | **1511 · 02B0 · 1097** |
| 🔍 | Automatyczne rozpoznawanie protokołu |
| ☀️ | Stopniowe / dynamiczne wykrywanie wejść PV |
| 📊 | Rozszerzona lokalna telemetria |
| 🛡️ | Zaawansowana diagnostyka tylko do odczytu |
| 🌍 | 8 języków |
| 🧪 | Łatwiejsze testowanie nowych modeli TSUN |

---

## Inżynieria wsteczna i walidacja

Implementacje 1511 i 02B0 są rozwijane poprzez **niezależną analizę lokalnego protokołu, obserwację rzeczywistych urządzeń i walidację sprzętową**.

Eksperymentalne mapowanie 1097 wykorzystuje publicznie dostępne badania protokołu **Stefana Alliusa / `s-allius/tsun-gen3-proxy`**, a następnie zostało dostosowane do bezpośredniego lokalnego użycia w TSUN Local.

Kandydaci do kompatybilności są celowo oznaczani oddzielnie od faktycznie zweryfikowanego sprzętu.

---

## Projekt

> [!IMPORTANT]
> **Nieoficjalny projekt społecznościowy.** TSUN Local jest niezależny i nie jest rozwijany, zatwierdzany, wspierany ani utrzymywany przez TSUN.

Autor i opiekun: **Jean-Philippe TESTART · `jptstar`**  
*Tworzony i udostępniany z pasji, ciekawości technicznej i dla społeczności Home Assistant.*

---

## Licencja

Copyright © 2026 Jean-Philippe TESTART (`jptstar`).

Udostępniany na licencji **GNU General Public License v3.0 lub nowszej**. Zobacz [LICENSE](../LICENSE).
