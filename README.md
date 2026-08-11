# TSUN Local — intégration locale Home Assistant

[Français](README.md) | [English](README_EN.md) | [Deutsch](README_DE.md)

[![GitHub Release](https://img.shields.io/github/v/release/jptstar/tsun-local)](https://github.com/jptstar/tsun-local/releases)

<p align="center">
  <img src="https://raw.githubusercontent.com/jptstar/tsun-local/main/custom_components/tsun_local/brand/icon@2x.png" width="160" alt="Icône indépendante TSUN Local">
</p>

> **Projet non officiel** — Cette intégration communautaire indépendante n’est ni développée, ni approuvée, ni maintenue par TSUN. Elle n’est affiliée à TSUN d’aucune manière. TSUN et les noms de ses produits restent la propriété de leurs détenteurs respectifs. Toute demande d’assistance concernant cette intégration doit être adressée à son auteur et non à TSUN.

**TSUN Local** permet d’intégrer directement dans Home Assistant des micro-onduleurs TSUN compatibles présents sur le réseau local, sans proxy et sans service cloud. La version 1.1.0 prend en charge le **TSOL-MP3000** validé et ajoute une première prise en charge des familles **GEN3**, **GEN3 PLUS** et d’autres modèles **TITAN** en attente de validation sur matériel réel.

**Auteur : Jean-Philippe TESTART (jptstar)**

## Licence

Copyright © 2026 Jean-Philippe TESTART (jptstar).

Ce projet est distribué sous la licence **GNU General Public License v3.0 ou ultérieure** (`GPL-3.0-or-later`). Les versions modifiées ou redistribuées doivent respecter les conditions de cette licence et conserver les mentions de copyright et de licence. Consultez le fichier [LICENSE](LICENSE).

La licence couvre uniquement cette implémentation indépendante. Elle ne confère aucun droit sur les marques, logos, logiciels ou produits de TSUN. Ce projet reste non officiel et sans affiliation avec TSUN.

## Versions

Les versions publiées suivent le format `MAJEURE.MINEURE.CORRECTIF`. HACS utilise les GitHub Releases pour proposer les mises à jour. Consultez le [journal des modifications](CHANGELOG.md) pour connaître le détail de chaque version.

## Compatibilité

- **Home Assistant 2026.3.0 ou version ultérieure**.

### Micro-onduleurs TITAN

- **TITAN 2250 W–3000 W — MP3000 / MP2250 / MS3000**
  - ✅ **TSOL-MP3000** : compatible et validé sur matériel réel ;
  - ❌ **TSOL-MP2250** : adaptateur disponible, non validé sur matériel réel ;
  - ❌ **TSOL-MS3000** : adaptateur disponible, non validé sur matériel réel.
- **TITAN 3680 W–6000 W — MP6000 / MP5000 / MP4600 / MP4000 / MP3750 / MP3680**
  - ❌ non validés et non pris en charge actuellement faute de carte complète des entrées PV.

### Micro-onduleurs GEN3 et GEN3 PLUS

L’adaptateur local est disponible pour les appareils à 1, 2 ou 4 entrées PV. Tous les modèles ci-dessous restent marqués ❌ jusqu’à validation par une capture ou un retour utilisateur sur matériel réel :

- ❌ **MS300, MS350, MS400, MS400-D** ;
- ❌ **MS600, MS700, MS800, MS600-D, MS800-D** ;
- ❌ **MS1600, MS1800, MS2000, MS2000-D** ;
- ❌ **MS3000** ;
- ❌ **MX450, MX1000**.

Le **MX3000** n’est pas déclaré compatible : la carte disponible s’arrête à PV4 alors que ce modèle peut comporter davantage d’entrées. Le stockage **DC1000** et les compteurs **TSOL-MG3-MS / DDZY422-D2** ne sont pas pris en charge par cet adaptateur de micro-onduleur.

## Installation

### Avec HACS

[![Ajouter TSUN Local à HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration)

Ou manuellement :

1. Dans HACS, ouvrez le menu **⋮** en haut à droite, puis **Dépôts personnalisés**.
2. Ajoutez `https://github.com/jptstar/tsun-local` avec le type **Integration**.
3. Cliquez sur **Ajouter**, puis ouvrez **TSUN Local**.
4. Cliquez sur **Télécharger** et choisissez la dernière version disponible.
5. Redémarrez Home Assistant.

Si la dernière version n’apparaît pas, ouvrez le menu du dépôt et sélectionnez **Actualiser les informations**.

### Installation manuelle

1. Copiez le dossier `custom_components/tsun_local` dans `/config/custom_components/` sur Home Assistant.
2. Redémarrez Home Assistant.
3. Ouvrez **Paramètres → Appareils et services → Ajouter une intégration**.
4. Recherchez **TSUN Local**.
5. Renseignez l’adresse IP, le port et le **SN inscrit sur l’étiquette du micro-onduleur**.

Le protocole local est détecté automatiquement lors de l’ajout de l’appareil.

## Plusieurs appareils

Plusieurs micro-onduleurs compatibles peuvent être ajoutés dans la même installation Home Assistant. Pour chaque appareil, relancez **Ajouter une intégration** et saisissez son adresse IP ainsi que son SN unique. Chaque entrée crée un appareil indépendant avec ses propres entités et son propre coordinateur de communication.

## Réglages depuis Home Assistant

Dans **Paramètres → Appareils et services → TSUN Local**, ouvrez le menu de l’appareil concerné :

- **Configurer** règle son intervalle normal, de 10 secondes à 5 minutes (30 secondes par défaut), ainsi que son intervalle hors ligne/nuit, de 1 à 60 minutes (5 minutes par défaut) ;
- **Reconfigurer** permet de modifier son adresse IP et son port TCP sans supprimer les entités ;
- chaque appareil possède son propre intervalle, indépendant des autres.

## Fonctionnement de nuit

Lorsque le micro-onduleur n’est plus alimenté, l’intégration le considère hors ligne sans répéter une erreur à chaque interrogation :

- les mesures instantanées (tension, courant, puissance et fréquence) deviennent indisponibles afin de ne pas afficher de valeurs périmées ;
- les compteurs d’énergie journaliers et totaux restent disponibles avec leur dernière valeur connue ;
- le diagnostic **Communication** passe hors ligne ;
- le compteur indique les échecs consécutifs et revient à zéro dès le réveil ;
- l’heure de la dernière communication réussie reste disponible ;
- les tentatives utilisent l’intervalle hors ligne/nuit configuré dans Home Assistant ;
- dès la première réponse du matin, l’intervalle configuré est restauré.

## Capteurs

L’intégration crée un appareil unique avec les mesures AC, 5 mesures par entrée PV détectée, la somme des puissances DC détectées, 4 capteurs de diagnostic et un état de connectivité.

Le nombre d’entrées PV est dynamique : PV1 est disponible dès la première lecture, puis PV2 à PV6 pour TITAN ou PV2 à PV4 pour GEN3/GEN3 PLUS sont ajoutées lorsqu’une mesure ou un compteur valide est observé. Une entrée découverte reste enregistrée dans Home Assistant.
