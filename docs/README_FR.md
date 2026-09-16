<p align="center"><a href="../README.md">English</a> · <strong>Français</strong> · <a href="README_DE.md">Deutsch</a> · <a href="README_NL.md">Nederlands</a> · <a href="README_IT.md">Italiano</a> · <a href="README_ES.md">Español</a> · <a href="README_PL.md">Polski</a> · <a href="README_ZH.md">简体中文</a></p>

<h1 align="center">TSUN Local</h1>
<h3 align="center">Votre onduleur. Votre réseau. Vos données.</h3>
<p align="center"><strong>Découverte automatique · Local · Lecture seule · Sans cloud · Sans proxy</strong><br><strong>1.6.2</strong></p>

## Compatibilité

| Protocole | Famille | Matériel validé | Statut |
|:---:|---|---|:---:|
| **1511** | TITAN | **TSOL-MP3000** | ✅ **Validé** |
| **02B0** | GEN3 / GEN3 PLUS | **TSOL-MS300** · **TSOL-MX500** · **TSOL-MS800** · **TSOL-MS2000** · **Sunology PLAY2** | ✅ **Validé** |
| **1097** | GEN4 | **Sunology PLAY2 (GEN4)** | ✅ **Validé** |

- **1511 — Probablement compatible:** `TSOL-MP2250` · `TSOL-MS3000`
- **02B0 — Probablement compatible:** `TSOL-MX450` · `TSOL-MX800` · `TSOL-MX1000` · `TSOL-MX3000` · `TSOL-MS1600` · `TSOL-MS1800`
- **1097 — Probablement compatible:** `TSOL-MS300` · `TSOL-MS350` · `TSOL-MS400` · `TSOL-MS600` · `TSOL-MS700` · `TSOL-MS800` · `TSOL-MS3000` · `TSOL-MX3000D`

Pages validées : [TSOL-MS300](https://jptstar.github.io/tsun-local/tsol-ms300-home-assistant.html) · [TSOL-MX500](https://jptstar.github.io/tsun-local/tsol-mx500-home-assistant.html) · [TSOL-MS800](https://jptstar.github.io/tsun-local/tsol-ms800-home-assistant.html) · [TSOL-MS2000](https://jptstar.github.io/tsun-local/tsol-ms2000-home-assistant.html) · [Sunology PLAY2](https://jptstar.github.io/tsun-local/sunology-play2.html)

## Installation

Installez TSUN Local via HACS, redémarrez Home Assistant puis ajoutez l’intégration depuis **Paramètres → Appareils et services**.

## Diagnostic

Deux paquets publics sont maintenus :

- **Windows** : [TSUN-Local-Diagnostic.exe](https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic.exe)
- **Python 3.10+** : [TSUN-Local-Diagnostic-Python.zip](https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic-Python.zip)

Le diagnostic est strictement en lecture seule. Désactivez l’entrée TSUN Local concernée avant la capture et réactivez-la ensuite. L’envoi d’un rapport anonymisé nécessite toujours un consentement explicite.

📚 [Guide diagnostic](HARDWARE_DUMP.md) · [Recherche PLAY2](PLAY2_LOCAL_RESEARCH.md) · [Entités](ENTITIES.md) · [Validation MP3000](MP3000_FIELD_VALIDATION.md)

## Crédits

Recherche publique croisée avec [`ha-solarman`](https://github.com/davidrapan/ha-solarman). Validation matérielle indépendante notamment par **dca31** et **paloindici**. Tous les crédits détaillés sont sur [la page contributeurs](contributors.html).

Projet indépendant maintenu par **Jean-Philippe TESTART (`jptstar`)**. Licence GPL-3.0-or-later.
