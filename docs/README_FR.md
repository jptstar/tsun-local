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
  <img src="../custom_components/tsun_local/brand/icon@2x.png" width="160" alt="TSUN Local pour Home Assistant, TSUN et Sunology PLAY2">
</p>

<h1 align="center">TSUN Local</h1>
<h3 align="center">Le solaire local plug-and-play dans Home Assistant</h3>
<p align="center"><strong>Détection automatique · Local · Lecture seule · Sans cloud · Sans proxy</strong></p>
<p align="center">Accès local direct aux micro-onduleurs TSUN compatibles et au <strong>Sunology PLAY2</strong>.<br><strong>1.5.2</strong></p>

<p align="center">
  <a href="https://github.com/jptstar/tsun-local/releases"><img alt="Version GitHub" src="https://img.shields.io/github/v/release/jptstar/tsun-local"></a>
  <a href="https://github.com/hacs/integration"><img alt="HACS" src="https://img.shields.io/badge/HACS-Custom-41BDF5"></a>
  <a href="../LICENSE"><img alt="GPL-3.0-or-later" src="https://img.shields.io/badge/License-GPL--3.0--or--later-blue"></a>
</p>

<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration">
    <img alt="Ajouter TSUN Local à HACS" src="https://my.home-assistant.io/badges/hacs_repository.svg">
  </a>
</p>

<p align="center"><a href="https://jptstar.github.io/tsun-local/"><strong>Site du projet</strong></a> · <a href="https://jptstar.github.io/tsun-local/sunology-play2.html"><strong>Sunology PLAY2</strong></a> · <a href="ENTITIES.md"><strong>Entités</strong></a></p>

---

## Installez. Ajoutez l’intégration. TSUN Local trouve l’onduleur.

TSUN Local est conçu pour que le suivi solaire local ressemble à une intégration Home Assistant native, pas à un projet de protocole réseau.

1. Installez **TSUN Local** avec HACS.
2. Redémarrez Home Assistant puis ajoutez **TSUN Local** depuis **Paramètres → Appareils et services**.
3. Sur un réseau local compatible, TSUN Local découvre le logger, identifie automatiquement la famille de protocole prise en charge et crée l’appareil.

**Pas d’adresse IP à saisir dans le flux automatique normal. Pas de proxy à déployer. Pas de compte cloud nécessaire au chemin des données. Pas de protocole à sélectionner.**

La découverte manuelle ou ciblée reste disponible pour les VLAN et réseaux atypiques.

---

## ✅ Sunology PLAY2 maintenant validé

Un véritable **Sunology PLAY2** a terminé avec succès l’installation normale de TSUN Local dans Home Assistant. Lors de ce test communautaire indépendant, le PLAY2 a été **détecté automatiquement et rapidement** par l’intégration.

Chemin local validé :

```text
Sunology PLAY2
  → logger LSW5BLE
  → TCP 8899
  → Solarman V5
  → sensor list 0x02B0
  → Modbus RTU FC03
  → TSUN Local
  → Home Assistant
```

Firmware logger testé sur le terrain : `LSW5BLE_17_02B0_1.08-D1`.

Le probe PLAY2 dédié a été utile pendant la phase de recherche, mais **un utilisateur PLAY2 doit désormais commencer par l’intégration TSUN Local normale et sa détection automatique**.

📚 **[Détails de compatibilité locale Sunology PLAY2](PLAY2_LOCAL_RESEARCH.md)**

---

## Compatibilité

**Home Assistant 2026.3.0 ou version ultérieure.**

| Protocole | Famille / matériel validé | Statut |
|:---:|---|:---:|
| **1511** | TITAN · **TSOL-MP3000** | ✅ Validé |
| **02B0** | GEN3 / GEN3 PLUS · **TSOL-MX500 · Sunology PLAY2** | ✅ Validé |
| **1097** | GEN3 / GEN3 PLUS | 🧪 Expérimental |

**Probablement compatibles en 1511 / 02B0 :** `TSOL-MP2250`, `TSOL-MS3000` (génération TITAN), `TSOL-MX450`, `TSOL-MX800`, `TSOL-MX1000`, `TSOL-MX3000`, `TSOL-MS800`, `TSOL-MS1600`, `TSOL-MS1800`, `TSOL-MS2000` et variantes `-D` correspondantes lorsqu’elles existent.

**Candidats 1097 expérimentaux :** `TSOL-MS300`, `TSOL-MS350`, `TSOL-MS400`, `TSOL-MS600`, `TSOL-MS700`, `TSOL-MS800`, `TSOL-MS3000`, `TSOL-MX3000D`.

> [!NOTE]
> Un même nom commercial peut couvrir plusieurs générations matérielles ou de logger. **Le protocole local détecté fait foi pour la compatibilité TSUN Local.**

