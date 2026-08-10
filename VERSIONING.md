# Versionnement et publication

Le projet utilise le versionnement sémantique `MAJEURE.MINEURE.CORRECTIF` :

- **MAJEURE** : changement incompatible, notamment un nouveau domaine Home Assistant ;
- **MINEURE** : nouvelle fonctionnalité compatible ;
- **CORRECTIF** : correction compatible sans nouvelle fonctionnalité majeure.

Les tags Git sont préfixés par `v`, par exemple `v1.0.1`. La valeur sans préfixe doit être identique au champ `version` de `custom_components/tsun_local/manifest.json`.

## Publier une version

1. Modifier la version dans `manifest.json`.
2. Ajouter la version et sa date dans `CHANGELOG.md`.
3. Faire valider et fusionner la pull request dans `main`.
4. Créer et pousser le tag correspondant :

   ```bash
   git switch main
   git pull --ff-only
   git tag -a v1.1.3 -m "Version 1.1.3"
   git push origin v1.1.3
   ```

5. Le workflow `release.yml` vérifie automatiquement la concordance du tag, du manifeste et du journal, puis crée la GitHub Release utilisée par HACS.

Ne jamais déplacer ou réutiliser un tag déjà publié. Toute correction ultérieure reçoit un nouveau numéro de version.
