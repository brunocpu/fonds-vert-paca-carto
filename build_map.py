"""
Build script pour la cartographie Fonds Vert PACA 2024.

Usage: python build_map.py

Prérequis:
    - Python 3.10+
    - Accès internet (téléchargement CSV + géocodage geo.api.gouv.fr)
"""

import csv
import json
import urllib.request
from collections import defaultdict
from pathlib import Path

CSV_URL = "https://static.data.gouv.fr/resources/fonds-vert-liste-des-projets-subventionnes/20250731-095516/fonds-vert-2024-export.csv"
CSV_PATH = Path("data/fonds_vert_2024_source.csv")
OUTPUT_JSON = Path("data/paca_map_data_v3.json")

PACA_DEPTS = {'04', '05', '06', '13', '83', '84'}

# ============================================================
# CORRECTIONS DE GEOLOCALISATION
# Lignes CSV (1-indexed avec header) -> code_commune réel
# Détail et justifications dans data/corrections.json
# ============================================================
LINE_CORRECTIONS = {
    # 10 corrections depuis titre du projet
    8245: '13054',  # Paris -> Marignane ("Centre Ancien de Marignane")
    8440: '06085',  # Nancy -> Mougins ("chemin de l'Espagnol à Mougins")
    8780: '13077',  # Lyon -> Port-de-Bouc ("Friche Azur Chimie - Port de Bouc")
    8278: '04143',  # Marseille -> Oraison ("site Lacroix à Oraison")
    8281: '04245',  # Aix -> Volx ("Volx Cave Coopérative")
    8348: '04112',  # Marseille -> Manosque ("Lycée Esclangon - MANOSQUE")
    8437: '06088',  # Marseille -> Nice ("Ilot Jean Médecin à NICE")
    8466: '06083',  # Marseille -> Menton ("Lycée Curie à MENTON")
    8525: '83098',  # Marseille -> Le Pradet ("station service - Le Pradet")
    8635: '83137',  # Marseille -> Toulon ("covoiturage Toulon-Cuers")
    # 2 corrections depuis recherche web
    8276: '04049',  # Marseille -> Château-Arnoux (Résidence LAPIE, article mesinfos.fr)
    8661: '83098',  # Marseille -> Le Pradet (38 logements, site MFP)
    # 2 approximations
    8776: '84031',  # Aix -> Carpentras approx (CITTA, étude en Vaucluse)
    8553: '84138',  # Nyons (26) -> Valréas (SM Eygues, bassin versant 26/84)
    # 8 lignes PAPI Côtiers des Maures (Canal de Provence siège Le Tholonet -> Le Muy)
    8679: '83086', 8680: '83086', 8682: '83086', 8683: '83086',
    8685: '83086', 8686: '83086', 8690: '83086', 8695: '83086',
}

# Labels courts pour les mesures (doivent correspondre à ceux de la carte HTML)
DEMARCHE_SHORT = {
    "Rénovation énergétique des bâtiments publics locaux": "Rénov. énergétique",
    "Recyclage foncier": "Recyclage foncier",
    "Renaturation des villes et des villages": "Renaturation",
    "Rénovation des parcs de luminaires d'éclairage public": "Éclairage public",
    "Renforcement des aides apportées par les PAPI et appui financier aux collectivités, gestionnaires de digues, dans le cadre de la compétence GEMAPI": "PAPI/GEMAPI",
    "Accompagnement du déploiement des zones à faibles émissions mobilité (ZFE)": "ZFE mobilité",
    "Prévention des risques d'incendies de forêt et de végétation": "Incendies de forêt",
    "Territoires d'Industrie en transition écologique": "Terr. Industrie",
    "Soutien au tri à la source et à la valorisation des biodéchets": "Biodéchets",
    "Développement du covoiturage": "Covoiturage",
    "Développement des mobilités durables en zones rurales": "Mobilités rurales",
    "Ingénierie": "Ingénierie",
    "Appui aux collectivités de montagne soumises à des risques émergents": "Risques montagne",
}


def clean(s):
    """Supprime les caractères de contrôle d'une chaîne."""
    return s.replace('\n', ' ').replace('\r', '').replace('\t', ' ').strip() if s else ''


def norm(s):
    """Normalise les apostrophes typographiques en apostrophes droites."""
    return s.replace('\u2019', "'").replace('\u2018', "'") if s else ''


