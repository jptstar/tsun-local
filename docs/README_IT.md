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
<h3 align="center">Il tuo inverter. La tua rete. I tuoi dati.</h3>
<p align="center"><strong>Locale. Sola lettura. Nessun cloud. Nessun proxy.</strong></p>
<p align="center">Accesso locale diretto ai microinverter TSUN compatibili in Home Assistant.<br><strong>1.5.1</strong></p>

<p align="center">
  <a href="https://github.com/jptstar/tsun-local/releases"><img alt="GitHub Release" src="https://img.shields.io/github/v/release/jptstar/tsun-local"></a>
  <a href="https://github.com/hacs/integration"><img alt="HACS" src="https://img.shields.io/badge/HACS-Custom-41BDF5"></a>
  <a href="../LICENSE"><img alt="GPL-3.0-or-later" src="https://img.shields.io/badge/License-GPL--3.0--or--later-blue"></a>
</p>

---

## Il tuo inverter TSUN potrebbe già funzionare

TSUN Local supporta **tre famiglie di protocolli locali TSUN**.

| Protocollo | Famiglia / riferimento validato | Stato |
|:---:|---|:---:|
| **1511** | TITAN · **TSOL-MP3000** | ✅ **Validato** |
| **02B0** | GEN3 / GEN3 / GEN3 PLUS · **TSOL-MX500** | ✅ **Validato** |
| **1097** | GEN3 / GEN3 PLUS | 🧪 **Sperimentale** |

> [!TIP]
> **Non presente nell’elenco non significa non supportato.** Se il tuo inverter usa **1511, 02B0 o 1097**, potrebbe già funzionare.

<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration">
    <img alt="Aggiungi TSUN Local a HACS" src="https://my.home-assistant.io/badges/hacs_repository.svg">
  </a>
</p>

<p align="center"><strong>Installalo. Lascia che TSUN Local identifichi il protocollo. Scopri cosa espone il tuo inverter.</strong></p>

---

## In breve

| | Cosa espone TSUN Local |
|---|---|
| ☀️ **PV** | Tensione · Corrente · Potenza · Energia giornaliera · Energia totale |
| ⚡ **AC** | Tensione · Corrente · Frequenza · Potenza · Energia giornaliera · Energia totale |
| 🚨 **Diagnostica** | Allarmi · Comunicazione · Informazioni logger |
| 🛡️ **Avanzata** | Protezione rete · Diagnostica inverter · Disattivata per impostazione predefinita |
| 🔒 **Sicurezza** | Sola lettura · Nessuna scrittura di configurazione sull’inverter |

📚 **[Riferimento completo delle entità per protocollo](ENTITIES.md)** — sensori, sensori binari e pulsanti per **1511, 02B0 e 1097**.

---

## Compatibilità

**Home Assistant 2026.3.0 o successivo.**

> [!NOTE]
> **✅ Validato** = confermato su hardware reale con TSUN Local.  
> **🔎 Probabilmente compatibile** = la famiglia di protocollo è supportata, ma questo modello preciso non è ancora stato validato con TSUN Local.  
> **🧪 Sperimentale** = il protocollo è supportato, ma serve ancora una validazione più ampia su dispositivi reali.

### 1511 · TITAN — ✅ Validato

**✅ Validato**  
`TSOL-MP3000`

**🔎 Probabilmente compatibile**  
`TSOL-MP2250` · `TSOL-MS3000` *(generazione TITAN)*

| | Dati disponibili |
|---|---|
| ☀️ **PV** | Fino a 6 ingressi · Tensione · Corrente · Potenza · Energia giornaliera e totale |
| ⚡ **AC** | Tensione · Corrente · Frequenza · Potenza · Energia giornaliera e totale |
| 🚨 **Diagnostica** | Allarme inverter · conteggio e nomi allarmi attivi · firmware DSP/QCPU |
| 🛡️ **Avanzato** | Soglie e tempi di protezione rete · 10 diagnostiche A1/21 aggiuntive di validazione sul campo · candidato grezzo paese/profilo · temperature |

### 02B0 · GEN3 / GEN3 PLUS — ✅ Validato

**✅ Validato**  
`TSOL-MX500`

**🔎 Probabilmente compatibile**  
`TSOL-MX450` · `TSOL-MX800` · `TSOL-MX1000` · `TSOL-MX3000`  
`TSOL-MS800` · `TSOL-MS1600` · `TSOL-MS1800` · `TSOL-MS2000`  
Le corrispondenti varianti `-D` possono essere compatibili dove previste.

