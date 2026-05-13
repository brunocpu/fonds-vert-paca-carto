# Changelog

## v1.9 — 2026-05-13

Audit des localisations : 29 dossiers relocalisés sur la carte (~12 M€ de subventions affectées à une autre commune que celle du CSV brut), en deux passes successives. Filtre par mesure appliqué projet par projet (correction de bug : les popups affichaient parfois des projets hors filtre). Doctrine de localisation formalisée.

Structuration du repo : `LICENSE` (MIT), tests d'invariants (`pytest` + GitHub Actions), documentation publique (`METHODOLOGIE.md`, `CONTRIBUTING.md`), templates d'issues, Open Graph, rename `build_map_v2.py` → `build_map.py`. Refonte du bandeau « preuve de concept » : citation des APIs publiques utilisées, lien vers le code source, mention de l'usage d'IA et des erreurs résiduelles possibles. Relecture éditoriale globale.

**Compteurs** : 2023 : 303 communes, 586 projets, 156,4 M€ · 2024 : 282 communes, 568 projets, 138,1 M€.

## v1.6 — 2026-05-11

Harmonisation des noms de bénéficiaires via l'API SIRENE (`recherche-entreprises.api.gouv.fr`) : 699 → 552 bénéficiaires distincts (−21 %). Le bénéficiaire est désormais visible dans les popups, l'export CSV et la recherche. Recherche par portée (projet / bénéficiaire / commune / mesure). Export CSV au format Excel français (séparateur `;`, décimale virgule, encodage UTF-8 + BOM).

## v1.5 — 2026-03-22

Cœur fonctionnel : pipeline unifié 2023+2024, sélecteur millésime, recherche plein texte, filtres croisés département × mesure × zonage (ZRR, PVD, ACV, Villages d'Avenir), donut de répartition par mesure, évolution 2023→2024 dans les popups, toggle €/habitant par département, export CSV, responsive mobile, accessibilité WCAG AA. Bandeau « preuve de concept » initial.

## v1.0 — 2026-03-08

Première version : cartographie Fonds Vert 2024 PACA (568 projets, 138 M€), 25 corrections de géolocalisation appliquées (`DOSSIER_CORRECTIONS` initial).

## v0.x — 2026-02

Retraitement initial des données 2023 : 113 projets sans `code_commune` (champ NULL dans le CSV MTE) rattachés à une commune réelle via le bénéficiaire, le titre, ou la préfecture du département. Constitution du cache géocodage (≈ 440 communes) et préparation des structures de retraitement.
