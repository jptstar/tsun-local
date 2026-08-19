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
<h3 align="center">Votre onduleur. Votre réseau. Vos données.</h3>
<p align="center"><strong>Local. Lecture seule. Sans cloud. Sans proxy.</strong></p>
<p align="center">Accès local direct aux micro-onduleurs TSUN compatibles dans Home Assistant.<br><strong>1.5.1-beta.2</strong></p>

<p align="center">
  <a href="https://github.com/jptstar/tsun-local/releases"><img alt="Version GitHub" src="https://img.shields.io/github/v/release/jptstar/tsun-local?include_prereleases"></a>
  <a href="https://github.com/hacs/integration"><img alt="HACS" src="https://img.shields.io/badge/HACS-Custom-41BDF5"></a>
  <a href="../LICENSE"><img alt="GPL-3.0-or-later" src="https://img.shields.io/badge/License-GPL--3.0--or--later-blue"></a>
</p>

---

## Votre micro-onduleur TSUN fonctionne peut-être déjà

TSUN Local prend en charge **trois familles de protocoles locaux TSUN**.

| Protocole | Famille / référence validée | Statut |
|:---:|---|:---:|
| **1511** | TITAN · **TSOL-MP3000** | ✅ **Validé** |
| **02B0** | GEN3 / GEN3 PLUS · **TSOL-MX500** | ✅ **Validé** |
| **1097** | GEN3 / GEN3 PLUS | 🧪 **Expérimental** |

> [!TIP]
> **Non listé ne signifie pas non pris en charge.** Si votre onduleur utilise **1511, 02B0 ou 1097**, il peut déjà fonctionner.

<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration">
    <img alt="Ajouter TSUN Local à HACS" src="https://my.home-assistant.io/badges/hacs_repository.svg">
  </a>
</p>

<p align="center"><strong>Installez-le. Laissez TSUN Local identifier le protocole. Voyez ce que votre onduleur expose.</strong></p>

---

## En un coup d’œil

| | Données exposées par TSUN Local |
|---|---|
| ☀️ **PV** | Tension · Courant · Puissance · Énergie du jour · Énergie totale |
| ⚡ **AC** | Tension · Courant · Fréquence · Puissance · Énergie du jour · Énergie totale |
| 🚨 **Diagnostics** | Alarmes actives · Communication · Informations du logger |
| 🛡️ **Avancé** | Protection réseau · Diagnostics de validation terrain MP3000 · Désactivés par défaut |
| 🔒 **Sécurité** | Lecture seule · Aucune écriture de configuration vers l’onduleur |

📚 **[Liste complète des entités par protocole](ENTITIES.md)** — capteurs, capteurs binaires et boutons exposés par **1511, 02B0 et 1097**.

---

## Compatibilité

**Home Assistant 2026.3.0 ou version ultérieure.**

> [!NOTE]
> **✅ Validé** = confirmé sur du matériel réel avec TSUN Local.  
> **🔎 Probablement compatible** = la famille de protocole est prise en charge, mais ce modèle précis n’a pas encore été validé avec TSUN Local.  
> **🧪 Expérimental** = le protocole est pris en charge, mais nécessite encore davantage de validation sur matériel réel.

### 1511 · TITAN — ✅ Validé

**✅ Validé**  
`TSOL-MP3000`

**🔎 Probablement compatible**  
`TSOL-MP2250` · `TSOL-MS3000` *(génération TITAN)*

| | Données disponibles |
|---|---|
| ☀️ **PV** | Jusqu’à 6 entrées · Tension · Courant · Puissance · Énergie du jour et totale |
| ⚡ **AC** | Tension · Courant · Fréquence · Puissance · Énergie du jour et totale |
| 🚨 **Diagnostics** | Alarme onduleur · compteur et liste des alarmes actives |
| 🛡️ **Avancé** | Seuils et temporisations de protection réseau · 10 diagnostics A1/21 supplémentaires en validation terrain · code pays/profil brut candidat · températures · niveau de puissance candidat |

