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
<h3 align="center">Il tuo inverter. La tua rete. I tuoi dati.</h3>
<p align="center"><strong>Locale. Sola lettura. Nessun cloud. Nessun proxy.</strong></p>
<p align="center">Accesso locale diretto ai microinverter TSUN compatibili in Home Assistant.<br><strong>1.4.0-beta.8</strong></p>

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
| **02B0** | GEN3 PLUS · **TSOL-MX500** | ✅ **Validato** |
| **1097** | GEN3 | 🧪 **Sperimentale** |

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
| 🚨 **Diagnostica** | Allarmi inverter |
| 🛡️ **Avanzata** | Soglie di protezione rete e diagnostica dei tempi |

### 02B0 · GEN3 PLUS — ✅ Validato

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
| 🛡️ **Avanzata** | Diagnostica protezione rete · Coefficiente di uscita |

### 1097 · GEN3 — 🧪 Sperimentale

**🔎 Probabilmente compatibile**  
`TSOL-MS300` · `TSOL-MS350` · `TSOL-MS400`  
`TSOL-MS600` · `TSOL-MS700` · `TSOL-MS800`  
`TSOL-MS3000`

> [!NOTE]
> La ricerca pubblica su GEN3 associa generalmente questi dispositivi alla famiglia di numeri di serie **R17 / R47**. La compatibilità con il protocollo **1097** di TSUN Local resta sperimentale finché non viene confermata su più hardware reale.

| | Dati disponibili |
|---|---|
| ☀️ **PV** | Telemetria PV standard |
| ⚡ **AC** | Telemetria standard inverter / AC |
| 🚨 **Diagnostica** | Diagnostica inverter disponibile |
| 🛡️ **Avanzata** | Versione protocollo · Versione inverter · Temperatura · Isolamento RX/RY · Valore grezzo paese/profilo · Potenza di progetto |

> **🔎 Probabilmente compatibile non significa validato.** Significa che TSUN Local implementa già la famiglia di protocollo pertinente, rendendo il dispositivo un buon candidato alla compatibilità.

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

## Reverse engineering e validazione

Le implementazioni 1511 e 02B0 sono sviluppate tramite **analisi indipendente del protocollo locale, osservazione di dispositivi reali e validazione hardware**.

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
