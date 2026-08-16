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
<h3 align="center">Votre onduleur. Votre réseau. Vos données.</h3>
<p align="center"><strong>Local. Lecture seule. Sans cloud. Sans proxy.</strong></p>
<p align="center">Accès local direct aux micro-onduleurs TSUN compatibles dans Home Assistant.<br><strong>1.4.0-beta.8</strong></p>

<p align="center">
  <a href="https://github.com/jptstar/tsun-local/releases"><img alt="Version GitHub" src="https://img.shields.io/github/v/release/jptstar/tsun-local"></a>
  <a href="https://github.com/hacs/integration"><img alt="HACS" src="https://img.shields.io/badge/HACS-Custom-41BDF5"></a>
  <a href="../LICENSE"><img alt="GPL-3.0-or-later" src="https://img.shields.io/badge/License-GPL--3.0--or--later-blue"></a>
</p>

---

## Votre micro-onduleur TSUN fonctionne peut-être déjà

TSUN Local prend en charge **trois familles de protocoles locaux TSUN**.

| Protocole | Famille / référence validée | Statut |
|:---:|---|:---:|
| **1511** | TITAN · **TSOL-MP3000** | ✅ **Validé** |
| **02B0** | GEN3 PLUS · **TSOL-MX500** | ✅ **Validé** |
| **1097** | GEN3 | 🧪 **Expérimental** |

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
| 🚨 **Diagnostics** | Alarmes · Communication · Informations du logger |
| 🛡️ **Avancé** | Protection réseau · Diagnostics onduleur · Désactivés par défaut |
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
| 🚨 **Diagnostics** | Alarmes onduleur |
| 🛡️ **Avancé** | Seuils de protection réseau et temporisations |

### 02B0 · GEN3 PLUS — ✅ Validé

**✅ Validé**  
`TSOL-MX500`

**🔎 Probablement compatible**  
`TSOL-MX450` · `TSOL-MX800` · `TSOL-MX1000` · `TSOL-MX3000`  
`TSOL-MS800` · `TSOL-MS1600` · `TSOL-MS1800` · `TSOL-MS2000`  
Les variantes `-D` correspondantes peuvent également être compatibles lorsqu’elles existent.

> [!NOTE]
> Les recherches publiques sur GEN3 PLUS associent généralement ces appareils à la famille de numéros de série **Y17 / Y47**. Cela permet notamment de distinguer les modèles dont le nom existe aussi dans d’anciennes variantes GEN3.

| | Données disponibles |
|---|---|
| ☀️ **PV** | Détection dynamique des entrées PV · Tension · Courant · Puissance · Énergie |
| ⚡ **AC** | Tension · Courant · Fréquence · Puissance · Énergie |
| 🚨 **Diagnostics** | Alarmes onduleur |
| 🛡️ **Avancé** | Diagnostics de protection réseau · Coefficient de sortie |

### 1097 · GEN3 — 🧪 Expérimental

**🔎 Probablement compatible**  
`TSOL-MS300` · `TSOL-MS350` · `TSOL-MS400`  
`TSOL-MS600` · `TSOL-MS700` · `TSOL-MS800`  
`TSOL-MS3000`

> [!NOTE]
> Les recherches publiques sur GEN3 associent généralement ces appareils à la famille de numéros de série **R17 / R47**. La compatibilité avec le protocole **1097** de TSUN Local reste expérimentale tant qu’elle n’a pas été confirmée sur davantage de matériel réel.

| | Données disponibles |
|---|---|
| ☀️ **PV** | Télémétrie PV standard |
| ⚡ **AC** | Télémétrie onduleur / AC standard |
| 🚨 **Diagnostics** | Diagnostics onduleur disponibles |
| 🛡️ **Avancé** | Version protocole · Version onduleur · Température · Isolation RX/RY · Valeur brute pays/profil · Puissance nominale de conception |

> **🔎 Probablement compatible ne signifie pas validé.** Cela signifie que TSUN Local implémente déjà la famille de protocole correspondante, ce qui en fait un bon candidat à la compatibilité.

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

## Tester un autre modèle TSUN

Votre onduleur n’a pas besoin d’être listé ci-dessus.

Si TSUN Local identifie l’un de ces protocoles :

```text
1511
02B0
1097
```

laissez-le fonctionner et vérifiez les entités découvertes.

> [!TIP]
> **Votre onduleur peut devenir le prochain modèle validé.** Les retours utiles comprennent le modèle exact, le protocole détecté, le nombre d’entrées PV, la version du firmware et les entités renvoyant des valeurs plausibles.

---

## TSUN Local 1.4

### Un TSUN Local plus large

La version 1.4 fait évoluer TSUN Local d’une prise en charge de modèles individuels vers une **compatibilité par familles de protocoles**.

| | |
|---|---|
| 🔌 | **1511 · 02B0 · 1097** |
| 🔍 | Identification automatique du protocole |
| ☀️ | Détection progressive / dynamique des entrées PV |
| 📊 | Télémétrie locale étendue |
| 🛡️ | Diagnostics avancés en lecture seule |
| 🌍 | 8 langues |
| 🧪 | Tests facilités pour de nouveaux modèles TSUN |

---

## Rétro-ingénierie et validation

Les implémentations 1511 et 02B0 sont développées à partir d’une **analyse indépendante du protocole local, d’observations sur appareil réel et de validations matérielles**.

Les candidats à la compatibilité sont volontairement distingués du matériel réellement validé.

---

## Contributions

TSUN Local bénéficie également de contributions communautaires :

- **Stefan Allius / `s-allius/tsun-gen3-proxy`** — recherches publiques sur le protocole 1097 ayant contribué au mapping expérimental utilisé par TSUN Local.
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
