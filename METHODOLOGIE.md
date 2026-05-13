# Méthodologie — Cartographie Fonds Vert PACA

Ce document expose la méthodologie de retraitement appliquée aux données publiques pour produire la cartographie. Il accompagne la fiche de réutilisation sur data.gouv.fr et complète le `README.md`.

## Statut

Preuve de concept réalisée à titre personnel. Données publiques, code et corrections versionnés sous licence MIT. Ce n'est pas un outil officiel ; les chiffres présentés ne se substituent pas aux publications du Ministère de la Transition écologique.

## Périmètre

### Couvert

- **Région** : Provence-Alpes-Côte d'Azur (6 départements : 04, 05, 06, 13, 83, 84)
- **Millésimes** : 2023 et 2024 (croisable, séparable, ou agrégé)
- **Programme budgétaire** : **P380** uniquement (subventions de droit commun du Fonds Vert)
- **Croisement** : zonages ANCT (PVD, ACV, Villages d'Avenir, ZRR)

### Non couvert (à signaler explicitement)

- **Programme P113 (biodiversité)** : le millésime 2024 du Fonds Vert comprend une ressource séparée `fonds-vert-p113-2024-export.csv` (~130 Ko) pour les crédits biodiversité dérivés de la Stratégie Nationale Biodiversité 2030. **Cette ressource n'a pas été ingérée dans le POC**. Les indicateurs présentés sur la mesure « Biodiversité » et les évolutions 2023→2024 sur cet axe sont donc partiels pour 2024. Cette omission est documentée publiquement.
- Autres régions, autres millésimes, autres programmes (P135 « habitat indigne », etc.).

## Sources de données

| Source | Dataset / Endpoint | Usage | Licence |
|---|---|---|---|
| Fonds Vert 2024 P380 | `1fdc94e1-0f50-4d39-8be3-40ab381ee9c4` | Projets 2024 | LO 2.0 |
| Fonds Vert 2023 P380 | `ac2da594-aea2-4b87-973f-03f406ec4cfd` | Projets 2023 | LO 2.0 |
| Croisement ANCT | `617322c7c8e7b27041570e71` | PVD, ACV, VA, TI, FS, Cités éducatives | LO 2.0 |
| ZRR (COG 2021) | `5943d13588ee38742a95eb0c` | Zones de Revitalisation Rurale | LO 2.0 |
| `geo.api.gouv.fr` | API publique | Géocodage commune (lat/lng, population) | LO 2.0 |
| `recherche-entreprises.api.gouv.fr` | API publique | Nom officiel INSEE par SIREN | LO 2.0 |

Les CSV sources sont stockés dans `data/` à l'état brut ; les caches API (géocodage, SIRENE) le sont aussi pour reproductibilité.

## Pipeline de retraitement

```
CSV national fonds_vert_{2023,2024}_source.csv
  ↓ filtre PACA (6 départements)
  ↓ application DOSSIER_CORRECTIONS (corrections de localisation)
  ↓ application corrections_2023.json (NULL → commune, codes INSEE)
  ↓ géocodage geo.api.gouv.fr (cache local)
  ↓ harmonisation noms bénéficiaires via SIRENE (cache local)
  ↓ agrégation par commune × mesure
  ↓ génération JSON intermédiaires
  ↓ generate_combined_data_js.py → data.js
  ↓ index.html (Leaflet)
```

Tout est reproductible avec `python build_map.py --year both && python generate_combined_data_js.py` (Python 3.10+, aucune dépendance externe).

## Doctrine de localisation

Un projet est rattaché à la commune où l'**investissement physique** est réalisé, pas au siège juridique du bénéficiaire (SIRET) — qui est ce que renvoie le CSV brut dans beaucoup de cas.

### Conséquence pratique

1. **Bénéficiaire ≠ lieu du projet** : quand le titre ou le résumé mentionne une commune différente du bénéficiaire (ex. *« lycée Paul Cézanne à Aix-en-Provence »* porté par la Région PACA dont le siège est à Marseille), on relocalise sur la commune mentionnée. Documenté dans `DOSSIER_CORRECTIONS` (millésime 2024) et `corrections_2023.json` (millésime 2023).
2. **Projets pluri-communaux portés par un syndicat ou une CC** (ex. 4 poteaux incendie sur Aubignosc/Simiane/Vachères, syndicat siégeant à Banon) : conservés au siège du porteur. Splitter dénaturerait la donnée source et le montant agrégé.
3. **Toponymes locaux** (*rue Châteauvieux* à Caderousse, *Pont de Briançon* à Jausiers, *Plan Porte d'Orange* à Carpentras, *Mas Saint Cézaire* à Arles) : pas de relocalisation. Ce sont des noms de lieux-dits internes à la commune réelle.
4. **Cas frontaliers ambigus** (ex. dossier 13075487 *Falaise de Lettret*, porté par la Commune de Châteauvieux voisine, ouvrage probablement à cheval sur la limite communale) : conservés au porteur juridique pour cohérence avec la logique SIRET.

### Retraitements techniques annexes

- **Hardcodage de 11 noms de communes** que l'API `geo.api.gouv.fr` ne renvoyait pas avec leur champ `nom` (Vitrolles, Pignans, Sigonce, Varages, Cabrières-d'Aigues, Lançon-Provence, Villeneuve, Saint-Pierre, Réallon, Marseille arrondissements). Noms vérifiés manuellement sur INSEE.
- **Re-encodage `latin-1 → UTF-8`** du cache de géocodage (corruption initiale d'encodage).

## Harmonisation des bénéficiaires (SIRENE)

Les CSV sources contiennent plusieurs libellés pour une même entité légale (ex. `AIX MARSEILLE PROVENCE BP MET` et `METROPOLE D'AIX-MARSEILLE-PROVENCE` sont le même SIREN `200054807`, 29 projets). Sans harmonisation, **51 % des projets étaient affectés par des doublons** (144 entités multi-libellées).

Méthode : pour chaque SIREN (champ `siren` 2023 / `siret_beneficiaire` 2024), appel à l'API publique `recherche-entreprises.api.gouv.fr` → récupération du `nom_raison_sociale` officiel INSEE. Cache permanent dans `data/siret_cache.json`.

Impact : **699 → 552 bénéficiaires distincts** (−21 %). Le SIREN est aussi stocké dans `data.js` pour traçabilité.

## Audit des localisations

Deux passes d'audit ont été menées (v1.7 puis v1.8) en croisant le **libellé** de chaque projet avec le **nom de commune** affecté, pour détecter les incohérences résiduelles non couvertes par les corrections initiales.

| Millésime | Mécanisme de correction | Nombre de dossiers | Montant total relocalisé |
|---|---|---|---|
| 2023 | `corrections_2023.json` (113 NULL réaffectés + 2 audit libellé + 21 codes INSEE rectifiés en silent fix) | 115 | — |
| 2024 | `DOSSIER_CORRECTIONS` dans `build_map.py` (24 initiales + 9 audit v1.7 + 8 audit v1.8) | 41 | ~10 M€ relocalisés vs. CSV brut |
| **Total dossiers retraités sur la localisation** | | **156** | |

Méthodologie d'audit :
- Extraction de tous les libellés post-corrections appliquées.
- Recherche des mentions de communes PACA dans les titres et résumés.
- Vérification manuelle de chaque hit (regex permissive génère faux positifs : toponymes locaux, noms d'EPCI, intercommunaux).
- Décisions appliquées dossier par dossier avec commentaire dans le code.

L'audit ne prétend pas être exhaustif : il repère les écarts détectables textuellement, pas les erreurs où le libellé est lui-même imprécis.

## Limites connues

### Liées aux données sources

- **P113 biodiversité 2024 non couvert** (cf. §Périmètre).
- **Zonage ANCT** : version COG 2021 utilisée. Le dataset a été mis à jour (COG 2025) le 13 avril 2026. Le POC n'a pas encore été re-fetché ; quelques communes peuvent voir leur statut ZRR évoluer dans la version officielle.
- **Population** : issue de l'API `geo.api.gouv.fr`, dernière mise à jour INSEE disponible au moment du fetch.

### Liées au retraitement

- **Doctrine de localisation discutable** : les cas frontaliers et pluri-communaux ont été tranchés par règle générique (porteur juridique). Une autre doctrine est défendable.
- **Audit libellé textuel** : ne détecte pas les erreurs sémantiques où le libellé du CSV est lui-même incomplet ou imprécis.
- **Aucun mécanisme de re-fetch automatique** : les corrections appliquées peuvent devenir obsolètes si les datasets sources sont republiés avec une structure différente.

### Liées à la stack technique

- **Couverture de tests limitée** : 7 tests d'invariants sur les données produites (corrections appliquées, totaux conservés, géocodage complet, harmonisation SIRENE, doctrine respectée). Pas de tests sur la couche UI (Leaflet, recherche, export CSV) — vérifications visuelles manuelles. Voir `tests/test_pipeline.py` et le workflow `tests` GitHub Actions.
- **GitHub Pages comme hébergement** : pas de SLA, pas de garantie de disponibilité.

## Usage de l'IA dans le pipeline

Pour transparence, distinction des étapes où l'IA intervient et où elle n'intervient pas :

| Étape | Usage IA | Risque d'erreur introduite |
|---|---|---|
| Téléchargement CSV, parsing, géocodage API | ❌ aucun, logique déterministe | Nul |
| Harmonisation bénéficiaires SIRENE | ❌ aucun, appel API déterministe | Nul |
| Définition `DOSSIER_CORRECTIONS` initiales (24 cas 2024) | ✅ proposition IA, validation humaine dossier par dossier | Faible — chaque correction est commentée avec la justification textuelle |
| Audit libellés v1.7 et v1.8 (29 dossiers relocalisés) | ✅ détection IA, validation humaine pour chaque cas | Modéré sur la détection initiale, faible après validation |
| Rédaction code et documentation | ✅ assistance IA (Claude / Claude Code) | Faible — code testé en exécution |
| Doctrine de localisation | ❌ décision humaine, IA dans rôle d'analyse | Nul |

**Risque résiduel principal** : les corrections de localisation reposent sur la lecture du libellé. Un libellé ambigu peut conduire à une décision discutable. Toutes les corrections sont commentées dans le code source ; un lecteur peut auditer chaque cas.

## Reproductibilité et signalement d'erreurs

- **Code source** : `https://github.com/brunocpu/fonds-vert-paca-carto` (MIT)
- **Données retraitées** : `data/` dans le repo (JSON et CSV bruts versionnés)
- **Caches API** : `data/geocode_cache.json` et `data/siret_cache.json` versionnés pour pipeline 100 % offline reproductible
- **Build** : `python build_map.py --year both && python generate_combined_data_js.py`
- **Signalements** : issues GitHub sur le repo

Toute correction proposée est bienvenue.

## Crédits

- Données : Ministère de la Transition écologique (Fonds Vert), ANCT, INSEE, Etalab — sous Licence Ouverte 2.0
- Code et retraitement : projet personnel, MIT
- Assistance IA : Claude (Anthropic) via Claude Code et le connecteur MCP data.gouv.fr
