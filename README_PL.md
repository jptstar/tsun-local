# TSUN Local — Lokalna integracja z Home Assistant

[Français](README.md) | [English](README_EN.md) | [Deutsch](README_DE.md) | [Nederlands](README_NL.md) | [Italiano](README_IT.md) | [Español](README_ES.md) | [Polski](README_PL.md) | [简体中文](README_ZH.md)

[![GitHub Release](https://img.shields.io/github/v/release/jptstar/tsun-local)](https://github.com/jptstar/tsun-local/releases)

<p align="center">
  <img src="https://raw.githubusercontent.com/jptstar/tsun-local/main/custom_components/tsun_local/brand/icon@2x.png" width="160" alt="Niezależna ikona TSUN Local">
</p>

> **Projekt nieoficjalny** — Ta niezależna integracja społecznościowa nie jest opracowywana, zatwierdzana ani utrzymywana przez TSUN i nie jest w żaden sposób powiązana z TSUN. TSUN oraz nazwy jego produktów pozostają własnością odpowiednich podmiotów. Prośby o pomoc dotyczącą tej integracji należy kierować do jej autora, a nie do TSUN.

**TSUN Local** integruje zgodne mikrofalowniki TSUN bezpośrednio z Home Assistant przez sieć lokalną, bez serwera pośredniczącego i bez usługi chmurowej. Wersja 1.1.4 obsługuje zweryfikowane na rzeczywistym sprzęcie modele **TSOL-MP3000** i **MX500** oraz inne modele **TITAN**, **GEN3** i **GEN3 PLUS**, które oczekują na weryfikację.

**Autor: Jean-Philippe TESTART (jptstar)**

## Licencja

Copyright © 2026 Jean-Philippe TESTART (jptstar).

Projekt jest rozpowszechniany na licencji **GNU General Public License v3.0 lub nowszej** (`GPL-3.0-or-later`). Wersje zmodyfikowane lub redystrybuowane muszą być zgodne z tą licencją i zachować informacje o prawach autorskich oraz licencji. Zobacz [LICENSE](LICENSE).

Licencja obejmuje wyłącznie tę niezależną implementację. Nie przyznaje żadnych praw do znaków towarowych, logo, oprogramowania ani produktów TSUN. Projekt pozostaje nieoficjalny i niepowiązany z TSUN.

## Wersje

Publikowane wersje mają format `MAJOR.MINOR.PATCH`. HACS korzysta z GitHub Releases do udostępniania aktualizacji. Szczegóły znajdują się w [rejestrze zmian](CHANGELOG.md).

## Zgodność

**Home Assistant 2026.3.0 lub nowszy**

### Legenda

- ✅ Zgodny i zweryfikowany na rzeczywistym sprzęcie
- ❌ Adapter dostępny, oczekuje na weryfikację sprzętową
- ⛔ Obecnie nieobsługiwany

### Mikrofalowniki

| Rodzina | Modele | Status |
|---|---|---|
| TITAN 2250 W–3000 W | **TSOL-MP3000** | ✅ Zweryfikowany |
| TITAN 2250 W–3000 W | **TSOL-MP2250, TSOL-MS3000** | ❌ Oczekuje na weryfikację |
| TITAN 3680 W–6000 W | **MP6000, MP5000, MP4600, MP4000, MP3750, MP3680** | ⛔ Nieobsługiwane |
| GEN3 / GEN3 PLUS | **MS300, MS350, MS400, MS400-D** | ❌ Oczekują na weryfikację |
| GEN3 / GEN3 PLUS | **MS600, MS700, MS800, MS600-D, MS800-D** | ❌ Oczekują na weryfikację |
| GEN3 / GEN3 PLUS | **MS1600, MS1800, MS2000, MS2000-D** | ❌ Oczekują na weryfikację |
| GEN3 / GEN3 PLUS | **MS3000** | ❌ Oczekuje na weryfikację |
| GEN3 / GEN3 PLUS | **MX500** | ✅ Zweryfikowany |
| GEN3 / GEN3 PLUS | **MX450, MX1000** | ❌ Oczekują na weryfikację |
| GEN3 / GEN3 PLUS | **MX3000** | ⛔ Nieobsługiwany |

Adapter GEN3 / GEN3 PLUS dynamicznie wykrywa urządzenia z **1, 2 lub 4 wejściami PV**.

Model **MX3000** nie jest obsługiwany, ponieważ dostępna mapa rejestrów kończy się na PV4, a ten model może mieć dodatkowe wejścia.

### Inne urządzenia

| Typ | Modele | Status |
|---|---|---|
| System magazynowania energii | **DC1000** | ⛔ Nieobsługiwany |
| Inteligentne liczniki | **TSOL-MG3-MS, DDZY422-D2** | ⛔ Nieobsługiwane |

## Instalacja

### Za pomocą HACS

[![Dodaj TSUN Local do HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration)

Lub dodaj ręcznie:

1. W HACS otwórz menu **⋮** w prawym górnym rogu i wybierz **Repozytoria niestandardowe**.
2. Dodaj `https://github.com/jptstar/tsun-local` jako typ **Integracja**.
3. Wybierz **Dodaj**, a następnie otwórz **TSUN Local**.
4. Wybierz **Pobierz** i najnowszą dostępną wersję.
5. Uruchom ponownie Home Assistant.

Jeśli najnowsza wersja nie jest widoczna, otwórz menu repozytorium i wybierz **Aktualizuj informacje**.

### Instalacja ręczna

1. Skopiuj `custom_components/tsun_local` do `/config/custom_components/`.
2. Uruchom ponownie Home Assistant.
3. Otwórz **Ustawienia → Urządzenia i usługi → Dodaj integrację**.
4. Wyszukaj **TSUN Local**.
5. Wprowadź adres IP, port oraz **numer SN wydrukowany na etykiecie mikrofalownika**.

Podczas dodawania wybierz **Wyszukaj w sieci lokalnej** lub **Konfiguracja ręczna**, a następnie **TITAN** dla TSOL-MP3000 albo **GEN3 / GEN3 PLUS** dla MX500. Wprowadź **Monitor SN / Logger SN** z etykiety. Wyszukiwanie sprawdza wyłącznie lokalną sieć IPv4 na porcie 8899 i nie wysyła danych do adresów kandydatów.

## Wiele urządzeń

Do tej samej instalacji Home Assistant można dodać wiele zgodnych mikrofalowników. Dla każdego urządzenia uruchom **Dodaj integrację** i podaj jego adres IP oraz unikalny numer SN. Każda konfiguracja tworzy niezależne urządzenie z własnymi encjami i koordynatorem komunikacji.

## Ustawienia w Home Assistant

W **Ustawienia → Urządzenia i usługi → TSUN Local** otwórz menu odpowiedniego urządzenia:

- **Konfiguruj** ustawia normalny interwał od 10 sekund do 5 minut (domyślnie 30 sekund) oraz interwał offline/nocny od 1 do 60 minut (domyślnie 5 minut);
- **Skonfiguruj ponownie** zmienia adres IP i port TCP bez usuwania encji;
- każde urządzenie ma niezależne interwały odpytywania.

## Działanie lokalne i izolacja od chmury

TSUN Local komunikuje się wyłącznie przez sieć lokalną i nie korzysta z usług chmurowych. Integracja nie zmienia ustawień chmury w oprogramowaniu urządzenia.

Aby uniemożliwić mikrofalownikowi dostęp do Internetu, utwórz w routerze lub zaporze regułę blokującą dostęp WAN, pozostawiając dostęp do sieci lokalnej i DHCP. Home Assistant musi nadal mieć dostęp do adresu IP mikrofalownika przez port TCP **8899**. Po instalacji HACS potrzebuje Internetu wyłącznie do sprawdzania i pobierania aktualizacji.

## Praca nocna

Gdy mikrofalownik przestaje być zasilany, integracja oznacza go jako offline bez powtarzania błędu przy każdym odpytywaniu:

- pomiary chwilowe (napięcie, prąd, moc i częstotliwość) stają się niedostępne, aby nie wyświetlać nieaktualnych wartości;
- dzienne i całkowite liczniki energii pozostają dostępne z ostatnią znaną wartością;
- diagnostyka **Komunikacja** zgłasza stan offline;
- licznik kolejnych błędów komunikacji wraca do zera po wznowieniu komunikacji;
- czas ostatniej udanej komunikacji pozostaje dostępny;
- kolejne próby korzystają ze skonfigurowanego interwału offline/nocnego;
- po pierwszej udanej odpowiedzi rano przywracany jest normalny interwał.

## Czujniki

Integracja tworzy jedno urządzenie z pomiarami AC, 5 pomiarami dla każdego wykrytego wejścia PV, sumą wykrytych mocy DC, 4 czujnikami diagnostycznymi i jednym stanem łączności.

Liczba wejść PV jest dynamiczna: PV1 jest dostępne po pierwszym odczycie; PV2–PV6 dla TITAN lub PV2–PV4 dla GEN3/GEN3 PLUS są dodawane po wykryciu prawidłowego pomiaru lub licznika energii. Wykryte wejście pozostaje zarejestrowane w Home Assistant.