### 02B0 · GEN3 / GEN3 PLUS — ✅ Validé

**✅ Validé**  
`TSOL-MX500`

**🔎 Probablement compatible**  
`TSOL-MX450` · `TSOL-MX800` · `TSOL-MX1000` · `TSOL-MX3000`  
`TSOL-MS800` · `TSOL-MS1600` · `TSOL-MS1800` · `TSOL-MS2000`  
Les variantes `-D` correspondantes peuvent également être compatibles lorsqu’elles existent.

| | Données disponibles |
|---|---|
| ☀️ **PV** | Détection dynamique des entrées PV · Tension · Courant · Puissance · Énergie |
| ⚡ **AC** | Tension · Courant · Fréquence · Puissance · Énergie |
| 🚨 **Diagnostics** | Alarmes onduleur |
| 🛡️ **Avancé** | Diagnostics de protection réseau · Niveau de puissance (%) |

### 1097 · GEN3 / GEN3 PLUS — 🧪 Expérimental

**🔎 Probablement compatible**  
`TSOL-MS300` · `TSOL-MS350` · `TSOL-MS400`  
`TSOL-MS600` · `TSOL-MS700` · `TSOL-MS800`  
`TSOL-MS3000` · `TSOL-MX3000D`

| | Données disponibles |
|---|---|
| ☀️ **PV** | Télémétrie PV standard |
| ⚡ **AC** | Télémétrie onduleur / AC standard |
| 🚨 **Diagnostics** | Diagnostics onduleur disponibles |
| 🛡️ **Avancé** | Version protocole · Version onduleur · Température · Isolation RX/RY · Niveau de puissance expérimental · Valeur brute pays/profil · Puissance nominale de conception |

---

## 🚨 Catalogue d’alarmes MP3000

Les **224 positions** des 14 mots d’alarme sont toutes intégrées, comptées et affichées lorsqu’elles sont actives. Les **12 correspondances fonctionnelles validées** couvrent la tension d’entrée PV trop faible et les défauts DSP pour PV1 à PV6. Les **212 autres positions** restent entièrement opérationnelles avec un code TSUN Local neutre et unique ; leur signification nécessite une validation physique sur un matériel de contrôle adapté.

Home Assistant conserve une page lisible : un état **Alarme de l’onduleur**, un compteur et une liste **Alarmes actives**, puis les 14 mots bruts complets comme diagnostics désactivés par défaut. Aucune des 224 positions n’est ignorée et 224 entités permanentes ne sont pas créées.

La bêta 1.5.1 ne modifie pas cette architecture d’alarmes : les 224 positions, les codes uniques et les six mots d’alarme PV restent inchangés.

---

## 🧪 TSUN Local 1.5.1 beta 1

La 1.5.1-beta.2 conserve la présentation et le fonctionnement de la 1.5.0, tout en ajoutant les dernières découvertes MP3000 en **lecture seule**.

| | Nouveautés |
|---|---|
| 📶 | **Signal Wi-Fi du logger corrigé** : une page `index` valide mais sans RSSI n’empêche plus la lecture de `cover_sta_rssi` sur `/status.html` ; le dump réel après correction a remonté **30 %** |
| 🛡️ | **10 diagnostics A1/21 supplémentaires** exposés comme entités avancées, désactivées par défaut |
| 🌍 | **Code pays/profil brut candidat** : `2000 / 0x07D0 = 8` sur le MP3000 configuré France |
| ⏱️ | `0x07D1 = 80` et `0x07D2 = 80` documentés comme paire candidate pour les deux temporisations de 40,0 s, sans inventer leur ordre individuel |
| 🚨 | Les **224 positions d’alarme** de la 1.5.0 sont conservées sans doublon d’entité |
| 🔒 | Aucune écriture vers l’onduleur |

Pour les nouvelles correspondances sémantiques A1/21, le statut reste volontairement :

