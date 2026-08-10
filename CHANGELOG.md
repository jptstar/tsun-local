# Journal des modifications

Toutes les évolutions notables de ce projet sont documentées ici. Le projet suit le [versionnement sémantique](https://semver.org/lang/fr/).

## [1.0.0] - 2026-08-10

### Ajouté

- première version publique du logiciel TSUN Local ;
- domaine Home Assistant générique et stable `tsun_local` ;
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

[1.0.0]: https://github.com/jptstar/tsun-local/releases/tag/v1.0.0