def download_csv():
    if CSV_PATH.exists():
        print(f"CSV présent : {CSV_PATH}")
        return
    print("Téléchargement du CSV depuis data.gouv.fr...")
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(CSV_URL, CSV_PATH)
    print(f"Téléchargé : {CSV_PATH} ({CSV_PATH.stat().st_size / 1e6:.1f} MB)")


def parse_csv():
    communes = defaultdict(lambda: {
        'count': 0, 'montant': 0, 'commune': '', 'dept': '',
        'code_dept': '', 'demarches': defaultdict(int), 'projets': []
    })
    stats = {'total': 0, 'corrected': 0}

    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            line = i + 2
            if row.get('nom_region') != "Provence-Alpes-Côte d'Azur":
                continue
            code = row.get('code_commune', '').strip()

            if line in LINE_CORRECTIONS:
                code = LINE_CORRECTIONS[line]
                stats['corrected'] += 1
            elif code[:2] not in PACA_DEPTS:
                continue

            try:
                m = (row.get('montant_engage', '0') or '0').replace('\xa0', '').replace(' ', '').replace(',', '.')
                montant = float(m) if m else 0
            except ValueError:
                montant = 0

            dem = row.get('demarche', '') or ''
            dem_short = DEMARCHE_SHORT.get(norm(dem), dem[:25] if dem else 'Autre')

            communes[code]['count'] += 1
            communes[code]['montant'] += montant
            communes[code]['commune'] = clean(row.get('nom_commune', ''))
            communes[code]['dept'] = clean(row.get('nom_departement', ''))
            communes[code]['code_dept'] = code[:2]
            communes[code]['demarches'][norm(dem)] += montant
            communes[code]['projets'].append({
                'nom': clean(row.get('nom_du_projet', ''))[:80],
                'montant': montant,
                'demarche': norm(dem),
                'demarche_short': dem_short,
            })
            stats['total'] += 1

    print(f"Projets PACA : {stats['total']} (corrigés : {stats['corrected']})")
    print(f"Communes : {len(communes)}")
    return communes


def geocode(communes):
    geocoded = {}
    codes = list(communes.keys())
    for i, code in enumerate(codes):
        try:
            url = f"https://geo.api.gouv.fr/communes/{code}?fields=centre,nom,population&format=json"
            with urllib.request.urlopen(url, timeout=5) as resp:
                data = json.loads(resp.read())
                if 'centre' in data and data['centre']['coordinates']:
                    geocoded[code] = {
                        'lat': data['centre']['coordinates'][1],
                        'lng': data['centre']['coordinates'][0],
                        'nom': data.get('nom', ''),
                        'population': data.get('population', 0),
                    }
        except Exception as e:
            print(f"  Échec géocodage {code} : {e}")
        if (i + 1) % 50 == 0:
            print(f"  Géocodé {i + 1}/{len(codes)}")
    print(f"Géocodé : {len(geocoded)}/{len(codes)}")
    return geocoded


def build_map_data(communes, geocoded):
    map_data = []
    for code, geo in geocoded.items():
        c = communes[code]
        top_dem = max(c['demarches'], key=c['demarches'].get) if c['demarches'] else ''
        top_dem_short = DEMARCHE_SHORT.get(top_dem, top_dem[:25] if top_dem else 'Autre')
        map_data.append({
            'lat': geo['lat'], 'lng': geo['lng'],
            'commune': geo['nom'] or c['commune'],
            'code': code, 'dept': c['dept'], 'code_dept': c['code_dept'],
            'count': c['count'], 'montant': c['montant'],
            'top_demarche': top_dem, 'demarche_short': top_dem_short,
            'projets': c['projets'],
            'population': geo.get('population', 0),
        })
    map_data.sort(key=lambda x: -x['montant'])

    total = sum(d['count'] for d in map_data)
    montant = sum(d['montant'] for d in map_data)
    print(f"Carte : {len(map_data)} communes, {total} projets, {montant / 1e6:.1f} M€")
    return map_data


if __name__ == '__main__':
    print("=" * 50)
    print("Cartographie Fonds Vert PACA 2024")
    print("=" * 50)

    download_csv()
    communes = parse_csv()
    geocoded = geocode(communes)
    map_data = build_map_data(communes, geocoded)

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(map_data, f, ensure_ascii=False, indent=2)
    print(f"JSON sauvegardé : {OUTPUT_JSON}")
    print("Terminé.")
