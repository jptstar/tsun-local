# Journal des modifications

Toutes les évolutions notables de ce projet sont documentées ici. Le projet suit le [versionnement sémantique](https://semver.org/lang/fr/).

## [1.1.3] - 2026-08-11

### Ajouté

- documentation complète en néerlandais, italien, espagnol, polonais et chinois simplifié.

### Modifié

- ajout d’un sélecteur commun des huit langues dans tous les README.

## [1.1.2] - 2026-08-11

### Ajouté

- traductions Home Assistant en néerlandais (`nl`), italien (`it`), espagnol (`es`), polonais (`pl`) et chinois simplifié (`zh-Hans`).

## [1.1.1] - 2026-08-11

### Modifié

- ajout du **MX500** à la liste des micro-onduleurs GEN3 / GEN3 PLUS disponibles pour essai et en attente de validation sur matériel réel.

## [1.1.0] - 2026-08-11

### Ajouté

- détection automatique du protocole local lors de l’ajout d’un appareil ;
- premier adaptateur GEN3 / GEN3 PLUS fondé sur la carte de registres 02B0 fournie ;
- détection progressive du nombre d’entrées PV : jusqu’à 6 pour TITAN et jusqu’à 4 pour GEN3 / GEN3 PLUS ;
- ajout dynamique dans Home Assistant des entités correspondant aux entrées PV détectées ;
- tests unitaires des enveloppes AP, CRC, requêtes, réponses, compteurs 32 bits et décodeurs des deux protocoles.

### Modifié

- la puissance DC totale additionne uniquement les entrées PV détectées ;
- les compteurs d’énergie restent disponibles hors ligne et la nuit, tandis que les mesures instantanées deviennent indisponibles ;
- la documentation de compatibilité distingue les appareils validés, disponibles pour essai et non pris en charge.

## [1.0.1] - 2026-08-11

### Modifié

- le port local par défaut `8899` est maintenant prérempli dans le formulaire Home Assistant et reste modifiable par l’utilisateur.

## [1.0.0] - 2026-08-10

### Ajouté

- première version publique du logiciel TSUN Local ;
- domaine Home Assistant générique et stable `tsun_local` ;
- interface commune pour des adaptateurs de protocoles extensibles ;
- première implémentation indépendante du protocole local 1511 pour le TSOL-MP3000 ;
- lectures AC et PV1 à PV6 ;
- puissance DC totale calculée comme somme des six puissances PV ;
- diagnostics de communication et gestion automatique du fonctionnement nocturne ;
- intervalles normal et hors ligne/nuit configurables pour chaque appareil ;
- prise en charge de plusieurs micro-onduleurs ;
- configuration et reconfiguration depuis Home Assistant ;
- traductions Home Assistant en français, anglais et allemand ;
- documentation GitHub en français, anglais et allemand ;
- licence GPL-3.0 et copyright de Jean-Philippe TESTART (jptstar).

[1.1.3]: https://github.com/jptstar/tsun-local/compare/v1.1.2...v1.1.3
[1.1.2]: https://github.com/jptstar/tsun-local/compare/v1.1.1...v1.1.2
[1.1.1]: https://github.com/jptstar/tsun-local/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/jptstar/tsun-local/compare/v1.0.1...v1.1.0
[1.0.1]: https://github.com/jptstar/tsun-local/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/jptstar/tsun-local/releases/tag/v1.0.0
