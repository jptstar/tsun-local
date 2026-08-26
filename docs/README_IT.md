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
<p align="center">Accesso locale diretto ai microinverter TSUN compatibili in Home Assistant.<br><strong>1.5.3-beta.2</strong></p>

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
| **02B0** | GEN3 / GEN3 PLUS · **TSOL-MX500** | ✅ **Validato** |
| **1097** | GEN3 / GEN3 PLUS | 🧪 **Sperimentale** |

> [!TIP]
> **Non presente nell’elenco non significa non supportato.** Se il tuo inverter usa **1511, 02B0 o 1097**, potrebbe già funzionare.

<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration">
    <img alt="Aggiungi TSUN Local a HACS" src="https://my.home-assistant.io/badges/hacs_repository.svg">
  </a>
</p>

---

## In breve

| | Cosa espone TSUN Local |
|---|---|
| ☀️ **PV** | Tensione · Corrente · Potenza · Energia giornaliera · Energia totale |
| ⚡ **AC** | Tensione · Corrente · Frequenza · Potenza · Energia giornaliera · Energia totale |
| 🚨 **Diagnostica** | Allarmi attivi · Comunicazione · Informazioni logger |
| 🛡️ **Avanzata** | Protezione rete · Firmware · Diagnostica inverter · Dati sperimentali di validazione sul campo |
| 🔒 **Sicurezza** | Sola lettura · Nessuna scrittura di configurazione sull’inverter |

📚 **[Riferimento completo delle entità per protocollo](ENTITIES.md)**

---

## Compatibilità

**Home Assistant 2026.3.0 o successivo.**

> [!NOTE]
> **✅ Validato** = confermato su hardware reale con TSUN Local.  
> **🔎 Probabilmente compatibile** = la famiglia di protocollo è supportata, ma questo modello preciso non è ancora stato validato.  
> **🧪 Sperimentale** = il protocollo è supportato, ma serve ancora una validazione più ampia su dispositivi reali.

### 1511 · TITAN — ✅ Validato

**✅ Validato**  
`TSOL-MP3000`

**🔎 Probabilmente compatibile**  
`TSOL-MP2250` · `TSOL-MS3000` *(generazione TITAN)*

Fino a 6 ingressi PV, telemetria AC/PV, energia, diagnostica inverter, versioni firmware, allarmi e diagnostica di rete avanzata in sola lettura.

📚 **[Dettagli di validazione MP3000 / TITAN](MP3000_FIELD_VALIDATION.md)**

### 02B0 · GEN3 / GEN3 PLUS — ✅ Validato

**✅ Validato**  
`TSOL-MX500` · `Sunology PLAY2`

**🔎 Probabilmente compatibile**  
`TSOL-MX450` · `TSOL-MX800` · `TSOL-MX1000` · `TSOL-MX3000`  
`TSOL-MS800` · `TSOL-MS1600` · `TSOL-MS1800` · `TSOL-MS2000`

Le corrispondenti varianti `-D` possono essere compatibili dove previste.

Rilevamento dinamico degli ingressi PV, telemetria AC/PV, allarmi inverter e diagnostica avanzata in sola lettura.


Validazione indipendente di **Sunology PLAY2** in Home Assistant: rilevamento automatico e configurazione TSUN Local completati con successo su hardware reale.

### 1097 · GEN3 / GEN3 PLUS — 🧪 Sperimentale

**🔎 Probabilmente compatibile**  
`TSOL-MS300` · `TSOL-MS350` · `TSOL-MS400`  
`TSOL-MS600` · `TSOL-MS700` · `TSOL-MS800`  
`TSOL-MS3000` · `TSOL-MX3000D`

Il supporto del protocollo è implementato, ma serve ulteriore validazione su dispositivi reali.

> [!NOTE]
> Lo stesso nome commerciale può coprire più generazioni hardware o logger. **Per TSUN Local fa fede il protocollo locale rilevato.**

---

## 🚨 Allarmi MP3000

TSUN Local supporta l’intero bitfield degli allarmi MP3000 mantenendo compatta l’interfaccia Home Assistant. **Tutte le 224 posizioni di allarme vengono conservate e valutate quando diventano attive.**

Le **12 corrispondenze funzionali osservate su hardware** coprono la bassa tensione d’ingresso PV e i guasti DSP per PV1 fino a PV6. Le altre **212 posizioni** mantengono identificatori TSUN Local neutri e stabili finché il loro significato funzionale non viene validato fisicamente.

