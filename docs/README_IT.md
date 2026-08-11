# TSUN Local — Integrazione locale per Home Assistant

[English](../README.md) | [Français](README_FR.md) | [Deutsch](README_DE.md) | [Nederlands](README_NL.md) | [Italiano](README_IT.md) | [Español](README_ES.md) | [Polski](README_PL.md) | [简体中文](README_ZH.md)

[![GitHub Release](https://img.shields.io/github/v/release/jptstar/tsun-local)](https://github.com/jptstar/tsun-local/releases)

<p align="center">
  <img src="https://raw.githubusercontent.com/jptstar/tsun-local/main/custom_components/tsun_local/brand/icon@2x.png" width="160" alt="Icona indipendente di TSUN Local">
</p>

> **Progetto non ufficiale** — Questa integrazione indipendente della comunità non è sviluppata, approvata o mantenuta da TSUN e non è affiliata a TSUN in alcun modo. TSUN e i nomi dei suoi prodotti restano di proprietà dei rispettivi titolari. Le richieste di assistenza relative a questa integrazione devono essere rivolte all’autore, non a TSUN.

**TSUN Local** integra direttamente in Home Assistant i microinverter TSUN compatibili **attraverso la rete locale, senza proxy né servizi cloud**.

La versione 1.1.8 supporta **TSOL-MP3000** e **MX500**, convalidati su hardware reale, oltre ad altri modelli **TITAN**, **GEN3** e **GEN3 PLUS** in attesa di convalida.

**Autore: Jean-Philippe TESTART (jptstar)**

## Natura del progetto e supporto

TSUN Local è un'integrazione Home Assistant che ho sviluppato inizialmente per passione e per uso personale. Poiché molti utenti hanno difficoltà a stabilire una connessione locale con i microinverter TITAN, la rendo disponibile affinché il maggior numero possibile di persone possa beneficiarne.

Se ricevo feedback e informazioni diagnostiche su modelli specifici, sono disposto a dedicare un po' di tempo a migliorare la compatibilità e correggere i bug. TSUN Local rimane tuttavia un hobby e un'attività secondaria, non la mia attività principale. Le risposte o le correzioni potrebbero quindi talvolta richiedere un po' di tempo.

## Versioni

Le versioni pubblicate seguono il formato `MAJOR.MINOR.PATCH`. HACS utilizza le GitHub Releases per proporre gli aggiornamenti. Consultare il [registro delle modifiche](../CHANGELOG.md) per i dettagli.

## Compatibilità

**Home Assistant 2026.3.0 o versione successiva**

### Legenda

- ✅ Compatibile e convalidato su hardware reale
- 🧪 Pronto per i test della community — adattatore disponibile; feedback benvenuti
- 🔎 Dati hardware richiesti — compatibilità ancora da confermare

### Microinverter

#### TITAN

| Configurazione | Modelli | Stato |
|---|---|---|
| 6-in-1 | **TSOL-MP3000** | ✅ Convalidato |
| 6-in-1 | **TSOL-MP2250, TSOL-MS3000** | 🧪 Cercasi tester |
| Ingressi da determinare | **MP6000, MP5000, MP4600, MP4000, MP3750, MP3680** | 🔎 Cercasi dati hardware |

#### GEN3 / GEN3 PLUS — serie MX

| Configurazione | Modelli | Stato |
|---|---|---|
| 1-in-1 | **MX500** | ✅ Convalidato |
| 1-in-1 | **MX450, MX400** | 🧪 Cercasi tester |
| 2-in-1 | **MX1000, MX900, MX800** | 🧪 Cercasi tester |
| 4-in-1 | **MX2250** | 🧪 Cercasi tester |
| 6-in-1 | **MX3300, MX3000, MX2700, MX2500, MX2400** | 🔎 Cercasi dati hardware |

#### GEN3 / GEN3 PLUS — serie MS

| Configurazione | Modelli | Stato |
|---|---|---|
| 1-in-1 | **MS400, MS350, MS300, MS400-D** | 🧪 Cercasi tester |
| 2-in-1 | **MS800, MS700, MS600, MS600-D, MS800-D** | 🧪 Cercasi tester |
| 4-in-1 | **MS2000, MS1800, MS1600, MS2000-D, MS3000** | 🧪 Cercasi tester |

Il rilevamento PV è dinamico fino a **6 ingressi per TITAN**. Per GEN3 / GEN3 PLUS, la mappa attuale copre **1, 2 o 4 ingressi PV**; PV5 e PV6 non vengono ancora rilevati.

### Altri dispositivi

| Tipo | Modelli | Stato |
|---|---|---|
| Batteria GEN3 PLUS | **TSOL-DC1000** | 🔎 Cercasi dati hardware |
| Contatore intelligente | **TSOL-MG3-MS, DDZY422-D2** | 🔎 Cercasi dati hardware |

> **Possiedi uno di questi modelli?** I modelli contrassegnati con 🧪 sono pronti per i test della community. [Apri una segnalazione di compatibilità](https://github.com/jptstar/tsun-local/issues/new) indicando modello esatto, versione firmware e risultato del test. Oscura i numeri di serie completi e le informazioni private della rete.

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
5. Inserire l’indirizzo IP, la porta e il **Monitor SN / Logger SN riportato sull’etichetta del microinverter**.

Durante l’aggiunta scegliere **Cerca nella rete locale** o **Configurazione manuale**, quindi inserire il **Monitor SN / Logger SN** riportato sull’etichetta. L’integrazione rileva automaticamente il protocollo locale supportato; non è necessario scegliere la famiglia del dispositivo. La ricerca controlla tutte le reti IPv4 attive esposte da Home Assistant sulla porta selezionata e non invia dati applicativi agli indirizzi candidati. Se non viene trovato alcun dispositivo, il modulo consente di inserire una sottorete LAN o VLAN instradata in notazione CIDR.

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

## Licenza

Copyright © 2026 Jean-Philippe TESTART (jptstar).

Questo progetto è distribuito con licenza **GNU General Public License v3.0 o successiva** (GPL-3.0-or-later). Le versioni modificate o ridistribuite devono rispettare questa licenza e conservare le note di copyright e di licenza. Vedere [LICENSE](https://github.com/jptstar/tsun-local/blob/main/LICENSE).

La licenza copre esclusivamente questa implementazione indipendente. Non concede alcun diritto sui marchi, loghi, software o prodotti TSUN. Questo progetto resta non ufficiale e non affiliato a TSUN.
