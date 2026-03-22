"""
Build script unifié pour la cartographie Fonds Vert PACA.
Supporte les millésimes 2023 et 2024 avec un pipeline unique.

Usage:
    python build_map_v2.py --year 2024
    python build_map_v2.py --year 2023
    python build_map_v2.py --year both

Données source : data.gouv.fr via MCP datagouv ou téléchargement direct.
"""

import argparse
import csv
import json
import urllib.request
import time
from collections import defaultdict
from pathlib import Path

# ============================================================
# CONFIGURATION PAR MILLÉSIME
# ============================================================
YEARS_CONFIG = {
    2023: {
        'csv_url': 'https://static.data.gouv.fr/resources/fonds-vert-liste-des-projets-subventionnes-en-2023/20240731-110636/fonds-vert-2023-export.csv',
        'csv_path': Path('data/fonds_vert_2023_source.csv'),
        'output_json': Path('data/paca_2023_map_data.json'),
        'output_js': Path('data_2023.js'),
        'col_demarche': 'nom_demarche_ds',
        'col_beneficiaire': 'nom_beneficiaire_principal',
    },
    2024: {
        'csv_url': 'https://static.data.gouv.fr/resources/fonds-vert-liste-des-projets-subventionnes/20250731-095516/fonds-vert-2024-export.csv',
        'csv_path': Path('data/fonds_vert_2024_source.csv'),
        'output_json': Path('data/paca_2024_map_data.json'),
        'output_js': Path('data_2024.js'),
        'col_demarche': 'demarche',
        'col_beneficiaire': 'raison_sociale_beneficiaire',
    },
}

# Colonnes communes (identiques 2023/2024)
COL_REGION = 'nom_region'
COL_DEPT = 'code_departement'
COL_DEPT_NOM = 'nom_departement'
COL_COMMUNE = 'code_commune'
COL_COMMUNE_NOM = 'nom_commune'
COL_PROJET = 'nom_du_projet'
COL_MONTANT = 'montant_engage'
COL_DOSSIER = 'numero_dossier_ds'

PACA_DEPTS = {'04', '05', '06', '13', '83', '84'}
REGION_PACA = "Provence-Alpes-Côte d'Azur"

# ============================================================
# CORRECTIONS PAR NUMÉRO DE DOSSIER (stables entre versions CSV)
# ============================================================
DOSSIER_CORRECTIONS = {
    # === 2024 : 4 HORS PACA ===
    '14719608': '13054',  # Paris → Marignane (titre: "Centre Ancien de Marignane")
    '17574680': '06085',  # Nancy → Mougins (titre: "chemin de l'Espagnol à Mougins")
    '18113567': '13077',  # Lyon → Port-de-Bouc (titre: "Friche Azur Chimie - Port de Bouc")
    '16726781': '84138',  # Nyons → Valréas (benef: SM Eygues en Aygues)
    # === 2024 : MARSEILLE (13055) mal codé ===
    '16474025': '04112',  # → Manosque (titre: "Lycée Esclangon - MANOSQUE")
    '17457171': '04143',  # → Oraison (titre: "site Lacroix à Oraison")
    '14026700': '04049',  # → Château-Arnoux (résumé: "Commune de Château Arnoux St Auban")
    '17963893': '06088',  # → Nice (titre: "Ilot Jean Médecin à NICE")
    '16954930': '06083',  # → Menton (titre: "Lycée Curie à MENTON")
    '11338517': '83098',  # → Le Pradet (titre: "station service - Le Pradet")
    '11816713': '83137',  # → Toulon (titre: "covoiturage Toulon-Cuers")
    # === 2024 : AIX (13001) mal codé ===
    '15728266': '04245',  # → Volx (titre: "Volx Cave Coopérative")
    '17029299': '84031',  # → Carpentras (approx: CITTA, dept 84)
    # === 2024 : 8 PAPI Côtiers des Maures (13109 Le Tholonet → 83086 Le Muy) ===
    '11833274': '83086',  # PAPI Maures action 7.4a
    '11833674': '83086',  # PAPI Maures action 7.3 (Pansard)
    '11833196': '83086',  # PAPI Maures action 7.3a (Batailler)
    '11833649': '83086',  # PAPI Maures action 7.2b (Pansard)
    '11731205': '83086',  # PAPI Maures (ripisylve)
    '11833121': '83086',  # PAPI Maures action 7.2a (Batailler)
    '11833617': '83086',  # PAPI Maures action 7.1b (Pansard)
    '11833705': '83086',  # PAPI Maures action 7.4b (Maravenne)
    # === 2024 : 2 nouvelles anomalies dept mismatch ===
    '13014757': '06095',  # Fréjus(83062) → Peymeinade (résumé: "centre ville de Peymeinade")
    '19905814': '83143',  # code 04135 → Vinon-sur-Verdon (titre: "digues à Vinon-sur-Verdon")
    # === 2024 : incertaine ===
    '18214898': '13055',  # Avignon(84007) → Marseille (Commission Durance, dept 13)
}

