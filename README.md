# Fonds Vert PACA — Cartographie interactive v1.4

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

## Fonctionnalités

- **Sélecteur millésime** : 2023 / 2024 / 2023+2024 (défaut)
- **Recherche plein texte** : sur les 1 154 noms de projets, communes, mesures
- **Filtres croisés** : département × mesure × zonage/programme
- **Filtre Zonage / Programme** : ZRR (484 communes), PVD (65), ACV (12), Villages d'Avenir (208)
- **Évolution 2023→2024** : dans les popups des communes présentes les deux années
- **€/habitant par département** : toggle dans le panel stats (bar chart comparatif)
- **Donut** : répartition par mesure (top 5 + "Autres")
- **Export CSV** : données filtrées, BOM UTF-8 pour Excel
- **Header dynamique** : compteurs mis à jour à chaque filtrage
- **Réinitialiser** : reset global de tous les filtres

## Sources de données

| Source | Dataset | Usage |
|---|---|---|
| Fonds Vert 2024 | `1fdc94e1-0f50-4d39-8be3-40ab381ee9c4` | Projets 2024 |
| Fonds Vert 2023 | `ac2da594-aea2-4b87-973f-03f406ec4cfd` | Projets 2023 |
| Croisement ANCT | `617322c7c8e7b27041570e71` | PVD, ACV, VA, TI, FS, Cités édu. |
| ZRR (COG 2021) | `5943d13588ee38742a95eb0c` | Zones de Revitalisation Rurale |
| geo.api.gouv.fr | API | Géocodage + population |

## Pipeline

```
MCP datagouv → CSV national (2023 + 2024)
            → filtre PACA (6 départements)
            → corrections géolocalisation (24 dossiers 2024 + 113 NULL 2023)
            → géocodage geo.api.gouv.fr (442 communes, cache local)
            → build_map_v2.py --year both
            → generate_combined_data_js.py → data.js
            → programmes_anct.js (ANCT + ZRR)
            → index.html (Leaflet, GitHub Pages)
```

## Fichiers

```
├── index.html                    # Carte interactive v1.4
├── data.js                       # Données combinées 2023+2024 (349 KB)
├── programmes_anct.js            # Zonages ANCT + ZRR par commune PACA (17 KB)
├── build_map_v2.py               # Pipeline unifié 2023+2024
├── generate_combined_data_js.py  # Génère data.js depuis les JSON
├── init_data.py                  # One-shot : corrections_2023.json + geocode_cache.json
├── fix_cache.py                  # One-shot : re-encode cache latin-1→UTF-8
├── patch_cache_names.py          # One-shot : hardcode 11 noms API indisponibles
├── data/
│   ├── fonds_vert_2023_source.csv
│   ├── fonds_vert_2024_source.csv
│   ├── corrections_2023.json     # 113 corrections NULL 2023
│   ├── geocode_cache.json        # 442 communes géocodées + noms API
│   ├── paca_2023_map_data.json   # 307 communes, 586 projets
│   └── paca_2024_map_data.json   # 277 communes, 568 projets
├── README.md
├── MCP_SETUP.md
└── .gitignore
```

## Corrections de géolocalisation (2024)

24 dossiers corrigés — le champ `code_commune` du CSV MTE pointe parfois sur le siège du bénéficiaire (SIRET) plutôt que sur le lieu réel du projet. Détail dans le code source (`DOSSIER_CORRECTIONS` dans `build_map_v2.py`).

Impact : Marseille passe de 39,3 M€ à 27,8 M€ (8 projets relocalisés vers leur commune réelle).

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