**LIVE DEVICE READ CONFIRMED; CONFIGURATION CHANGE VALIDATION PENDING**

### Pays France : 8, pas 1008

L’export `device_parameters.csv` de TSUN/Talent contient bien `France` avec un `raw_value` exporté de `1008`. Mais **1008 n’est pas utilisé comme code pays local**. Le dernier dump a d’ailleurs trouvé `1008` sur `0x0BCE` au moment où le compteur d’énergie AC journalière valait simplement **10,08 kWh**.

Les recherches publiques de **Stefan Allius / `s-allius/tsun-gen3-proxy`** documentent la table pays du protocole 1097, où **France = 8**, ainsi que le champ pays/profil 1097 à `0x1400`. Cette découverte est explicitement attribuée à Stefan. La valeur MP3000 `0x07D0 = 8` devient ainsi le meilleur candidat 1511 pour le pays, mais l’adresse sémantique 1511 reste sous validation indépendante.

📚 Voir **[MP3000 / TITAN 1511 — diagnostics de validation terrain](MP3000_FIELD_VALIDATION.md)**.

---

## 🛡️ Diagnostics avancés

Les entités avancées sont volontairement **désactivées par défaut**. La page standard de l’appareil reste ainsi simple, tout en permettant d’activer les informations techniques lorsque nécessaire.

Pour en activer une :

**Paramètres → Appareils et services → TSUN Local → Appareil → Entités → Entités désactivées**

Aucune écriture de configuration vers l’onduleur n’est implémentée.

---

## Installation

### HACS

<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration">
    <img alt="Ajouter TSUN Local à HACS" src="https://my.home-assistant.io/badges/hacs_repository.svg">
  </a>
</p>

Ou ajoutez `https://github.com/jptstar/tsun-local` dans **HACS → Dépôts personnalisés → Intégration**, installez **TSUN Local**, puis redémarrez Home Assistant.

### Manuel

Copiez `custom_components/tsun_local` dans `/config/custom_components/`, redémarrez Home Assistant, puis ajoutez **TSUN Local** depuis **Paramètres → Appareils et services**.

---

## Fonctionnement

```text
Onduleur TSUN
     │
     │ Réseau local
     ▼
 TSUN Local
     │
     ▼
Home Assistant
```

**Aucun cloud dans le chemin des données. Aucun proxy. Aucun service d’exécution distant. Aucune écriture de configuration vers l’onduleur.**

Interrogation locale directe uniquement.

---

## Politique de validation

Les noms fonctionnels et la prise en charge d’un modèle ne sont indiqués comme validés qu’après des contrôles reproductibles sur du matériel réel.

Une valeur locale qui correspond numériquement au profil constitue une preuve utile, mais elle reste marquée comme candidate tant qu’une observation indépendante ne permet pas de distinguer le champ sans ambiguïté.

---

## Contributions

TSUN Local bénéficie également de contributions communautaires :

- **Stefan Allius / `s-allius/tsun-gen3-proxy`** — recherches publiques sur le protocole 1097 ayant contribué au mapping expérimental utilisé par TSUN Local, notamment la découverte du champ pays/profil et de la table des pays où France = `8`.
- **TheSmartGerman** — tests sur matériel réel et retours de compatibilité sur le **TSOL-MP3000 en 1511**, au cours desquels le protocole **1097** a été détecté involontairement.

---

## Projet

> [!IMPORTANT]
> **Projet communautaire non officiel.** TSUN Local est indépendant et n’est ni développé, ni approuvé, ni soutenu, ni maintenu par TSUN.

Créé et maintenu par **Jean-Philippe TESTART · `jptstar`**  
*Développé et partagé par plaisir, curiosité technique et pour la communauté Home Assistant.*

---

## Licence

Copyright © 2026 Jean-Philippe TESTART (`jptstar`).

Distribué sous **GNU General Public License v3.0 ou ultérieure**. Voir [LICENSE](../LICENSE).