Home Assistant espone uno stato **Allarme inverter**, un conteggio **Allarmi attivi** e un sensore **Nomi allarmi attivi**. Le 14 parole grezze complete restano disponibili come diagnostica disattivata per impostazione predefinita, senza creare 224 entità permanenti.

---


> [!TIP]
> Gli allarmi attivi sono mostrati anche come **testo chiaro localizzato** con un codice di posizione stabile, ad esempio `Sottotensione rete (02B0-A014)`. **Sunology PLAY2** usa la stessa interfaccia compatta 02B0; le quattro parole ERR grezze restano disponibili come diagnostica avanzata.

## 🛡️ Diagnostica avanzata

Le entità avanzate sono intenzionalmente **disattivate per impostazione predefinita**. A seconda del protocollo includono valori di protezione rete, firmware, diagnostica inverter e alcuni valori sperimentali di validazione sul campo.

Per abilitarle:

**Impostazioni → Dispositivi e servizi → TSUN Local → Dispositivo → Entità → Entità disabilitate**

Le associazioni semantiche sperimentali restano esplicitamente indicate fino a validazione indipendente. Non sono implementate scritture di configurazione verso l’inverter.

📚 **[Evidenze di validazione MP3000](MP3000_FIELD_VALIDATION.md)**  
📚 **[Riferimento completo delle entità](ENTITIES.md)**

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

## 🔬 Valida un altro modello TSUN

TSUN Local include uno strumento di dump hardware autonomo, rispettoso della privacy e **rigorosamente in sola lettura**.

**⬇️ [Scarica `tsun_dump.py`](https://raw.githubusercontent.com/jptstar/tsun-local/main/tools/tsun_dump.py)**

È sufficiente Python 3.10+.

macOS / Linux:

```bash
cd ~/Downloads
python3 tsun_dump.py --full
```

Windows:

```powershell
py tsun_dump.py --full
```

Lo strumento può rilevare logger TSUN compatibili, identificare le famiglie di protocollo supportate e creare un dump JSON rispettoso della privacy per ogni dispositivo. Non implementa alcuna scrittura verso l’inverter.

Per VLAN, rilevamento mirato, confronti prima/dopo e validazione avanzata:

📚 **[Guida Hardware Validation Dump Tool](HARDWARE_DUMP.md)**

---

## Prova un inverter non elencato

Se TSUN Local rileva `1511`, `02B0` o `1097`, lascialo funzionare e controlla le entità scoperte.

Sono utili il modello esatto, il protocollo rilevato, la versione firmware, il numero di ingressi PV e quali entità restituiscono valori plausibili.

> [!TIP]
> **Il tuo inverter potrebbe diventare il prossimo modello validato.**

---

## Politica di validazione

TSUN Local separa il supporto hardware confermato dalla ricerca sperimentale sui protocolli.

I nomi funzionali e il supporto di un modello vengono indicati come validati solo dopo controlli riproducibili su hardware reale. Un valore che coincide semplicemente con un profilo atteso costituisce un indizio, non una prova; le associazioni sperimentali restano marcate finché un’osservazione indipendente non le distingue in modo univoco.

---

## Contributi

TSUN Local beneficia della ricerca pubblica sui protocolli e dei test della community su hardware reale.

- **Stefan Allius / `s-allius/tsun-gen3-proxy`** — ricerca pubblica sui protocolli GEN3 / 1097 usata come riferimento per alcune associazioni sperimentali.
- **TheSmartGerman** — feedback di compatibilità su hardware reale.

La provenienza dettagliata e le evidenze di validazione sono documentate insieme alla relativa ricerca sul protocollo.

---

## Progetto

> [!IMPORTANT]
> **Progetto community non ufficiale.** TSUN Local è indipendente e non è sviluppato, approvato, supportato o mantenuto da TSUN.

Creato e mantenuto da **Jean-Philippe TESTART · `jptstar`**  
*Sviluppato e condiviso per divertimento, curiosità tecnica e per la community Home Assistant.*

---

## Licenza

Copyright © 2026 Jean-Philippe TESTART (`jptstar`).

Distribuito sotto **GNU General Public License v3.0 o successiva**. Vedi [LICENSE](../LICENSE).