---

## Ce que vous obtenez dans Home Assistant

| | Données exposées par TSUN Local |
|---|---|
| ☀️ **PV** | Tension · Courant · Puissance · Énergie du jour · Énergie totale |
| ⚡ **AC** | Tension · Courant · Fréquence · Puissance · Énergie du jour · Énergie totale |
| 🚨 **Alarmes** | Alarme onduleur · Nombre d’alarmes actives · Alarmes actives lisibles lorsque disponibles |
| 📡 **Communication** | État en ligne · Dernière communication réussie · Durée · Échecs |
| 🧩 **Appareil** | Firmware · informations logger · entrées PV détectées |
| 🛡️ **Avancé** | Protection réseau et diagnostics de validation en lecture seule, désactivés par défaut |

Les entrées PV sont créées dynamiquement lorsqu’elles sont détectées, sans imposer une topologie fixe à tous les onduleurs.

📚 **[Référence complète des entités par protocole](ENTITIES.md)**  
🌐 **[Référence visuelle des entités](https://jptstar.github.io/tsun-local/entities.html)**

---

## 🚨 Alarmes en texte clair — bêta 1.5.3

La **bêta 1.5.3** généralise l’interface compacte des alarmes aux protocoles **1511, 02B0 et 1097**.

Au lieu de n’exposer que des mots ou bits bruts, les alarmes actives peuvent être présentées avec un texte lisible et traduit, tout en conservant un code stable utile au diagnostic :

```text
Sous-tension réseau (02B0-A014)
Tension d’entrée PV1 trop faible (1511-A137)
Alarme onduleur non identifiée (1097-A041)
```

Les alarmes connues reçoivent un libellé fonctionnel clair. Les positions inconnues ou réservées restent visibles avec un texte neutre plutôt qu’une signification inventée.

- **1511 :** 224 positions de catalogue
- **02B0 :** 64 positions
- **1097 :** 64 positions
- Français, anglais, allemand, espagnol, italien, néerlandais, polonais et chinois simplifié

L’interface Home Assistant reste compacte : **Alarme de l’onduleur**, **Alarmes actives** et **Noms des alarmes actives**. Les mots bruts complets restent disponibles dans les diagnostics désactivés par défaut.

---

## Lecture seule par conception

TSUN Local effectue uniquement des lectures locales.

- aucune écriture de configuration onduleur ;
- aucune écriture de protection réseau ;
- aucune modification de provisioning ;
- aucun service d’exécution distant ;
- aucun cloud ni proxy dans le chemin des données Home Assistant.

Les correspondances expérimentales restent explicitement signalées jusqu’à validation indépendante.

---

## Installation

### HACS

Utilisez le bouton ci-dessus ou ajoutez :

`https://github.com/jptstar/tsun-local`

comme **HACS → Dépôts personnalisés → Intégration**, installez **TSUN Local**, redémarrez Home Assistant puis ajoutez l’intégration depuis **Paramètres → Appareils et services**.

### Manuel

Copiez `custom_components/tsun_local` dans `/config/custom_components/`, redémarrez Home Assistant puis ajoutez **TSUN Local**.

---

## Tester un autre onduleur

Si votre onduleur n’est pas listé, il peut déjà fonctionner s’il expose `1511`, `02B0` ou `1097`.

Le dépôt contient un outil de validation respectueux de la confidentialité et strictement en lecture seule :

**[`tools/tsun_dump.py`](../tools/tsun_dump.py)**

Les retours les plus utiles sont le modèle ou la marque OEM exacte, le protocole détecté, le firmware, le nombre d’entrées PV et la cohérence des valeurs AC/PV.

> [!TIP]
> **Votre onduleur pourrait devenir le prochain modèle validé.**

---

## Contributions

TSUN Local bénéficie de recherches protocolaires publiques et de tests indépendants sur matériel réel.

- **Stefan Allius / `s-allius/tsun-gen3-proxy`** — recherches publiques GEN3 / 1097 utilisées comme référence pour certaines correspondances expérimentales.
- **TheSmartGerman** — retours de compatibilité sur matériel réel.
- **dca31** — validation indépendante de l’installation Sunology PLAY2 dans Home Assistant.

---

## Projet

> [!IMPORTANT]
> **Projet communautaire non officiel.** TSUN Local est indépendant et n’est ni développé, ni approuvé, ni soutenu, ni maintenu par TSUN ou Sunology.

Créé et maintenu par **Jean-Philippe TESTART · `jptstar`**  
*Développé et partagé par plaisir, curiosité technique et pour la communauté Home Assistant.*

Distribué sous **GNU GPL v3.0 ou ultérieure**. Voir [LICENSE](../LICENSE).