> [!NOTE]
> La ricerca pubblica su GEN3 PLUS associa generalmente questi dispositivi alla famiglia di numeri di serie **Y17 / Y47**. Questo aiuta a distinguere i modelli il cui nome esiste anche in vecchie varianti GEN3.

| | Dati disponibili |
|---|---|
| ☀️ **PV** | Rilevamento dinamico degli ingressi PV · Tensione · Corrente · Potenza · Energia |
| ⚡ **AC** | Tensione · Corrente · Frequenza · Potenza · Energia |
| 🚨 **Diagnostica** | Allarmi inverter |
| 🛡️ **Avanzato** | Diagnostica protezione rete · Livello di potenza (%) |

### 1097 · GEN3 / GEN3 PLUS — 🧪 Sperimentale

**🔎 Probabilmente compatibile**  
`TSOL-MS300` · `TSOL-MS350` · `TSOL-MS400`  
`TSOL-MS600` · `TSOL-MS700` · `TSOL-MS800`  
`TSOL-MS3000` · `TSOL-MX3000D`

> [!NOTE]
> La ricerca pubblica su GEN3 associa generalmente questi dispositivi alla famiglia di numeri di serie **R17 / R47**. La compatibilità con il protocollo **1097** di TSUN Local resta sperimentale finché non viene confermata su più hardware reale.

| | Dati disponibili |
|---|---|
| ☀️ **PV** | Telemetria PV standard |
| ⚡ **AC** | Telemetria standard inverter / AC |
| 🚨 **Diagnostica** | Diagnostica inverter disponibile |
| 🛡️ **Avanzato** | Versione protocollo · Versione inverter · Temperatura · Isolamento RX/RY · Livello di potenza (sperimentale) · Valore grezzo paese/profilo · Potenza di progetto |

> **🔎 Probabilmente compatibile non significa validato.** Significa che TSUN Local implementa già la famiglia di protocollo pertinente, rendendo il dispositivo un buon candidato alla compatibilità.

---

## Correzioni dalla validazione sul campo incluse nella 1.4.1

La validazione su hardware reale MP3000 / 1511 e MX500 / 02B0 ha affinato alcuni diagnostici prima della ripubblicazione della 1.4.1:

- i tempi di protezione rete restano nativamente in **secondi**; le vecchie unità automatiche `ms` memorizzate dalle beta vengono migrate a `s`;
- sul MP3000 validato, il bit grezzo `0x2000` (`8192`) osservato all’alba, al tramonto e con irraggiamento molto basso resta visibile, viene conteggiato e segnalato con un codice locale neutro; lo stato mostra **Standby — bassa potenza solare in ingresso** finché il significato esatto non è confermato su hardware di controllo;
- i registri TITAN **3017** e **3028** vengono ora decodificati come **Temperatura inverter** e **Temperatura ambiente inverter** con `raw - 40 °C`; i valori grezzi restano disponibili per la verifica;
- il registro 02B0 `0x202C` viene ora mostrato come **Livello di potenza** con la scala confermata `raw × 100 / 1024` (`1024 = 100 %`);

---

## 🆕 TSUN Local 1.5.1

La versione **1.5.1** riunisce l’interfaccia completa degli allarmi MP3000 della 1.5.0 e le correzioni da beta1 a beta4 in una versione stabile:

- tutte le **224 posizioni di allarme MP3000** restano disponibili; 12 corrispondenze funzionali derivano da osservazioni dirette sull’hardware;
- sensore dedicato per i **nomi degli allarmi attivi**, localizzato in Home Assistant;
- correzione del fallback RSSI Wi-Fi del logger fino a `/status.html`;
- 10 diagnostiche A1/21 aggiuntive in sola lettura e candidato grezzo paese/profilo;
- `0x07EF`: `4000 → 40,00 %/Hz` con fattore candidato `×0,01`;
- firmware locale **DSP V1.1.72**, **QCPU1 V1.1.54** e **QCPU2 V1.1.54**; FCPU non viene pubblicato senza un registro 1511 locale identificato;
- il precedente candidato non validato del livello di potenza MP3000 resta rimosso;
- ID tecnici in inglese e nomi visualizzati tradotti in tutte le otto lingue.

Le assegnazioni A1/21 non ancora confermate indipendentemente mantengono lo stato: **LIVE DEVICE READ CONFIRMED; CONFIGURATION CHANGE VALIDATION PENDING**.
---

