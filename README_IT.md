# TSUN Local — Integrazione locale per Home Assistant

[Français](README.md) | [English](README_EN.md) | [Deutsch](README_DE.md) | [Nederlands](README_NL.md) | [Italiano](README_IT.md) | [Español](README_ES.md) | [Polski](README_PL.md) | [简体中文](README_ZH.md)

[![GitHub Release](https://img.shields.io/github/v/release/jptstar/tsun-local)](https://github.com/jptstar/tsun-local/releases)

<p align="center">
  <img src="https://raw.githubusercontent.com/jptstar/tsun-local/main/custom_components/tsun_local/brand/icon@2x.png" width="160" alt="Icona indipendente di TSUN Local">
</p>

> **Progetto non ufficiale** — Questa integrazione indipendente della comunità non è sviluppata, approvata o mantenuta da TSUN e non è affiliata a TSUN in alcun modo. TSUN e i nomi dei suoi prodotti restano di proprietà dei rispettivi titolari. Le richieste di assistenza relative a questa integrazione devono essere rivolte all’autore, non a TSUN.

**TSUN Local** integra direttamente in Home Assistant i microinverter TSUN compatibili presenti sulla rete locale, senza proxy né servizi cloud. La versione 1.1.4 supporta **TSOL-MP3000** e **MX500**, convalidati su hardware reale, oltre ad altri modelli **TITAN**, **GEN3** e **GEN3 PLUS** in attesa di convalida.

**Autore: Jean-Philippe TESTART (jptstar)**

## Licenza

Copyright © 2026 Jean-Philippe TESTART (jptstar).

Questo progetto è distribuito con licenza **GNU General Public License v3.0 o successiva** (`GPL-3.0-or-later`). Le versioni modificate o ridistribuite devono rispettare questa licenza e conservare le note di copyright e di licenza. Vedere [LICENSE](LICENSE).

La licenza copre esclusivamente questa implementazione indipendente. Non concede alcun diritto sui marchi, loghi, software o prodotti TSUN. Questo progetto resta non ufficiale e non affiliato a TSUN.

## Versioni

Le versioni pubblicate seguono il formato `MAJOR.MINOR.PATCH`. HACS utilizza le GitHub Releases per proporre gli aggiornamenti. Consultare il [registro delle modifiche](CHANGELOG.md) per i dettagli.

## Compatibilità

**Home Assistant 2026.3.0 o versione successiva**

### Legenda

- ✅ Compatibile e convalidato su hardware reale
- ❌ Adattatore disponibile, convalida hardware in attesa
- ⛔ Attualmente non supportato

### Microinverter

| Famiglia | Modelli | Stato |
|---|---|---|
| TITAN 2250 W–3000 W | **TSOL-MP3000** | ✅ Convalidato |
| TITAN 2250 W–3000 W | **TSOL-MP2250, TSOL-MS3000** | ❌ In attesa di convalida |
| TITAN 3680 W–6000 W | **MP6000, MP5000, MP4600, MP4000, MP3750, MP3680** | ⛔ Non supportato |
| GEN3 / GEN3 PLUS | **MS300, MS350, MS400, MS400-D** | ❌ In attesa di convalida |
| GEN3 / GEN3 PLUS | **MS600, MS700, MS800, MS600-D, MS800-D** | ❌ In attesa di convalida |
| GEN3 / GEN3 PLUS | **MS1600, MS1800, MS2000, MS2000-D** | ❌ In attesa di convalida |
| GEN3 / GEN3 PLUS | **MS3000** | ❌ In attesa di convalida |
| GEN3 / GEN3 PLUS | **MX500** | ✅ Convalidato |
| GEN3 / GEN3 PLUS | **MX450, MX1000** | ❌ In attesa di convalida |
| GEN3 / GEN3 PLUS | **MX3000** | ⛔ Non supportato |

L’adattatore GEN3 / GEN3 PLUS rileva dinamicamente i dispositivi con **1, 2 o 4 ingressi FV**.

Il **MX3000** non è supportato perché la mappa dei registri disponibile termina a PV4, mentre questo modello può avere ingressi aggiuntivi.

### Altri dispositivi

| Tipo | Modelli | Stato |
|---|---|---|
| Sistema di accumulo | **DC1000** | ⛔ Non supportato |
| Contatori intelligenti | **TSOL-MG3-MS, DDZY422-D2** | ⛔ Non supportato |

## Installazione

### Con HACS

[![Aggiungi TSUN Local a HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration)

Oppure aggiungerlo manualmente:

1. In HACS, aprire il menu **⋮** in alto a destra e selezionare **Repository personalizzati**.
2. Aggiungere `https://github.com/jptstar/tsun-local` con tipo **Integrazione**.
3. Selezionare **Aggiungi**, quindi aprire **TSUN Local**.
4. Selezionare **Scarica** e scegliere l’ultima versione disponibile.
5. Riavviare Home Assistant.

Se l’ultima versione non appare, aprire il menu del repository e selezionare **Aggiorna informazioni**.

### Installazione manuale

1. Copiare `custom_components/tsun_local` in `/config/custom_components/`.
2. Riavviare Home Assistant.
3. Aprire **Impostazioni → Dispositivi e servizi → Aggiungi integrazione**.
4. Cercare **TSUN Local**.
5. Inserire l’indirizzo IP, la porta e il **numero di serie (SN) riportato sull’etichetta del microinverter**.

Durante l’aggiunta scegliere **Cerca nella rete locale** o **Configurazione manuale**, quindi selezionare **TITAN** per TSOL-MP3000 oppure **GEN3 / GEN3 PLUS** per MX500. Inserire il **Monitor SN / Logger SN** riportato sull’etichetta. La ricerca controlla soltanto la rete IPv4 locale sulla porta 8899 e non invia dati agli indirizzi candidati.

## Più dispositivi

È possibile aggiungere più microinverter compatibili alla stessa installazione di Home Assistant. Eseguire **Aggiungi integrazione** per ogni dispositivo e inserire il relativo indirizzo IP e SN univoco. Ogni configurazione crea un dispositivo indipendente con le proprie entità e il proprio coordinatore di comunicazione.

## Impostazioni in Home Assistant

In **Impostazioni → Dispositivi e servizi → TSUN Local**, aprire il menu del dispositivo interessato:

- **Configura** imposta l’intervallo normale da 10 secondi a 5 minuti (30 secondi per impostazione predefinita) e l’intervallo offline/notturno da 1 a 60 minuti (5 minuti per impostazione predefinita);
- **Riconfigura** modifica l’indirizzo IP e la porta TCP senza eliminare le entità;
- ogni dispositivo dispone di intervalli di polling indipendenti.

## Funzionamento locale e isolamento dal cloud

TSUN Local comunica esclusivamente sulla rete locale e non utilizza servizi cloud. L’integrazione non modifica le impostazioni cloud del firmware.

Per impedire al microinverter di accedere a Internet, creare nel router o nel firewall una regola che blocchi l’accesso WAN mantenendo l’accesso alla rete locale e al DHCP. Home Assistant deve poter continuare a raggiungere l’indirizzo IP del microinverter sulla porta TCP **8899**. Dopo l’installazione, HACS richiede Internet solo per controllare e scaricare gli aggiornamenti.

## Funzionamento notturno

Quando il microinverter non è più alimentato, l’integrazione lo contrassegna come offline senza ripetere un errore a ogni interrogazione:

- le misure istantanee (tensione, corrente, potenza e frequenza) diventano non disponibili per evitare valori obsoleti;
- i contatori di energia giornaliera e totale restano disponibili con l’ultimo valore noto;
- la diagnostica **Comunicazione** indica lo stato offline;
- il contatore degli errori di comunicazione consecutivi torna a zero quando la comunicazione riprende;
- l’ora dell’ultima comunicazione riuscita resta disponibile;
- i nuovi tentativi utilizzano l’intervallo offline/notturno configurato;
- dopo la prima risposta riuscita del mattino viene ripristinato l’intervallo normale.

## Sensori

L’integrazione crea un unico dispositivo con misure AC, 5 misure per ogni ingresso FV rilevato, la somma delle potenze DC rilevate, 4 sensori diagnostici e uno stato di connettività.

Il numero di ingressi FV è dinamico: PV1 è disponibile dopo la prima lettura; da PV2 a PV6 per TITAN o da PV2 a PV4 per GEN3/GEN3 PLUS vengono aggiunti quando viene rilevata una misura o un contatore di energia valido. Un ingresso rilevato resta registrato in Home Assistant.