# === 2023 : corrections NULL → commune via titre/bénéficiaire ===
# Chargées depuis corrections_2023.json si présent
DOSSIER_CORRECTIONS_2023_FILE = Path('data/corrections_2023.json')

# ============================================================
# LABELS COURTS DÉMARCHES (unifié 2023/2024)
# ============================================================
DEMARCHE_SHORT = {
    # 2023 et 2024 communs
    "Rénovation énergétique des bâtiments publics locaux": "Rénov. énergétique",
    "Recyclage foncier": "Recyclage foncier",
    "Renaturation des villes et des villages": "Renaturation",
    "Rénovation des parcs de luminaires d'éclairage public": "Éclairage public",
    "Développement du covoiturage": "Covoiturage",
    "Ingénierie": "Ingénierie",
    "Appui aux collectivités de montagne soumises à des risques émergents": "Risques montagne",
    # 2023 spécifique
    "Renforcement des aides apportées par les PAPI et appui financier aux gestionnaires d'ouvrages dans le cadre de la GEMAPI": "PAPI/GEMAPI",
    "Accompagnement du déploiement des zones à faibles émissions mobilité (ZFE)": "ZFE mobilité",
    "Prévention des risques d'incendies de forêt et de végétation": "Incendies de forêt",
    "Soutien aux projets des Territoires d'industrie": "Terr. Industrie",
    "Tri à la source et valorisation des biodéchets": "Biodéchets",
    "Soutien aux autorités organisatrices de mobilités des territoires ruraux": "Mobilités rurales",
    "Accompagnement pour l'adaptation des territoires littoraux au recul du trait de côte": "Trait de côte",
    "Accompagnement de la stratégie nationale biodiversité 2030": "Biodiversité",
    # 2024 spécifique (noms légèrement différents)
    "Renforcement des aides apportées par les PAPI et appui financier aux collectivités, gestionnaires de digues, dans le cadre de la compétence GEMAPI": "PAPI/GEMAPI",
    "Territoires d'Industrie en transition écologique": "Terr. Industrie",
    "Soutien au tri à la source et à la valorisation des biodéchets": "Biodéchets",
    "Développement des mobilités durables en zones rurales": "Mobilités rurales",
}

DEPT_NAMES = {
    "04": "Alpes-de-Haute-Provence", "05": "Hautes-Alpes",
    "06": "Alpes-Maritimes", "13": "Bouches-du-Rhône",
    "83": "Var", "84": "Vaucluse",
}


# ============================================================
# UTILITAIRES
# ============================================================
def norm(s):
    """Normalise apostrophes typographiques."""
    return s.replace('\u2019', "'").replace('\u2018', "'") if s else ''


def clean(s):
    """Supprime caractères de contrôle."""
    return s.replace('\n', ' ').replace('\r', '').replace('\t', ' ').strip() if s else ''


def fmt_montant(n):
    if n >= 1e6:
        return f"{n/1e6:.1f} M€"
    if n >= 1e3:
        return f"{n/1e3:.0f} k€"
    return f"{n:.0f} €"


def download_csv(url, path):
    if path.exists():
        print(f"  CSV présent : {path}")
        return
    print(f"  Téléchargement depuis {url[:60]}...")
    path.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, path)
    print(f"  Téléchargé : {path} ({path.stat().st_size / 1e6:.1f} MB)")


def geocode_commune(code):
    """Géocode une commune via geo.api.gouv.fr. Retourne (lat, lng, pop) ou None."""
    try:
        url = f"https://geo.api.gouv.fr/communes?code={code}&fields=centre,population&limit=1"
        req = urllib.request.Request(url, headers={'User-Agent': 'FondsVert-PACA/2.0'})
        resp = urllib.request.urlopen(req, timeout=5)
        results = json.loads(resp.read())
        if results and 'centre' in results[0] and results[0]['centre']:
            c = results[0]['centre']['coordinates']
            return (c[1], c[0], results[0].get('population'))
    except Exception:
        pass
    return None


