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
<p align="center">Accès local direct aux micro-onduleurs TSUN compatibles dans Home Assistant.<br><strong>1.5.1</strong></p>

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
| **02B0** | GEN3 / GEN3 PLUS · **TSOL-MX500** | ✅ **Validé** |
| **1097** | GEN3 / GEN3 PLUS | 🧪 **Expérimental** |

> [!TIP]
> **Non listé ne signifie pas non pris en charge.** Si votre onduleur utilise **1511, 02B0 ou 1097**, il peut déjà fonctionner.

<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration">
    <img alt="Ajouter TSUN Local à HACS" src="https://my.home-assistant.io/badges/hacs_repository.svg">
  </a>
</p>

---

## En un coup d’œil

| | Données exposées par TSUN Local |
|---|---|
| ☀️ **PV** | Tension · Courant · Puissance · Énergie du jour · Énergie totale |
| ⚡ **AC** | Tension · Courant · Fréquence · Puissance · Énergie du jour · Énergie totale |
| 🚨 **Diagnostics** | Alarmes actives · Communication · Informations du logger |
| 🛡️ **Avancé** | Protection réseau · Firmware · Diagnostics onduleur · Données expérimentales de validation terrain |
| 🔒 **Sécurité** | Lecture seule · Aucune écriture de configuration vers l’onduleur |

📚 **[Liste complète des entités par protocole](ENTITIES.md)**

---

## Compatibilité

**Home Assistant 2026.3.0 ou version ultérieure.**

> [!NOTE]
> **✅ Validé** = confirmé sur du matériel réel avec TSUN Local.  
> **🔎 Probablement compatible** = la famille de protocole est prise en charge, mais ce modèle précis n’a pas encore été validé.  
> **🧪 Expérimental** = le protocole est pris en charge, mais nécessite encore davantage de validation sur matériel réel.

### 1511 · TITAN — ✅ Validé

**✅ Validé**  
`TSOL-MP3000`

**🔎 Probablement compatible**  
`TSOL-MP2250` · `TSOL-MS3000` *(génération TITAN)*

Jusqu’à 6 entrées PV, télémétrie AC/PV, énergie, diagnostics onduleur, versions firmware, alarmes et diagnostics réseau avancés en lecture seule.

📚 **[Détails de validation MP3000 / TITAN](MP3000_FIELD_VALIDATION.md)**

### 02B0 · GEN3 / GEN3 PLUS — ✅ Validé

**✅ Validé**  
`TSOL-MX500`

**🔎 Probablement compatible**  
`TSOL-MX450` · `TSOL-MX800` · `TSOL-MX1000` · `TSOL-MX3000`  
`TSOL-MS800` · `TSOL-MS1600` · `TSOL-MS1800` · `TSOL-MS2000`

Les variantes `-D` correspondantes peuvent également être compatibles lorsqu’elles existent.

Détection dynamique des entrées PV, télémétrie AC/PV, alarmes onduleur et diagnostics avancés en lecture seule.

### 1097 · GEN3 / GEN3 PLUS — 🧪 Expérimental

**🔎 Probablement compatible**  
`TSOL-MS300` · `TSOL-MS350` · `TSOL-MS400`  
`TSOL-MS600` · `TSOL-MS700` · `TSOL-MS800`  
`TSOL-MS3000` · `TSOL-MX3000D`

Le protocole est implémenté, mais davantage de validation sur matériel réel est nécessaire.

> [!NOTE]
> Un même nom commercial peut couvrir plusieurs générations matérielles ou de logger. **Le protocole local détecté fait foi pour la compatibilité TSUN Local.**

---

## 🚨 Alarmes MP3000

TSUN Local prend en charge l’intégralité du champ d’alarmes MP3000 tout en conservant une interface Home Assistant compacte. **Les 224 positions d’alarme sont préservées et évaluées lorsqu’elles deviennent actives.**

Les **12 correspondances fonctionnelles observées sur matériel** couvrent la faible tension d’entrée PV et les défauts DSP pour PV1 à PV6. Les **212 autres positions** conservent un identifiant TSUN Local neutre et stable jusqu’à validation physique de leur signification.

Home Assistant expose un état **Alarme de l’onduleur**, un compteur **Alarmes actives** et un capteur **Noms des alarmes actives**. Les 14 mots bruts complets restent disponibles comme diagnostics désactivés par défaut, sans créer 224 entités permanentes.

---

## 🛡️ Diagnostics avancés

Les entités avancées sont volontairement **désactivées par défaut**. Elles regroupent, selon le protocole, des valeurs de protection réseau, les firmwares, des diagnostics onduleur et certains champs expérimentaux de validation terrain.

Pour en activer une :

**Paramètres → Appareils et services → TSUN Local → Appareil → Entités → Entités désactivées**

Les correspondances sémantiques expérimentales restent explicitement signalées jusqu’à validation indépendante. Aucune écriture de configuration vers l’onduleur n’est implémentée.

📚 **[Preuves de validation terrain MP3000](MP3000_FIELD_VALIDATION.md)**  
📚 **[Liste complète des entités](ENTITIES.md)**

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

## 🔬 Valider un autre modèle TSUN

TSUN Local inclut un outil autonome de capture matérielle, respectueux de la confidentialité et **strictement en lecture seule**.

**⬇️ [Télécharger `tsun_dump.py`](https://raw.githubusercontent.com/jptstar/tsun-local/main/tools/tsun_dump.py)**

Python 3.10+ suffit.

macOS / Linux :

```bash
cd ~/Downloads
python3 tsun_dump.py --full
```

Windows :

```powershell
py tsun_dump.py --full
```

L’outil peut découvrir les loggers TSUN compatibles, détecter la famille de protocole et produire un fichier JSON respectueux de la confidentialité pour chaque appareil. Aucune écriture vers l’onduleur n’est implémentée.

Pour les VLAN, la découverte ciblée, les comparaisons avant/après et la validation avancée :

📚 **[Guide de l’outil Hardware Validation Dump](HARDWARE_DUMP.md)**

---

## Tester un onduleur non listé

Si TSUN Local détecte `1511`, `02B0` ou `1097`, laissez-le fonctionner et vérifiez les entités découvertes.

Les retours les plus utiles comprennent le modèle exact, le protocole détecté, la version firmware, le nombre d’entrées PV et les entités qui renvoient des valeurs plausibles.

> [!TIP]
> **Votre onduleur pourrait devenir le prochain modèle validé.**

---

## Politique de validation

TSUN Local distingue la prise en charge matérielle confirmée de la recherche protocolaire expérimentale.

Les noms fonctionnels et la prise en charge d’un modèle ne sont indiqués comme validés qu’après des contrôles reproductibles sur du matériel réel. Une valeur qui correspond simplement à un profil constitue une preuve, pas une validation définitive ; les correspondances expérimentales restent signalées jusqu’à ce qu’une observation indépendante permette de les distinguer.

---

## Contributions

TSUN Local bénéficie de recherches protocolaires publiques et de tests communautaires sur matériel réel.

- **Stefan Allius / `s-allius/tsun-gen3-proxy`** — recherches publiques GEN3 / 1097 utilisées comme référence pour certaines correspondances expérimentales.
- **TheSmartGerman** — retours de compatibilité sur matériel réel.

La provenance détaillée et les preuves de validation sont documentées avec les recherches protocolaires concernées.

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
