# Fonds Vert PACA — Cartographie interactive v1.6

Cartographie interactive des projets financés par le Fonds Vert en Provence-Alpes-Côte d'Azur (2023 + 2024), croisés avec les zonages et programmes nationaux (ZRR, PVD, ACV, Villages d'Avenir).

**[Voir la carte](https://brunocpu.github.io/fonds-vert-paca-carto/)**

Données ouvertes [data.gouv.fr](https://www.data.gouv.fr/datasets/fonds-vert-liste-des-projets-subventionnes) via connecteur MCP.

## Chiffres

| | 2023 | 2024 | 2023+2024 |
|---|---|---|---|
| Communes | 307 | 277 | 440 |
| Projets | 586 | 568 | 1 154 |
| Montant | 156,4 M€ | 138,1 M€ | 294,5 M€ |
| Géocodage | 100% | 100% | — |
| Bénéficiaires distincts (SIRENE) | — | — | 552 |

## Fonctionnalités

- **Sélecteur millésime** : 2023 / 2024 / 2023+2024 (défaut)
- **Recherche par portée** : pills cliquables `Tout / Projet / Bénéficiaire / Commune / Mesure` avec compteurs, badges de scope sur chaque résultat — **synchronisée avec la carte, les stats et l'export CSV**
- **Bénéficiaires canonicalisés** : libellé officiel INSEE résolu par SIREN (558 entités), -21 % de doublons éliminés
- **Filtres croisés** : département × mesure × zonage/programme
- **Filtre Zonage / Programme** : ZRR (484 communes), PVD (65), ACV (12), Villages d'Avenir (208)
- **Évolution 2023→2024** : dans les popups des communes présentes les deux années
- **€/habitant par département** : toggle dans le panel stats (bar chart comparatif)
- **Donut** : répartition par mesure (top 5 + "Autres")
- **Export CSV** : 1 ligne par projet (9 colonnes métier : Dépt → Commune → Mesure → Projet → Bénéficiaire → Subvention), format Excel FR (séparateur `;`, décimale virgule, BOM UTF-8)
- **Header dynamique** : compteurs mis à jour à chaque filtrage
- **Réinitialiser** : reset global de tous les filtres
- **Responsive mobile** : panneaux Filtres / Stats en off-canvas sous 768 px
- **Accessibilité AA** : contrastes WCAG, aria-labels, skip-link, navigation clavier
- **Bandeau « preuve de concept »** : mention non-officielle, liens data.gouv.fr et MCP data.gouv

## Sources de données

| Source | Dataset | Usage |
|---|---|---|
| Fonds Vert 2024 | `1fdc94e1-0f50-4d39-8be3-40ab381ee9c4` | Projets 2024 |
| Fonds Vert 2023 | `ac2da594-aea2-4b87-973f-03f406ec4cfd` | Projets 2023 |
| Croisement ANCT | `617322c7c8e7b27041570e71` | PVD, ACV, VA, TI, FS, Cités édu. |
| ZRR (COG 2021) | `5943d13588ee38742a95eb0c` | Zones de Revitalisation Rurale |
| geo.api.gouv.fr | API | Géocodage + population |
| recherche-entreprises.api.gouv.fr | API | Noms officiels INSEE par SIREN (canonicalisation bénéficiaires) |

## Pipeline

```
MCP datagouv → CSV national (2023 + 2024)
            → filtre PACA (6 départements)
            → corrections géolocalisation (24 dossiers 2024 + 113 NULL 2023)
            → géocodage geo.api.gouv.fr (442 communes, cache local)
            → fetch_siret_names.py (558 SIRENs → noms INSEE, cache local)
            → build_map_v2.py --year both
            → generate_combined_data_js.py → data.js
            → programmes_anct.js (ANCT + ZRR)
            → index.html (Leaflet, GitHub Pages)
```

## Fichiers

```
├── index.html                    # Carte interactive v1.6
├── data.js                       # Données combinées 2023+2024 (430 KB, +siren +bénéficiaire)
├── programmes_anct.js            # Zonages ANCT + ZRR par commune PACA (17 KB)
├── build_map_v2.py               # Pipeline unifié 2023+2024
├── generate_combined_data_js.py  # Génère data.js depuis les JSON
├── fetch_siret_names.py          # Fetch noms officiels INSEE par SIREN (cache)
├── init_data.py                  # One-shot : corrections_2023.json + geocode_cache.json
├── fix_cache.py                  # One-shot : re-encode cache latin-1→UTF-8
├── patch_cache_names.py          # One-shot : hardcode 11 noms API indisponibles
├── data/
│   ├── fonds_vert_2023_source.csv
│   ├── fonds_vert_2024_source.csv
│   ├── corrections_2023.json     # 113 corrections NULL 2023
│   ├── geocode_cache.json        # 442 communes géocodées + noms API
│   ├── siret_cache.json          # 558 entités SIRENE (nom officiel par SIREN)
│   ├── paca_2023_map_data.json   # 307 communes, 586 projets
│   └── paca_2024_map_data.json   # 277 communes, 568 projets
├── README.md
├── MCP_SETUP.md
└── .gitignore
```

## Retraitement des données sources

Les deux millésimes ont nécessité un travail de réparation pour atteindre 100 % de géocodage. Toutes les corrections sont versionnées et reproductibles.

### Canonicalisation des bénéficiaires (SIRENE)

Les CSV sources contiennent plusieurs libellés pour une même entité légale (ex. `AIX MARSEILLE PROVENCE BP MET` + `METROPOLE D'AIX-MARSEILLE-PROVENCE` = même SIREN 200054807, 29 projets). Sans canonicalisation, **51 % des projets étaient affectés** (144 entités multi-libellées).

Méthode : pour chaque SIREN (champ `siren` 2023 / `siret_beneficiaire` 2024), appel à l'API publique `recherche-entreprises.api.gouv.fr` → récupération du `nom_raison_sociale` officiel INSEE. Cache permanent dans `data/siret_cache.json`.

Impact : **699 → 552 bénéficiaires distincts** (−21 %). Le SIREN est aussi stocké dans `data.js` pour traçabilité.

### 2023 — 113 corrections (`data/corrections_2023.json`)

113 projets sans `code_commune` (champ NULL dans le CSV MTE) ont été rattachés à une commune réelle :

| Méthode | Nb | Description |
|---|---|---|
| `benef` | 73 | Rattachement via le bénéficiaire / EPCI (siège de la collectivité porteuse) |
| `dept_fallback` | 20 | Rattachement à la préfecture du département quand la commune ne peut pas être ciblée |
| `titre` | 13 | Commune déduite du titre du projet |
| `titre_fix` | 7 | Code commune corrigé à partir du titre (incohérence avérée) |

Sans ce travail, ces 113 projets seraient invisibles sur la carte.

### 2024 — 24 dossiers relocalisés (`DOSSIER_CORRECTIONS` dans `build_map_v2.py`)

Le champ `code_commune` pointe parfois sur le siège du bénéficiaire (SIRET) plutôt que sur le lieu réel du projet. Identification via le titre, le résumé et le bénéficiaire.

Impact notable : Marseille passe de 39,3 M€ à 27,8 M€, 8 projets étant en réalité portés par d'autres communes (Manosque, Oraison, Château-Arnoux, Nice, Menton, Le Pradet, Toulon, Volx…).

## Croisements clés

| Zonage/Programme | Communes PACA | Financées Fonds Vert | Couverture |
|---|---|---|---|
| ZRR | 484 | 193 | 39% |
| PVD | 65 | 54 | 83% |
| ACV | 12 | 12 | 100% |
| Villages d'Avenir | 208 | 110 | 52% |

## Build

```bash
# Données (cache complet, 0 appel API)
python fetch_siret_names.py        # one-shot, peuple data/siret_cache.json
python build_map_v2.py --year both
python generate_combined_data_js.py

# Déploiement
git add -A
git commit -m "v1.x: description"
git push
```

## Contexte

POC réalisé avec Claude + MCP (connecteurs data.gouv.fr, filesystem). Exercice de bout en bout : sourcing données ouvertes, pipeline Python, cartographie Leaflet, croisement inter-programmes, déploiement GitHub Pages.

## Licence

Données : Licence Ouverte 2.0 (data.gouv.fr) · Code : MIT