# ============================================================
# PIPELINE PRINCIPAL
# ============================================================
def build_year(year):
    cfg = YEARS_CONFIG[year]
    print(f"\n{'='*60}")
    print(f"  FONDS VERT {year} — BUILD PACA")
    print(f"{'='*60}")

    # 1. Télécharger CSV
    download_csv(cfg['csv_url'], cfg['csv_path'])

    # 2. Charger corrections spécifiques
    corrections = dict(DOSSIER_CORRECTIONS)
    if year == 2023 and DOSSIER_CORRECTIONS_2023_FILE.exists():
        with open(DOSSIER_CORRECTIONS_2023_FILE, 'r') as f:
            corr_2023 = json.load(f)
            for dossier, info in corr_2023.items():
                corrections[dossier] = info['code_commune']
        print(f"  Corrections 2023 chargées : {len(corr_2023)} dossiers")

    # 3. Parser CSV
    communes = defaultdict(lambda: {
        'count': 0, 'montant': 0, 'commune': '', 'dept': '',
        'code_dept': '', 'demarches': defaultdict(float), 'projets': []
    })
    stats = {'total': 0, 'paca': 0, 'corrected': 0, 'skipped': 0}

    col_dem = cfg['col_demarche']

    with open(cfg['csv_path'], 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get(COL_REGION, '').strip() != REGION_PACA:
                continue
            stats['paca'] += 1

            code = row.get(COL_COMMUNE, '').strip()
            dossier = row.get(COL_DOSSIER, '').strip()
            dept = row.get(COL_DEPT, '').strip()

            # Appliquer corrections par dossier
            if dossier in corrections:
                code = corrections[dossier]
                stats['corrected'] += 1
            elif code in ('', 'NULL', 'nan'):
                stats['skipped'] += 1
                continue
            elif code[:2] not in PACA_DEPTS:
                stats['skipped'] += 1
                continue

            # Parser montant
            try:
                m = (row.get(COL_MONTANT, '0') or '0').replace('\xa0', '').replace(' ', '').replace(',', '.')
                montant = float(m) if m else 0
            except ValueError:
                montant = 0

            # Démarche
            dem_raw = norm(row.get(col_dem, '') or '')
            dem_short = DEMARCHE_SHORT.get(dem_raw, dem_raw[:30] if dem_raw else 'Autre')

            # Agréger
            nom_commune = clean(row.get(COL_COMMUNE_NOM, '')).title()
            communes[code]['count'] += 1
            communes[code]['montant'] += montant
            communes[code]['demarches'][dem_short] += montant
            if not communes[code]['commune']:
                communes[code]['commune'] = nom_commune
            communes[code]['dept'] = DEPT_NAMES.get(dept, dept)
            communes[code]['code_dept'] = dept
            communes[code]['projets'].append({
                'nom': clean(row.get(COL_PROJET, '')),
                'montant': montant,
                'demarche_short': dem_short,
            })

    print(f"\n  Stats parsing :")
    print(f"    Lignes PACA : {stats['paca']}")
    print(f"    Corrigées   : {stats['corrected']}")
    print(f"    Ignorées    : {stats['skipped']}")
    print(f"    Communes    : {len(communes)}")

    # 4. Géocodage
    print(f"\n  Géocodage ({len(communes)} communes)...")
    cache_path = Path('data/geocode_cache.json')
    geo_cache = {}
    if cache_path.exists():
        with open(cache_path, 'r') as f:
            geo_cache = json.load(f)

    data = []
    geo_ok, geo_cached, geo_fail = 0, 0, 0
    for code in sorted(communes.keys(), key=lambda c: -communes[c]['montant']):
        c = communes[code]
        entry = {
            'code': code,
            'commune': c['commune'],
            'code_dept': c['code_dept'],
            'dept': c['dept'],
            'montant': round(c['montant'], 2),
            'count': c['count'],
            'demarche_short': max(c['demarches'], key=c['demarches'].get) if c['demarches'] else '',
            'projets': sorted(c['projets'], key=lambda p: -p['montant']),
        }

        if code in geo_cache:
            entry['lat'] = geo_cache[code]['lat']
            entry['lng'] = geo_cache[code]['lng']
            entry['population'] = geo_cache[code].get('population')
            geo_cached += 1
        else:
            result = geocode_commune(code)
            if result:
                lat, lng, pop = result
                entry['lat'] = lat
                entry['lng'] = lng
                entry['population'] = pop
                geo_cache[code] = {'lat': lat, 'lng': lng, 'population': pop}
                geo_ok += 1
            else:
                geo_fail += 1
            time.sleep(0.05)

        data.append(entry)

    # Sauvegarder cache
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, 'w') as f:
        json.dump(geo_cache, f, ensure_ascii=False)

    total_geo = sum(1 for d in data if 'lat' in d)
    print(f"    Cache  : {geo_cached}")
    print(f"    API    : {geo_ok}")
    print(f"    Échecs : {geo_fail}")
    print(f"    Total  : {total_geo}/{len(data)} ({total_geo/len(data)*100:.1f}%)")

    # 5. Sauvegarder JSON
    cfg['output_json'].parent.mkdir(parents=True, exist_ok=True)
    with open(cfg['output_json'], 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n  JSON : {cfg['output_json']}")

    # 6. Stats finales
    tm = sum(d['montant'] for d in data)
    tp = sum(d['count'] for d in data)
    print(f"\n  === RÉSULTAT {year} ===")
    print(f"  Communes : {len(data)}")
    print(f"  Projets  : {tp}")
    print(f"  Montant  : {fmt_montant(tm)}")

    return data


# ============================================================
# MAIN
# ============================================================
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Build Fonds Vert PACA map data')
    parser.add_argument('--year', choices=['2023', '2024', 'both'], default='both')
    args = parser.parse_args()

    years = [2023, 2024] if args.year == 'both' else [int(args.year)]
    for y in years:
        build_year(y)