## 🚨 Catalogo allarmi MP3000

Tutte le **224 posizioni** delle 14 parole di allarme sono incluse, conteggiate e mostrate quando attive. **12 corrispondenze funzionali** sono state osservate direttamente su hardware reale; le altre **212 posizioni** ricevono un codice TSUN Local neutro e univoco e richiedono una verifica fisica su hardware di controllo adeguato. Nessuna posizione attiva viene scartata. I testi in otto lingue sono formulazioni indipendenti di TSUN Local, non traduzioni del server presentate come ufficiali.

---

## 🛡️ Diagnostica avanzata

Le entità avanzate sono intenzionalmente **disattivate per impostazione predefinita**. In questo modo la pagina normale del dispositivo resta semplice, mentre le informazioni tecniche rimangono disponibili quando servono.

Per abilitarne una:

**Impostazioni → Dispositivi e servizi → TSUN Local → Dispositivo → Entità → Entità disabilitate**

Non sono implementate scritture di configurazione verso l’inverter.

---

## Installazione

### HACS

<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration">
    <img alt="Aggiungi TSUN Local a HACS" src="https://my.home-assistant.io/badges/hacs_repository.svg">
  </a>
</p>

Oppure aggiungi `https://github.com/jptstar/tsun-local` in **HACS → Repository personalizzati → Integrazione**, installa **TSUN Local** e riavvia Home Assistant.

### Manuale

Copia `custom_components/tsun_local` in `/config/custom_components/`, riavvia Home Assistant e aggiungi **TSUN Local** da **Impostazioni → Dispositivi e servizi**.

---

## Come funziona

```text
Inverter TSUN
     │
     │ Rete locale
     ▼
 TSUN Local
     │
     ▼
Home Assistant
```

**Nessun cloud nel percorso dei dati. Nessun proxy. Nessun servizio runtime remoto. Nessuna scrittura di configurazione sull’inverter.**

Solo polling locale diretto.

---

## Prova un altro modello TSUN

Il tuo inverter non deve necessariamente essere elencato sopra.

Se TSUN Local identifica uno di questi protocolli:

```text
1511
02B0
1097
```

lascialo funzionare e controlla le entità rilevate.

> [!TIP]
> **Il tuo inverter potrebbe diventare il prossimo modello validato.** Sono utili il modello esatto, il protocollo rilevato, il numero di ingressi PV, la versione firmware e quali entità restituiscono valori plausibili.

---

## TSUN Local 1.4

### Un TSUN Local più ampio

La versione 1.4 porta TSUN Local dai singoli modelli conosciuti verso la **compatibilità per famiglia di protocollo**.

| | |
|---|---|
| 🔌 | **1511 · 02B0 · 1097** |
| 🔍 | Identificazione automatica del protocollo |
| ☀️ | Rilevamento progressivo / dinamico degli ingressi PV |
| 📊 | Telemetria locale ampliata |
| 🛡️ | Diagnostica avanzata in sola lettura |
| 🌍 | 8 lingue |
| 🧪 | Test più semplice di nuovi modelli TSUN |

---

## Politica di validazione

I nomi funzionali e il supporto di un modello vengono indicati come convalidati solo dopo controlli riproducibili su hardware reale.

I candidati alla compatibilità sono intenzionalmente distinti dall’hardware effettivamente validato.

---

## Contributi

TSUN Local beneficia anche dei contributi della community:

- **Stefan Allius / `s-allius/tsun-gen3-proxy`** — ricerca pubblica sul protocollo 1097 che ha contribuito alla mappatura sperimentale usata da TSUN Local.
- **TheSmartGerman** — test su hardware reale e feedback di compatibilità per il **TSOL-MP3000 con 1511**, durante i quali il protocollo **1097** è stato rilevato involontariamente.

---

## Progetto

> [!IMPORTANT]
> **Progetto comunitario non ufficiale.** TSUN Local è indipendente e non è sviluppato, approvato, sostenuto o mantenuto da TSUN.

Creato e mantenuto da **Jean-Philippe TESTART · `jptstar`**  
*Creato e condiviso per passione, curiosità tecnica e per la community di Home Assistant.*

---

## Licenza

Copyright © 2026 Jean-Philippe TESTART (`jptstar`).

Distribuito con licenza **GNU General Public License v3.0 o successiva**. Vedi [LICENSE](../LICENSE).
