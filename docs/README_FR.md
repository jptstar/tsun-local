# TSUN Local — intégration locale Home Assistant

[English](../README.md) | [Français](README_FR.md) | [Deutsch](README_DE.md) | [Nederlands](README_NL.md) | [Italiano](README_IT.md) | [Español](README_ES.md) | [Polski](README_PL.md) | [简体中文](README_ZH.md)

[![Version GitHub](https://img.shields.io/github/v/release/jptstar/tsun-local)](https://github.com/jptstar/tsun-local/releases)

<p align="center">
  <img src="https://raw.githubusercontent.com/jptstar/tsun-local/main/custom_components/tsun_local/brand/icon@2x.png" width="160" alt="Icône indépendante TSUN Local">
</p>

> **Projet non officiel** — Cette intégration communautaire indépendante n’est ni développée, ni approuvée, ni maintenue par TSUN. Elle n’est affiliée à TSUN d’aucune manière. TSUN et les noms de ses produits restent la propriété de leurs détenteurs respectifs. Toute demande d’assistance concernant cette intégration doit être adressée à son auteur et non à TSUN.

**TSUN Local** connecte directement à Home Assistant les micro-onduleurs TSUN compatibles présents sur le réseau local, sans proxy et sans service cloud. La version **1.3.3** prend en charge les **TSOL-MP3000** et **TSOL-MX500**, tous deux validés sur du matériel réel, et fournit des adaptateurs prêts à tester pour d’autres modèles TITAN, GEN3 et GEN3 PLUS.

## À propos du projet

J’ai initialement développé cette intégration pour le plaisir et pour ma propre installation Home Assistant. Comme de nombreux utilisateurs rencontrent des difficultés pour accéder localement à leur micro-onduleur TSUN, je la mets à disposition afin que tout le monde puisse en profiter.

Les retours matériels, résultats de diagnostic et signalements de bugs précis sont les bienvenus. Je peux investir un peu de temps pour améliorer la compatibilité lorsque les informations fournies sont exploitables, mais cela reste un loisir et non mon activité principale. Il est donc possible que je mette parfois du temps à répondre ou à apporter une correction.

## Fonctions principales

- interrogation entièrement locale en TCP, sans proxy ni dépendance au cloud ;
- sélection automatique du protocole local actuellement pris en charge ;
- découverte native par UDP complétée par une recherche TCP limitée ;
- détection automatique des entrées PV disponibles dans les cartes de registres validées ;
- tension, courant, fréquence, puissance, énergie journalière et énergie totale AC ;
- tension, courant, puissance, énergie journalière et énergie totale pour chaque entrée PV détectée ;
- puissance DC totale calculée à partir des puissances PV détectées ;
- alarmes brutes du micro-onduleur et état global d’alarme ;
- diagnostics de communication avec des intervalles distincts en fonctionnement normal, après erreur et hors ligne/nuit ;
- un bouton par appareil pour actualiser immédiatement les données ;
- plusieurs micro-onduleurs dans la même installation Home Assistant ;
- entités Home Assistant traduites en français, anglais, allemand, espagnol, italien, néerlandais, polonais et chinois simplifié.

## Compatibilité

- **Home Assistant 2026.3.0 ou version ultérieure**.

**Légende :** ✅ validé sur matériel réel · 🧪 adaptateur prêt pour les tests communautaires · 🔎 informations de registres ou captures matérielles supplémentaires nécessaires · ⏸️ hors périmètre pour le moment.

### Micro-onduleurs TITAN

| Entrées PV | Modèles | État | Remarques |
|---:|---|:---:|---|
| 6 | **TSOL-MP3000** | ✅ | Validé sur matériel réel |
| 6 | TSOL-MP2250, TSOL-MS3000 | 🧪 | Adaptateur 1511 prêt à tester |
| 6 | MP3680, MP3750, MP4000, MP4600, MP5000, MP6000 | 🔎 | Matériel à six entrées ; protocole local et carte des registres à confirmer par une capture matérielle |

### Micro-onduleurs GEN3 et GEN3 PLUS

| Entrées PV | Modèles | État | Remarques |
|---:|---|:---:|---|
| 1 | **TSOL-MX500** | ✅ | Validé sur matériel réel |
| 1 | MX400, MX450, MS300, MS350, MS400, MS400-D | 🧪 | Adaptateur 02B0 prêt à tester |
| 2 | MX800, MX900, MX1000, MS600, MS700, MS800, MS600-D, MS700-D, MS800-D | 🧪 | Adaptateur 02B0 prêt à tester |
| 4 | MX2250, MS1600, MS1800, MS2000, MS2000-D | 🧪 | Adaptateur 02B0 prêt à tester |
| 6 | MS3000, MX2400, MX2500, MX2700, MX3000/MX3000D, MX3300 | 🔎 | La carte 02B0 disponible s’arrête actuellement à PV4 |

## Installation

### Avec HACS

[![Ajouter TSUN Local à HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration)

Ou manuellement :

1. Dans HACS, ouvrez le menu **⋮**, puis **Dépôts personnalisés**.
2. Ajoutez `https://github.com/jptstar/tsun-local` avec le type **Integration**.
3. Ouvrez **TSUN Local**, cliquez sur **Télécharger** et choisissez la dernière version.
4. Redémarrez Home Assistant.

Si une nouvelle version n’apparaît pas, ouvrez le menu du dépôt puis sélectionnez **Actualiser les informations**.

### Installation manuelle

1. Copiez `custom_components/tsun_local` dans `/config/custom_components/`.
2. Redémarrez Home Assistant.
3. Ouvrez **Paramètres → Appareils et services → Ajouter une intégration**.
4. Recherchez **TSUN Local**.

## Ajouter un appareil

TSUN Local peut rechercher automatiquement les micro-onduleurs présents sur le réseau local. Vous pouvez également saisir manuellement leur adresse IP. Le port TCP `8899` est proposé par défaut et reste modifiable.

Le protocole utilisé et le **SN** numérique sont détectés automatiquement. Si nécessaire, le SN peut être saisi manuellement depuis la page locale ou l’étiquette de l’appareil. Il est distinct du **SN Micro-onduleur** alphanumérique.

Si l’appareil se trouve sur un autre VLAN et n’est pas détecté, indiquez son sous-réseau au format CIDR ou utilisez la configuration manuelle.

Plusieurs micro-onduleurs peuvent être ajoutés. Chaque appareil dispose de ses propres entités et paramètres d’actualisation.

## Réglages d’interrogation

Dans **Paramètres → Appareils et services → TSUN Local**, ouvrez **Configurer** pour l’appareil concerné :

- intervalle normal : de 10 secondes à 5 minutes, 20 secondes par défaut ;
- intervalle de nouvelle tentative après une erreur : de 10 secondes à 5 minutes, 20 secondes par défaut ;
- intervalle hors ligne/nuit : de 1 à 60 minutes, 5 minutes par défaut ;
- échecs consécutifs avant le passage hors ligne : de 1 à 20, 3 par défaut.

Utilisez **Reconfigurer** pour modifier l’adresse IP ou le port TCP sans supprimer les entités existantes.

Le bouton **Actualiser les données** lance immédiatement une lecture complète du micro-onduleur concerné sans modifier les intervalles configurés. Si un autre appareil TSUN est en cours de lecture, l’actualisation manuelle attend la fin de cette interrogation.

## Entités

L’intégration crée un appareil Home Assistant pour chaque micro-onduleur configuré. Les identifiants techniques des entités restent en anglais tandis que leurs noms affichés sont traduits.

Les nouveaux identifiants utilisent des clés anglaises stables comme `ac_power`, `pv1_current` et `pv1_energy_total`. Un identifiant déjà enregistré par Home Assistant avec une ancienne version n’est volontairement pas renommé automatiquement, car cela pourrait casser des tableaux de bord ou des automatisations ; il peut être modifié manuellement dans les paramètres de l’entité.

Les données disponibles comprennent :

- les mesures instantanées et compteurs d’énergie AC ;
- cinq mesures pour chaque entrée PV détectée ;
- la puissance DC totale calculée ;
- quatre diagnostics de communication, plus les capteurs de diagnostic **SN**, **SN Micro-onduleur**, version du firmware et adresse MAC du logger ;
- un capteur binaire de connectivité **Micro-onduleur en ligne** ;
- un état global d’alarme et les registres bruts propres au protocole ;
- un bouton manuel **Actualiser les données**.

La détection des entrées PV est progressive. TITAN peut exposer PV1 à PV6 avec la carte 1511 actuelle. GEN3/GEN3 PLUS peut exposer PV1 à PV4 avec la carte 02B0 actuelle. Une fois découverte, une entrée reste enregistrée dans Home Assistant.

### Alarmes du micro-onduleur

Les alarmes internes sont distinctes des échecs de communication :

- TITAN/1511 expose quatre mots globaux, quatre mots secondaires et un mot brut pour chaque entrée PV détectée ;
- GEN3/GEN3 PLUS/02B0 expose les quatre registres bruts ERR1 à ERR4 ;
- chaque diagnostic brut indique sa valeur décimale, sa valeur hexadécimale et l’adresse du registre ;
- toute valeur brute non nulle active le capteur binaire global **Alarme de l’onduleur** ;
- si le bloc complet ne peut pas être lu, l’état global devient indisponible au lieu d’indiquer à tort qu’aucune alarme n’est active.

Les manuels publiés décrivent des catégories de défaut, mais aucun document public trouvé à ce jour ne définit une correspondance registre/bit fiable pour toutes les familles prises en charge. TSUN Local conserve donc les valeurs inconnues sous forme brute plutôt que d’afficher une description non vérifiée.

Les catégories documentées comprennent notamment les tensions ou courants PV anormaux, l’absence ou l’anomalie de tension/fréquence du réseau, la surchauffe, les défauts de terre ou d’isolement et les défauts internes du micro-onduleur. Elles restent uniquement informatives tant que leur relation avec chaque registre brut n’est pas confirmée.

## Fonctionnement de nuit et hors ligne

Lorsque le micro-onduleur alimenté par les panneaux ne répond plus la nuit :

Tant que le seuil configurable n’est pas atteint, les dernières valeurs restent disponibles et les nouvelles tentatives utilisent l’intervalle après erreur. Lorsque le seuil est atteint (3 échecs par défaut), l’appareil passe hors ligne et utilise l’intervalle hors ligne/nuit. La première réponse réussie remet immédiatement le compteur à zéro et rétablit l’intervalle normal.

- les tensions, courants, puissances et fréquences instantanés deviennent indisponibles ;
- l’état et les registres bruts d’alarme deviennent indisponibles ;
- les compteurs d’énergie journaliers et totaux conservent leur dernière valeur ;
- **Micro-onduleur en ligne** se désactive et le compteur d’échecs augmente ;
- l’intervalle hors ligne/nuit plus lent est utilisé ;
- l’intervalle normal revient après la première réponse réussie.

## Fonctionnement local et accès au cloud

TSUN Local ne contacte lui-même aucun service cloud TSUN. Une fois installé, il lit directement la télémétrie de l’appareil sur le réseau local.

L’intégration ne désactive pas la communication internet ou cloud propre au micro-onduleur. Pour une isolation internet complète, il faut la configurer sur le routeur ou le pare-feu tout en conservant l’accès local de Home Assistant à l’adresse IP et au port TCP de l’appareil.

## Tests communautaires et diagnostics

Les modèles marqués 🧪 sont réellement prêts à être essayés. Un test réussi comme un échec est utile : seules les remontées sur du matériel réel permettent de confirmer les différences entre modèles ou versions de micrologiciel.

Si l’intégration est déjà configurée :

1. Ouvrez **Paramètres → Appareils et services → TSUN Local**.
2. Activez les journaux de débogage depuis le menu de l’intégration, reproduisez le problème une fois, puis désactivez-les.
3. Téléchargez les diagnostics depuis la même page d’intégration ou depuis la page de l’appareil.
4. Ouvrez un [rapport de compatibilité](https://github.com/jptstar/tsun-local/issues/new/choose) en indiquant le modèle exact, la version du micrologiciel, la version de TSUN Local et en joignant le fichier téléchargé.

Si la configuration ne peut pas aboutir, lancez la capture autonome depuis une copie de ce dépôt :

```bash
python3 tools/diagnose_device.py --host ADRESSE_IP
```

Le SN numérique est demandé de manière interactive et ne reste pas dans l’historique de la commande. Le fichier `tsun_local_diagnostic.json` généré contient les mesures décodées et une courte trace circulaire des requêtes et réponses internes au protocole. Il ne contient **ni l’adresse IP, ni le SN, ni l’adresse MAC du logger, ni l’enveloppe AP**. Vérifiez-le avant de le partager, car les valeurs de production et d’énergie restent visibles.

Les réponses capturées peuvent être relues localement sans disposer du micro-onduleur :

```bash
python3 tools/replay_diagnostic.py tsun_local_diagnostic.json
```

Les cartes de registres disponibles constituent une base sérieuse, mais elles ne garantissent pas un comportement identique sur chaque modèle ou micrologiciel non testé. Cette capture relisible permet d’apporter des corrections ciblées sans accéder à distance au réseau d’un autre utilisateur.

## Évolutions possibles

Les idées suivantes ne sont volontairement pas encore activées et nécessitent une validation avant implémentation :

- les seuils de protection réseau sous forme de diagnostics en lecture seule ;
- le coefficient de sortie 02B0 sous forme de pourcentage en lecture seule ;
- des notifications ou réparations Home Assistant pour les alarmes persistantes ;
- les descriptions traduites des défauts lorsque la correspondance des registres et bits aura été confirmée ;
- d’autres adaptateurs locaux pour de futures familles de micro-onduleurs TSUN.

Aucune commande d’écriture ou de contrôle ne sera ajoutée sans protections explicites et validation sur matériel réel.

## Auteur

Jean-Philippe TESTART (`jptstar`)

## Licence

Copyright © 2026 Jean-Philippe TESTART (jptstar).

Ce projet est distribué sous la licence **GNU General Public License v3.0 ou ultérieure** (`GPL-3.0-or-later`). Les versions modifiées ou redistribuées doivent respecter cette licence et conserver les mentions de copyright et de licence. Consultez [LICENSE](LICENSE).

La licence couvre uniquement cette implémentation indépendante. Elle ne confère aucun droit sur les marques, logos, logiciels ou produits de TSUN. Ce projet reste non officiel et sans affiliation avec TSUN.
