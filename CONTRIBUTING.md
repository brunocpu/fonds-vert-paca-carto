# Contribuer

Merci de l'intérêt porté au POC. Toute aide est bienvenue, notamment pour les corrections de localisation, où la connaissance du terrain compte plus que l'expertise technique.

## Signaler une erreur de localisation

C'est le type de contribution le plus utile. Ouvrir une [issue GitHub](https://github.com/brunocpu/fonds-vert-paca-carto/issues/new?template=erreur-localisation.md) avec :

- La **commune actuellement affichée** sur la carte
- Le **titre exact du projet** (visible dans le popup) et le **bénéficiaire**
- La **commune attendue** + indice (résumé, document externe, connaissance du terrain…)

Exemple d'issue bien rédigée :

> Projet *« Travaux de restauration du torrent de Réallon à Savines-le-Lac »* (bénéficiaire CC Serre-Ponçon) affiché sur Embrun, devrait être sur Savines-le-Lac : l'investissement physique est à Savines-le-Lac selon le titre du projet.

## Signaler un bug technique

Ouvrir une [issue GitHub](https://github.com/brunocpu/fonds-vert-paca-carto/issues/new?template=bug.md) avec :

- Navigateur + version
- Étapes pour reproduire
- Comportement attendu vs. observé
- Capture d'écran si pertinent

## Proposer une amélioration

[Issue GitHub](https://github.com/brunocpu/fonds-vert-paca-carto/issues/new?template=suggestion.md), décrire le besoin, l'utilité, l'effort estimé si possible. Les propositions méthodologiques (couverture P113 biodiversité, refresh ANCT COG 2025, etc.) sont prioritaires.

## Si tu veux proposer une PR

1. Fork du repo, branche dédiée (`feat/...`, `fix/...`, `docs/...`).
2. Tester localement : `python build_map.py --year both && python generate_combined_data_js.py`, puis ouvrir `index.html` dans un navigateur.
3. Mettre à jour le `CHANGELOG.md` si la modification est utilisateur-visible.
4. Ouvrir la PR avec un message clair, en français, préfixé par `feat:`, `fix:`, `docs:`, `ui:`, ou `vX.X:` pour une version.
5. La doctrine de localisation (voir [`METHODOLOGIE.md`](METHODOLOGIE.md)) est volontairement stricte ; toute proposition de relocalisation doit citer le titre du projet et le bénéficiaire.

## Conventions du repo

- **Langue** : français pour les messages de commit, le code peut rester en français aussi pour les noms de variables métier (commune, demarche, beneficiaire) — c'est volontaire pour la lisibilité du domaine.
- **Encodage** : UTF-8 sans BOM partout sauf les CSV exportés (BOM pour Excel français).
- **Format commit** : `<type>: <description courte en minuscules>` (cf. conventional commits) ou `vX.X: <résumé>` pour une release.
- **Données** : les corrections de localisation sont versionnées dans `data/corrections_2023.json` (2023) ou `DOSSIER_CORRECTIONS` dans `build_map.py` (2024). Chaque entrée doit être commentée avec la justification textuelle.

## Limites des contributions acceptées

Ce repo est un POC personnel ; il n'a pas vocation à devenir un outil officiel. Les contributions sont acceptées au cas par cas, sans engagement de cadence de merge. Les corrections de données factuelles (localisation, codes INSEE) sont les plus simples à traiter quand elles arrivent.
