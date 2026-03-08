# Cartographie Fonds Vert PACA 2024

Cartographie interactive des projets financés par le Fonds Vert en Provence-Alpes-Côte d'Azur (2024), produite à partir des données ouvertes de [data.gouv.fr](https://www.data.gouv.fr/datasets/fonds-vert-liste-des-projets-subventionnes) via le connecteur MCP.

## Résultat

- **276 communes** géocodées
- **568 projets** — zéro retrait, zéro exclusion
- **138,1 M€** d'engagements
- Carte interactive Leaflet (fond sombre CARTO)
- Filtres par département, popups détaillés, panel statistiques

## Pipeline

```
MCP datagouv -> search_datasets("fonds vert")
             -> list_dataset_resources
             -> download CSV (33 657 lignes, 7,8 MB)
             -> filtre PACA + agrégation par commune
             -> corrections géolocalisation (25 anomalies, voir ci-dessous)
             -> géocodage via geo.api.gouv.fr
             -> carte Leaflet HTML autonome
```

## Corrections de géolocalisation

Le champ `code_commune` du CSV MTE pointe parfois sur le **siège du bénéficiaire** (SIRET) plutôt que sur le lieu réel du projet. C'est un défaut structurel des données Chorus/Démarches Simplifiées.

**25 anomalies détectées, 25 corrigées, 0 exclusion.**

### Relocalisés depuis le titre du projet (10) — 16,8 M€

| Code CSV | Commune CSV | Commune réelle | Montant | Indice |
|---|---|---|---|---|
| 75056 | Paris | Marignane (13) | 4 300 k€ | "Centre Ancien de Marignane" |
| 54395 | Nancy | Mougins (06) | 1 200 k€ | "chemin de l'Espagnol à Mougins" |
| 13055 | Marseille | Manosque (04) | 5 217 k€ | "Lycée Esclangon – MANOSQUE" |
| 13055 | Marseille | Menton (06) | 2 098 k€ | "Lycée Curie à MENTON" |
| 13055 | Marseille | Nice (06) | 1 226 k€ | "Ilot Jean Médecin à NICE" |
| 13055 | Marseille | Toulon (83) | 1 065 k€ | "covoiturage Toulon-Cuers" |
| 13055 | Marseille | Oraison (04) | 946 k€ | "site Lacroix à Oraison" |
| 13055 | Marseille | Le Pradet (83) | 450 k€ | "station service - Le Pradet" |
| 13001 | Aix | Volx (04) | 250 k€ | "Volx Cave Coopérative" |
| 69123 | Lyon | Port-de-Bouc (13) | 31 k€ | "Friche Azur Chimie - Port de Bouc" |

### Relocalisés par recherche web (2) — 480 k€

| Code CSV | Commune CSV | Commune réelle | Montant | Source |
|---|---|---|---|---|
| 13055 | Marseille | Château-Arnoux (04) | 315 k€ | Article mesinfos.fr 27/08/2025 |
| 13055 | Marseille | Le Pradet (83) | 165 k€ | Site Maison Familiale de Provence |

### Relocalisés par approximation (2) — 228 k€

| Code CSV | Commune CSV | Rattachement | Montant | Justification |
|---|---|---|---|---|
| 13001 | Aix | Carpentras (84) | 225 k€ | CITTA, étude en Vaucluse, commune non identifiable |
| 26220 | Nyons | Valréas (84) | 2,5 k€ | SM Eygues, bassin versant frontalier 26/84 |

### PAPI Côtiers des Maures (7) — 1,8 M€

7 projets du Canal de Provence (siège Le Tholonet, 13) -> **Le Muy (83086)** — massif des Maures, intégralement dans le Var.

### Conservés en l'état (4) — 1,1 M€

- **La Garde (83062)** : "SOC GARDEENNE" = code_commune correct, dept_declared erroné
- **Avignon (84007)** : Commission Durance, multi-département, acceptable
- **Moustiers-Sainte-Marie (04135)** : PNR Verdon, zone 04/83, acceptable (2 projets)

### Impact

| Métrique | Données brutes | Après corrections |
|---|---|---|
| Marseille | 39,3 M€ (44 proj) | 27,8 M€ (36 proj) |
| Projets sur la carte | 568 | 568 |
| Communes | 277 | 276 |
| Montant total | 138,1 M€ | 138,1 M€ |

## Fichiers

```
├── README.md                            # Ce fichier
├── fonds-vert-paca-carte.html           # Carte interactive (ouvrir dans Chrome)
├── build_map.py                         # Script reproductible
├── data/
│   ├── fonds_vert_2024_source.csv       # CSV source MTE (téléchargé, gitignored)
│   ├── paca_map_data_v3.json            # Données corrigées par commune
│   └── corrections.json                 # Détail des 25 corrections
└── .gitignore
```

## Source des données

```bash
curl -L "https://static.data.gouv.fr/resources/fonds-vert-liste-des-projets-subventionnes/20250731-095516/fonds-vert-2024-export.csv" -o data/fonds_vert_2024_source.csv
```

Dataset : `66a215a463a9da4fb801b8cf` / Resource : `1fdc94e1-0f50-4d39-8be3-40ab381ee9c4`

## Contexte

POC réalisé dans le cadre d'un test du connecteur MCP data.gouv.fr v1.26.0 sur Claude Desktop. Coordinateur de programmes État en région PACA (SGAR).

## Licence

Données : Licence Ouverte 2.0 (data.gouv.fr) · Code : MIT
