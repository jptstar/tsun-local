# TSUN Local — Lokalna integracja z Home Assistant

[English](../README.md) | [Français](README_FR.md) | [Deutsch](README_DE.md) | [Nederlands](README_NL.md) | [Italiano](README_IT.md) | [Español](README_ES.md) | [Polski](README_PL.md) | [简体中文](README_ZH.md)

[![GitHub Release](https://img.shields.io/github/v/release/jptstar/tsun-local)](https://github.com/jptstar/tsun-local/releases)

<p align="center">
  <img src="https://raw.githubusercontent.com/jptstar/tsun-local/main/custom_components/tsun_local/brand/icon@2x.png" width="160" alt="Niezależna ikona TSUN Local">
</p>

> **Projekt nieoficjalny** — Ta niezależna integracja społecznościowa nie jest opracowywana, zatwierdzana ani utrzymywana przez TSUN i nie jest w żaden sposób powiązana z TSUN. TSUN oraz nazwy jego produktów pozostają własnością odpowiednich podmiotów. Prośby o pomoc dotyczącą tej integracji należy kierować do jej autora, a nie do TSUN.

**TSUN Local** integruje zgodne mikrofalowniki TSUN bezpośrednio z Home Assistant **przez sieć lokalną, bez serwera pośredniczącego i bez usługi chmurowej**.

Wersja 1.3.1 obsługuje zweryfikowane na rzeczywistym sprzęcie modele **TSOL-MP3000** i **MX500** oraz inne modele **TITAN**, **GEN3** i **GEN3 PLUS**, które oczekują na weryfikację.

**Autor: Jean-Philippe TESTART (jptstar)**

## Charakter projektu i wsparcie

TSUN Local to integracja Home Assistant, którą początkowo opracowałem dla przyjemności i na własny użytek. Ponieważ wielu użytkowników ma trudności z nawiązaniem lokalnego połączenia z mikrofalownikami TITAN, udostępniam ją, aby mogło z niej skorzystać jak najwięcej osób.

Jeśli otrzymam opinie i informacje diagnostyczne dotyczące konkretnych modeli, chętnie poświęcę trochę czasu na poprawę kompatybilności i usuwanie błędów. TSUN Local pozostaje jednak hobby i zajęciem dodatkowym, a nie moją główną działalnością. Dlatego odpowiedzi lub poprawki mogą czasami wymagać trochę czasu.

## Wersje

Publikowane wersje mają format `MAJOR.MINOR.PATCH`. HACS korzysta z GitHub Releases do udostępniania aktualizacji. Szczegóły znajdują się w [rejestrze zmian](../CHANGELOG.md).

## Zgodność

**Home Assistant 2026.3.0 lub nowszy**

### Legenda

- ✅ Zgodny i zweryfikowany na rzeczywistym sprzęcie
- 🧪 Gotowy do testów społeczności — adapter jest dostępny; opinie są mile widziane
- 🔎 Poszukiwane dane sprzętowe — zgodność nie została jeszcze potwierdzona

### Mikrofalowniki

#### TITAN

| Konfiguracja | Modele | Status |
|---|---|---|
| 6-in-1 | **TSOL-MP3000** | ✅ Zweryfikowany |
| 6-in-1 | **TSOL-MP2250, TSOL-MS3000** | 🧪 Poszukiwani testerzy |
| Liczba wejść do ustalenia | **MP6000, MP5000, MP4600, MP4000, MP3750, MP3680** | 🔎 Poszukiwane dane sprzętowe |

#### GEN3 / GEN3 PLUS — seria MX

| Konfiguracja | Modele | Status |
|---|---|---|
| 1-in-1 | **MX500** | ✅ Zweryfikowany |
| 1-in-1 | **MX450, MX400** | 🧪 Poszukiwani testerzy |
| 2-in-1 | **MX1000, MX900, MX800** | 🧪 Poszukiwani testerzy |
| 4-in-1 | **MX2250** | 🧪 Poszukiwani testerzy |
| 6-in-1 | **MX3300, MX3000, MX2700, MX2500, MX2400** | 🔎 Poszukiwane dane sprzętowe |

#### GEN3 / GEN3 PLUS — seria MS

| Konfiguracja | Modele | Status |
|---|---|---|
| 1-in-1 | **MS400, MS350, MS300, MS400-D** | 🧪 Poszukiwani testerzy |
| 2-in-1 | **MS800, MS700, MS600, MS600-D, MS800-D** | 🧪 Poszukiwani testerzy |
| 4-in-1 | **MS2000, MS1800, MS1600, MS2000-D, MS3000** | 🧪 Poszukiwani testerzy |

Wykrywanie wejść PV jest dynamiczne do **6 wejść dla TITAN**. Dla GEN3 / GEN3 PLUS aktualna mapa obejmuje **1, 2 lub 4 wejścia PV**; PV5 i PV6 nie są jeszcze wykrywane.

> **Masz jeden z tych modeli?** Modele oznaczone 🧪 są gotowe do testów społeczności. [Otwórz raport zgodności](https://github.com/jptstar/tsun-local/issues/new), podając dokładny model, wersję oprogramowania i wynik testu. Ukryj pełne numery seryjne oraz prywatne informacje sieciowe.

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
5. Wprowadź adres IP i port. Home Assistant spróbuje automatycznie wykryć **Monitor SN / Logger SN**.

Podczas dodawania wybierz **Wyszukaj w sieci lokalnej** lub **Konfiguracja ręczna**. Home Assistant najpierw odczyta **Monitor SN / Logger SN** z lokalnej strony stanu loggera. Jeśli numer nie jest dostępny, formularz pozwoli ręcznie wprowadzić wartość **Device serial number** ze strony lub etykiety urządzenia. Integracja automatycznie wykrywa obsługiwany protokół lokalny; wybór rodziny urządzenia nie jest wymagany. Wyszukiwanie najpierw wysyła natywne zapytania tylko do odczytu przez UDP/48899 i sprawdza każdą odpowiedź na wybranym porcie TCP. Automatycznie ponownie wykorzystuje także podsieć `/24` każdego wcześniej skonfigurowanego urządzenia TSUN. Dla pierwszego urządzenia w nieznanej routowanej sieci VLAN podaj podsieć raz w notacji CIDR; kolejne wyszukiwania uwzględnią ją automatycznie. Jeśli router blokuje rozgłaszanie między sieciami VLAN, ten pierwszy wpis ręczny może być nadal konieczny.

## Wiele urządzeń

Po dodaniu urządzenia znalezionego przez wyszukiwanie sieciowe Home Assistant automatycznie otwiera nowe wyszukiwanie następnego mikrofalownika. Używa tych samych sieci i portu TCP, ukrywa właśnie skonfigurowany adres i kończy działanie, gdy nie pozostało żadne nieskonfigurowane urządzenie. Każdy mikrofalownik nadal wymaga własnego numeru Monitor SN i tworzy niezależny wpis z własnymi encjami i interwałami.

## Ustawienia w Home Assistant

W **Ustawienia → Urządzenia i usługi → TSUN Local** otwórz menu odpowiedniego urządzenia:

- **Konfiguruj** ustawia normalny interwał od 10 sekund do 5 minut (domyślnie 20 sekund), ponowienie po błędzie od 10 sekund do 5 minut (domyślnie 20 sekund), interwał offline/nocny od 1 do 60 minut (domyślnie 5 minut) oraz próg od 1 do 20 kolejnych błędów (domyślnie 3);
- **Skonfiguruj ponownie** zmienia adres IP i port TCP bez usuwania encji;
- każde urządzenie ma niezależne interwały odpytywania.

## Działanie lokalne i izolacja od chmury

TSUN Local komunikuje się wyłącznie przez sieć lokalną i nie korzysta z usług chmurowych. Integracja nie zmienia ustawień chmury w oprogramowaniu urządzenia.

Aby uniemożliwić mikrofalownikowi dostęp do Internetu, utwórz w routerze lub zaporze regułę blokującą dostęp WAN, pozostawiając dostęp do sieci lokalnej i DHCP. Home Assistant musi nadal mieć dostęp do adresu IP mikrofalownika przez port TCP **8899**. Po instalacji HACS potrzebuje Internetu wyłącznie do sprawdzania i pobierania aktualizacji.

## Praca nocna

Gdy mikrofalownik przestaje być zasilany, integracja oznacza go jako offline bez powtarzania błędu przy każdym odpytywaniu:

Do osiągnięcia konfigurowalnego progu ostatnie wartości pozostają dostępne, a ponowienia używają interwału po błędzie. Po osiągnięciu progu (domyślnie 3 błędy) urządzenie przechodzi offline i używa interwału offline/noc. Pierwsza udana odpowiedź zeruje licznik i przywraca normalny interwał.

- pomiary chwilowe (napięcie, prąd, moc i częstotliwość) stają się niedostępne, aby nie wyświetlać nieaktualnych wartości;
- dzienne i całkowite liczniki energii pozostają dostępne z ostatnią znaną wartością;
- czujnik binarny **Mikrofalownik online** zgłasza stan offline;
- licznik kolejnych błędów komunikacji wraca do zera po wznowieniu komunikacji;
- czas ostatniej udanej komunikacji pozostaje dostępny;
- kolejne próby korzystają ze skonfigurowanego interwału offline/nocnego;
- po pierwszej udanej odpowiedzi rano przywracany jest normalny interwał.

## Czujniki

Integracja tworzy jedno urządzenie z pomiarami AC, 5 pomiarami dla każdego wykrytego wejścia PV, sumą wykrytych mocy DC, 4 diagnostykami komunikacji, czujnikami diagnostycznymi numeru seryjnego mikrofalownika, wersji oprogramowania i adresu MAC loggera oraz binarnym czujnikiem łączności **Mikrofalownik online**.

Liczba wejść PV jest dynamiczna: PV1 jest dostępne po pierwszym odczycie; PV2–PV6 dla TITAN lub PV2–PV4 dla GEN3/GEN3 PLUS są dodawane po wykryciu prawidłowego pomiaru lub licznika energii. Wykryte wejście pozostaje zarejestrowane w Home Assistant.

## Licencja

Copyright © 2026 Jean-Philippe TESTART (jptstar).

Projekt jest rozpowszechniany na licencji **GNU General Public License v3.0 lub nowszej** (GPL-3.0-or-later). Wersje zmodyfikowane lub redystrybuowane muszą być zgodne z tą licencją i zachować informacje o prawach autorskich oraz licencji. Zobacz [LICENSE](https://github.com/jptstar/tsun-local/blob/main/LICENSE).

Licencja obejmuje wyłącznie tę niezależną implementację. Nie przyznaje żadnych praw do znaków towarowych, logo, oprogramowania ani produktów TSUN. Projekt pozostaje nieoficjalny i niepowiązany z TSUN.
