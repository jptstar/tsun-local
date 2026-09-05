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
<p align="center">Accès local direct aux micro-onduleurs TSUN compatibles dans Home Assistant.<br><strong>1.6.0</strong></p>

<p align="center">
  <a href="https://github.com/jptstar/tsun-local/releases"><img alt="Version GitHub" src="https://img.shields.io/github/v/release/jptstar/tsun-local"></a>
  <a href="https://github.com/hacs/integration"><img alt="HACS" src="https://img.shields.io/badge/HACS-Custom-41BDF5"></a>
  <a href="../LICENSE"><img alt="GPL-3.0-or-later" src="https://img.shields.io/badge/License-GPL--3.0--or--later-blue"></a>
</p>


---

## Compatibilité

**Home Assistant 2026.3.0 ou version ultérieure.**

| Protocole | Famille | Matériel validé | Statut |
|:---:|---|---|:---:|
| **1511** | TITAN | **TSOL-MP3000** | ✅ **Validé** |
| **02B0** | GEN3 / GEN3 PLUS | **TSOL-MX500** · **TSOL-MS800** · **Sunology PLAY2** | ✅ **Validé** |
| **1097** | GEN3 / GEN3 PLUS | — | 🧪 **Expérimental** |

> [!TIP]
> **Un modèle non listé n’est pas forcément incompatible.** TSUN Local se base d’abord sur le protocole local détecté, pas uniquement sur le nom commercial.

<details>
<summary><strong>Modèles probablement compatibles par protocole</strong></summary>

- **1511 — Probablement compatible:** `TSOL-MP2250` · `TSOL-MS3000` (TITAN)
- **02B0 — Probablement compatible:** `TSOL-MX450` · `TSOL-MX800` · `TSOL-MX1000` · `TSOL-MX3000` · `TSOL-MS1600` · `TSOL-MS1800` · `TSOL-MS2000` · variantes `-D` correspondantes
- **1097 — Probablement compatible:** `TSOL-MS300` · `TSOL-MS350` · `TSOL-MS400` · `TSOL-MS600` · `TSOL-MS700` · `TSOL-MS800` · `TSOL-MS3000` · `TSOL-MX3000D`

</details>

📚 **[Validation MP3000 / TITAN](MP3000_FIELD_VALIDATION.md)**

📚 **[TSOL-MX500 Home Assistant](https://jptstar.github.io/tsun-local/tsol-mx500-home-assistant.html)** · **[TSOL-MS800 Home Assistant](https://jptstar.github.io/tsun-local/tsol-ms800-home-assistant.html)**

**Nouveau dans la 1.6.0 :** la **relève adaptative** est activée par défaut et ajuste automatiquement la cadence de lecture en cas d’échecs de communication : 20 s en fonctionnement normal, 30 s après erreur et 300 s hors ligne/nuit.

📚 **[Liste complète des entités](ENTITIES.md)**

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


## 🚨 Catalogues d’alarmes

TSUN Local conserve une interface Home Assistant compacte tout en préservant chaque position de bit d’alarme utilisée par les protocoles pris en charge. **1511 possède 224 positions de catalogue ; 02B0 et 1097 en possèdent 64 chacun.**

Chaque alarme active est présentée sous la forme `Description (PROTOCOLE-Axxx)`, y compris lorsque sa signification est connue. Les positions non identifiées restent visibles avec un libellé neutre traduit, par exemple `Alarme onduleur non identifiée (02B0-A006)`.

Home Assistant expose pour 1511, 02B0 et 1097 un état **Alarme de l’onduleur**, un compteur **Alarmes actives** et un capteur **Noms des alarmes actives**. Les mots bruts complets restent disponibles comme diagnostics désactivés par défaut, sans créer des centaines d’entités permanentes.


---


> [!TIP]
> Les alarmes actives sont exposées en **texte clair localisé** avec un code stable par position, par exemple `Sous-tension réseau (02B0-A014)`. Le **Sunology PLAY2** bénéficie de cette interface 02B0 compacte ; les quatre mots ERR bruts restent disponibles en diagnostics avancés.

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

TSUN Local propose un diagnostic matériel respectueux de la confidentialité et **strictement en lecture seule** pour les modèles non listés et les problèmes de communication.

### Windows — solution la plus simple

**⬇️ [Télécharger `TSUN-Local-Diagnostic.exe`](https://github.com/jptstar/tsun-local/releases/latest/download/TSUN-Local-Diagnostic.exe)**

Aucune installation et aucun environnement Python ne sont nécessaires. L’application portable utilise le même moteur de diagnostic en lecture seule, découvre les loggers TSUN, teste les protocoles **1511 / 02B0 / 1097** et génère un rapport JSON anonymisé.

Pour diagnostiquer une perte de communication ou des entités indisponibles, **désactivez l’entrée de configuration TSUN Local concernée avant de lancer la capture**, puis réactivez-la ensuite.

### macOS / Linux / utilisateurs avancés

**⬇️ [Télécharger `tsun_dump.py`](https://raw.githubusercontent.com/jptstar/tsun-local/main/tools/tsun_dump.py)** — Python 3.10+.

```bash
python3 tsun_dump.py --full
```

Sous Windows, le script reste utilisable avec `py tsun_dump.py --full` si vous le préférez.

📚 **[Guide de l’outil Hardware Validation Dump](HARDWARE_DUMP.md)**

### Sunology PLAY2

**Sunology PLAY2 est validé sur du matériel Home Assistant réel** via le chemin local 02B0 / Solarman V5.

- Découverte automatique et ajout normal de TSUN Local confirmés indépendamment.
- Local et en lecture seule : aucun cloud et aucune écriture de configuration vers l’onduleur.
- La variante matérielle exacte MX400/MX450/MX500 reste volontairement non spécifiée ; le protocole **02B0** détecté fait foi.

📚 **[Détails de la recherche PLAY2](PLAY2_LOCAL_RESEARCH.md)** · 🔬 **[Sonde PLAY2 optionnelle en lecture seule](../tools/tsun_play2_probe.py)**

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

## Contributions et crédits

TSUN Local bénéficie de recherches protocolaires publiques et de validations indépendantes sur matériel réel. Ces crédits décrivent des références et validations ; ils n’impliquent aucune affiliation ni approbation.

- **David Rapan / [`ha-solarman`](https://github.com/davidrapan/ha-solarman)** — référence publique indépendante utilisée pour recouper certains registres Solarman / 02B0.
- **Stefan Allius / [`tsun-gen3-proxy`](https://github.com/s-allius/tsun-gen3-proxy)** — recherches publiques GEN3 / 1097 et country/profile utilisées pour la validation expérimentale.
- **TheSmartGerman** — test sur matériel réel ayant révélé la famille de protocole 1097.
- **dca31** — validation indépendante du Sunology PLAY2 via le parcours Home Assistant normal de TSUN Local.
- **Kmotr** — validation indépendante du TSOL-MS800 avec TSUN Local et un diagnostic Home Assistant anonymisé.

📚 **[Tous les contributeurs et crédits](contributors.html)**

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
