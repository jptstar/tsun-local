# TSUN Local — intégration locale Home Assistant

[Français](README.md) | [English](README_EN.md) | [Deutsch](README_DE.md)

[![GitHub Release](https://img.shields.io/github/v/release/jptstar/tsun-local)](https://github.com/jptstar/tsun-local/releases)

<p align="center">
  <img src="https://raw.githubusercontent.com/jptstar/tsun-local/main/custom_components/tsun_local/brand/icon@2x.png" width="160" alt="Icône indépendante TSUN Local">
</p>

> **Projet non officiel** — Cette intégration communautaire indépendante n’est ni développée, ni approuvée, ni maintenue par TSUN. Elle n’est affiliée à TSUN d’aucune manière. TSUN et les noms de ses produits restent la propriété de leurs détenteurs respectifs. Toute demande d’assistance concernant cette intégration doit être adressée à son auteur et non à TSUN.

**TSUN Local** permet d’intégrer directement dans Home Assistant des micro-onduleurs TSUN présents sur le réseau local, sans proxy et sans service cloud. La version actuelle prend en charge le **TSOL-MP3000**.

**Auteur : Jean-Philippe TESTART (jptstar)**

## Licence

Copyright © 2026 Jean-Philippe TESTART (jptstar).

Ce projet est distribué sous la licence **GNU General Public License v3.0 ou ultérieure** (`GPL-3.0-or-later`). Les versions modifiées ou redistribuées doivent respecter les conditions de cette licence et conserver les mentions de copyright et de licence. Consultez le fichier [LICENSE](LICENSE).

La licence couvre uniquement cette implémentation indépendante. Elle ne confère aucun droit sur les marques, logos, logiciels ou produits de TSUN. Ce projet reste non officiel et sans affiliation avec TSUN.

## Versions

Les versions publiées suivent le format `MAJEURE.MINEURE.CORRECTIF`. HACS utilise les GitHub Releases pour proposer les mises à jour. Consultez le [journal des modifications](CHANGELOG.md) pour connaître le détail de chaque version.

## Compatibilité

- **Home Assistant 2026.3.0 ou version ultérieure**.
- **TSOL-MP3000** : compatible et validé sur matériel réel, avec 6 entrées PV.

## Installation

### Avec HACS

1. Dans HACS, ouvrez **Intégrations**, puis **Dépôts personnalisés**.
2. Ajoutez `https://github.com/jptstar/tsun-local` avec le type **Integration**.
3. Installez **TSUN Local**, puis redémarrez Home Assistant.

### Installation manuelle

1. Copiez le dossier `custom_components/tsun_local` dans `/config/custom_components/` sur Home Assistant.
2. Redémarrez Home Assistant.
3. Ouvrez **Paramètres → Appareils et services → Ajouter une intégration**.
4. Recherchez **TSUN Local**.
5. Renseignez l’adresse IP, le port et le **SN inscrit sur l’étiquette du micro-onduleur**.

## Plusieurs appareils

Plusieurs micro-onduleurs compatibles peuvent être ajoutés dans la même installation Home Assistant. Pour chaque appareil, relancez **Ajouter une intégration** et saisissez son adresse IP ainsi que son SN unique. Chaque entrée crée un appareil indépendant avec ses propres entités et son propre coordinateur de communication.

## Réglages depuis Home Assistant

Dans **Paramètres → Appareils et services → TSUN Local**, ouvrez le menu de l’appareil concerné :

- **Configurer** règle son intervalle normal, de 10 secondes à 5 minutes (30 secondes par défaut), ainsi que son intervalle hors ligne/nuit, de 1 à 60 minutes (5 minutes par défaut) ;
- **Reconfigurer** permet de modifier son adresse IP et son port TCP sans supprimer les entités ;
- chaque appareil possède son propre intervalle, indépendant des autres.

## Fonctionnement de nuit

Lorsque le micro-onduleur n’est plus alimenté, l’intégration le considère hors ligne sans répéter une erreur à chaque interrogation :

- les mesures AC/PV deviennent indisponibles afin de ne pas afficher de valeurs périmées ;
- le diagnostic **Communication** passe hors ligne ;
- le compteur indique les échecs consécutifs et revient à zéro dès le réveil ;
- l’heure de la dernière communication réussie reste disponible ;
- les tentatives utilisent l’intervalle hors ligne/nuit configuré dans Home Assistant ;
- dès la première réponse du matin, l’intervalle configuré est restauré.

## Capteurs

L’intégration crée un appareil unique avec les mesures AC, 5 mesures pour chacune des 6 entrées PV, la somme des 6 puissances DC, 4 capteurs de diagnostic et un état de connectivité.

Les trois blocs lus sont `01/0x0BB8–0x0BD0`, `03/0x0E10–0x0E2D` et `04/0x0ED8–0x0EF5`.
