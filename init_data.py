"""
Script one-shot : écrit corrections_2023.json et geocode_cache.json dans data/
À exécuter une seule fois pour initialiser les fichiers de données.
"""
import json
import csv
import urllib.request
import time
from pathlib import Path
from collections import defaultdict

# ============================================================
# ÉTAPE 1 : Générer corrections_2023.json
# ============================================================
print("=== Génération corrections_2023.json ===")

CSV_2023_URL = 'https://static.data.gouv.fr/resources/fonds-vert-liste-des-projets-subventionnes-en-2023/20240731-110636/fonds-vert-2023-export.csv'
CSV_2023_PATH = Path('data/fonds_vert_2023_source.csv')

if not CSV_2023_PATH.exists():
    print("  Téléchargement CSV 2023...")
    CSV_2023_PATH.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(CSV_2023_URL, CSV_2023_PATH)

null_rows = []
with open(CSV_2023_PATH, 'r', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        if row['nom_region'].strip() == "Provence-Alpes-Côte d'Azur" and row['code_commune'].strip() in ('', 'NULL'):
            null_rows.append(row)

print(f"  {len(null_rows)} projets NULL à corriger")

# Mapping bénéficiaire → commune (siège EPCI)
BENEF_MAPPING = {
    'METROPOLE NCA': ('06088', 'Nice'),
    'AIX MARSEILLE PROVENCE': ('13055', 'Marseille'),
    'MET TOULON PROVENCE': ('83137', 'Toulon'),
    'CA DU GRAND AVIGNON': ('84007', 'Avignon'),
    'CA DRACENIE': ('83050', 'Draguignan'),
    'CA DES PAYS DE LERINS': ('06029', 'Cannes'),
    'CA SOPHIA ANTIPOLIS': ('06004', 'Antibes'),
    'CA PAYS DE GRASSE': ('06069', 'Grasse'),
    'CC ALPES D AZUR': ('06114', 'Puget-Théniers'),
    'CA ARLES CRAU CAMARGUE': ('13004', 'Arles'),
    'CC GUILLESTROIS': ('05065', 'Guillestre'),
    'CC SERRE-PONCON': ('05046', 'Embrun'),
    'SYEP EMBRUNAIS': ('05046', 'Embrun'),
    'CC DU BRIANCONNAIS': ('05023', 'Briançon'),
    'PETR DU GRAND BRIANCONNAIS': ('05023', 'Briançon'),
    'CC DU SISTERONAIS': ('04209', 'Sisteron'),
    'CC PAYS DE FORCALQUIER': ('04088', 'Forcalquier'),
    'CA PROVENCE-ALPES-AGGLO': ('04112', 'Manosque'),
    "CC VALLEE DE L'UBAYE": ('04019', 'Barcelonnette'),
    'CC ALPES PROVENCE VERDON': ('04039', 'Castellane'),
    'CA DURANCE LUBERON VERDON': ('04112', 'Manosque'),
    'CC DU PAYS D APT': ('84003', 'Apt'),
    'CA LES SORGUES DU COMTAT': ('84080', 'Pernes-les-Fontaines'),
    "CC D' AYGUES-OUVEZE": ('84035', 'Courthézon'),
    'CC PAYS DES SORGUES': ('84069', "L'Isle-sur-la-Sorgue"),
    'CC VAISON VENTOUX': ('84137', 'Vaison-la-Romaine'),
    'SIERT ANNOT ENTREVAUX': ('04008', 'Annot'),
    'SYNDMC PROVENCE VERTE': ('83023', 'Brignoles'),
    'SYNDMC MASSIF DES MAURES': ('83031', 'Collobrières'),
    'SM PNR VERDON': ('04039', 'Castellane'),
    'SMIGIBA': ('05023', 'Briançon'),
    'SYNDICAT MIXTE DU PNRQ': ('05065', 'Guillestre'),
    'SI GUIL-DURANCE': ('05046', 'Embrun'),
    'SMIAGE MARALPIN': ('06088', 'Nice'),
    'SICASIL': ('06029', 'Cannes'),
    'HABITATIONS DE HAUTE-PROVENCE': ('04112', 'Manosque'),
    'EPAGE HUVEAUNE': ('13055', 'Marseille'),
    'SYNDMC EPAGE MENELIK': ('13055', 'Marseille'),
    'ASYMIX SYMADREM': ('13004', 'Arles'),
    'ASCO ARROSANTS DE LA CRAU': ('13029', 'Fos-sur-Mer'),
    'SM AMENAGEMENT VALLEE DE LA DURANCE': ('84031', 'Cavaillon'),
    'SM DE L OUVEZE PROVENCALE': ('84137', 'Vaison-la-Romaine'),
    'CONSEIL ARCHITEC URBANISME TOULON': ('83137', 'Toulon'),
    "AGENCE D'URBANISME RHONE AVIGNON": ('84007', 'Avignon'),
    'DEMANDOLX': ('04068', 'Demandolx'),
    'BANON': ('04018', 'Banon'),
}

# Patterns titre
TITRE_PATTERNS = {
    'Draguignan': ('83050', 'Draguignan'),
    'Guillestre': ('05065', 'Guillestre'),
    'Trinité': ('06150', 'La Trinité'),
    'Chorges': ('05040', 'Chorges'),
    'Savines': ('05161', 'Savines-le-Lac'),
    'Gioberney': ('05071', 'La Chapelle-en-Valgaudémar'),
    'Mont Vial': ('06084', 'Malaussène'),
    'Cannes': ('06029', 'Cannes'),
    'Briançon': ('05023', 'Briançon'),
    'Vaison': ('84137', 'Vaison-la-Romaine'),
    'Rousset': ('05124', 'Rousset'),
    'Argenton': ('04094', 'Le Fugeret'),
}

# Post-corrections titre (améliorations)
TITRE_FIXES = {
    'Fos-sur-Mer': ('13029', 'Fos-sur-Mer'),
    'Luberon': ('84003', 'Apt'),
    'Mont-Ventoux': ('84012', 'Bédoin'),
    'Mandelieu': ('06079', 'Mandelieu-la-Napoule'),
    'Vachères': ('04224', 'Vachères'),
    'Vergières': ('13098', 'Saint-Martin-de-Crau'),
    'Bédarrides': ('84016', 'Bédarrides'),
}

DEPT_CHEFLIEU = {
    '04': ('04070', 'Digne-les-Bains'), '05': ('05061', 'Gap'),
    '06': ('06088', 'Nice'), '13': ('13055', 'Marseille'),
    '83': ('83137', 'Toulon'), '84': ('84007', 'Avignon'),
}

corrections = {}
for row in null_rows:
    dept = row['code_departement'].strip()
    titre = row['nom_du_projet'].strip()
    benef = row['nom_beneficiaire_principal'].strip()
    montant = float(row['montant_engage'] or 0)
    dossier = row['numero_dossier_ds'].strip()

    found = None
    source = ''

    # 1. Titre patterns
    for pattern, (code, commune) in TITRE_PATTERNS.items():
        if pattern in titre:
            found = (code, commune)
            source = f'titre:"{pattern}"'
            break

    # 2. Bénéficiaire patterns
    if not found:
        for pattern, (code, commune) in BENEF_MAPPING.items():
            if pattern in benef:
                found = (code, commune)
                source = f'benef:"{pattern}"'
                break

    # 3. Fallback dept
    if not found and any(x in benef for x in ['DEP ', 'SDIS ', 'REG ', 'SYNDICAT D ENERGIE', 'ASYMIX NTIC SICTIAM', 'ASYMIX PARC NATUREL', 'FED DEP', 'SM DE GESTION DU PNR']):
        code, commune = DEPT_CHEFLIEU[dept]
        found = (code, commune)
        source = f'dept_fallback:{dept}'

    if found:
        corrections[dossier] = {
            'code_commune': found[0], 'commune': found[1],
            'source': source, 'montant': montant, 'dept': dept
        }

# Post-corrections titre (améliorations)
for dossier, corr in corrections.items():
    if corr['source'].startswith('titre:'):
        continue
    row_match = next((r for r in null_rows if r['numero_dossier_ds'].strip() == dossier), None)
    if not row_match:
        continue
    titre = row_match['nom_du_projet'].strip()
    for keyword, (new_code, new_commune) in TITRE_FIXES.items():
        if keyword in titre and corr['code_commune'] != new_code:
            corr['code_commune'] = new_code
            corr['commune'] = new_commune
            corr['source'] = f'titre_fix:titre: "{keyword}"'
            break

Path('data').mkdir(exist_ok=True)
with open('data/corrections_2023.json', 'w', encoding='utf-8') as f:
    json.dump(corrections, f, ensure_ascii=False, indent=2)

print(f"  {len(corrections)} corrections sauvées dans data/corrections_2023.json")


# ============================================================
# ÉTAPE 2 : Construire geocode_cache.json depuis data.js existant + API
# ============================================================
print("\n=== Construction geocode_cache.json ===")

cache = {}

# Extraire coords du data.js existant (2024)
import re
with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
match = re.search(r'const DATA\s*=\s*(\[.*?\]);', content, re.DOTALL)
if match:
    data_2024 = json.loads(match.group(1))
    for d in data_2024:
        cache[d['code']] = {'lat': d['lat'], 'lng': d['lng'], 'population': d.get('population')}
    print(f"  {len(cache)} communes depuis data.js (2024)")

# Trouver les codes 2023 non encore dans le cache
all_codes_2023 = set()
with open(CSV_2023_PATH, 'r', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        if row['nom_region'].strip() == "Provence-Alpes-Côte d'Azur":
            code = row['code_commune'].strip()
            dossier = row['numero_dossier_ds'].strip()
            if code in ('', 'NULL') and dossier in corrections:
                code = corrections[dossier]['code_commune']
            if code and code != 'NULL':
                all_codes_2023.add(code)

missing = all_codes_2023 - set(cache.keys())
print(f"  {len(missing)} communes 2023 à géocoder via API")

for code in sorted(missing):
    try:
        url = f"https://geo.api.gouv.fr/communes?code={code}&fields=centre,population&limit=1"
        req = urllib.request.Request(url, headers={'User-Agent': 'FondsVert-PACA/2.0'})
        resp = urllib.request.urlopen(req, timeout=5)
        results = json.loads(resp.read())
        if results and 'centre' in results[0] and results[0]['centre']:
            c = results[0]['centre']['coordinates']
            cache[code] = {'lat': c[1], 'lng': c[0], 'population': results[0].get('population')}
    except Exception:
        pass
    time.sleep(0.05)

# Hardcoded pour les communes où l'API est instable
HARDCODED = {
    # Communes instables sur geo.api.gouv.fr — coords vérifiées manuellement
    '04008': (43.9667, 6.6667, 1100), '04023': (44.1083, 6.3917, 400),
    '04039': (43.8500, 6.5167, 1600), '04053': (44.0167, 5.9833, 600),
    '04067': (44.1167, 6.0500, 100), '04076': (43.9500, 6.8000, 857),
    '04079': (44.0833, 6.0167, 400), '04081': (44.1667, 6.0167, 400),
    '04091': (43.9533, 5.9750, 147), '04109': (43.8167, 5.8333, 700),
    '04120': (44.4028, 6.7639, 154), '04121': (43.9833, 6.2333, 837),
    '04124': (44.2833, 6.0667, 300), '04155': (44.1917, 6.3861, 120),
    '04160': (43.8828, 5.6611, 1556), '04162': (43.8500, 5.5333, 900),
    '04178': (44.0500, 5.7833, 2300), '04188': (43.8750, 5.7917, 3774),
    '04224': (43.9833, 5.6333, 307),
    '05010': (44.5167, 5.7500, 1400), '05019': (44.3833, 6.5000, 2800),
    '05024': (44.3833, 5.7167, 1500), '05031': (44.9333, 6.4833, 600),
    '05058': (44.5625, 6.0792, 40000), '05068': (44.3167, 5.9833, 600),
    '05074': (44.5167, 5.9500, 400), '05098': (44.6908, 6.5556, 957),
    '05161': (44.5261, 6.3928, 1069), '05164': (44.8667, 6.3833, 400),
    '05168': (44.3000, 5.9333, 300),
    '06005': (43.9333, 7.0667, 150), '06030': (43.5958, 7.0200, 42000),
    '06062': (44.0833, 7.5500, 300), '06064': (44.0833, 7.5500, 300),
    '06079': (43.5472, 6.9369, 22651), '06090': (43.7000, 7.2667, 5000),
    '06095': (43.6425, 6.8750, 8956), '06141': (43.9333, 7.0000, 300),
    '06150': (43.7389, 7.3100, 13000), '06157': (43.7228, 7.1122, 19328),
    '13010': (43.8833, 4.7500, 4000), '13029': (43.4375, 4.9444, 16584),
    '13039': (43.5300, 5.0400, 8000), '13044': (43.5167, 5.2333, 10000),
    '13098': (43.6431, 4.8578, 13872), '13114': (43.5667, 5.2833, 5000),
    '13118': (43.5500, 5.2333, 4000), '13201': (43.2965, 5.3698, 870000),
    '13208': (43.2800, 5.3800, 870000),
    '83003': (43.5950, 6.3706, 903), '83008': (43.5617, 6.6900, 2836),
    '83017': (43.2528, 5.9981, 3017), '83018': (43.2847, 6.0889, 3800),
    '83026': (43.4278, 6.2228, 1854), '83030': (43.3375, 6.5742, 4500),
    '83032': (43.4750, 6.1833, 3500), '83033': (43.3000, 6.1833, 3500),
    '83034': (43.3583, 6.5056, 1500), '83035': (43.2017, 5.7664, 4345),
    '83046': (43.5292, 6.1514, 2461), '83057': (43.3667, 6.1833, 5000),
    '83058': (43.5500, 6.7500, 55000), '83065': (43.6500, 5.8333, 1200),
    '83066': (43.6742, 5.8472, 1653), '83078': (43.4889, 6.7333, 7000),
    '83096': (43.3333, 6.3500, 7000), '83097': (43.1333, 6.2167, 6000),
    '83101': (43.2167, 6.6083, 2100), '83102': (43.2167, 6.6083, 2100),
    '83103': (43.6667, 5.8667, 200), '83104': (43.6103, 5.7617, 4200),
    '83106': (43.4500, 5.8583, 16000), '83108': (43.3592, 6.0428, 2806),
    '83114': (43.3083, 6.6333, 14000), '83120': (43.6417, 6.2167, 3500),
    '83121': (43.4417, 6.2639, 9000), '83122': (43.2000, 5.6833, 3800),
    '83129': (43.1022, 5.8481, 36489), '83134': (43.5500, 6.3833, 1800),
    '83143': (43.7264, 5.8094, 4470), '83154': (43.1583, 6.4667, 1300),
    '84005': (44.1333, 5.1667, 200), '84008': (44.1514, 5.2833, 300),
    '84012': (44.1261, 5.1811, 3119), '84016': (44.0500, 4.8833, 5200),
    '84025': (43.8506, 5.1506, 1816), '84039': (44.0556, 5.1278, 1200),
    '84055': (43.9281, 5.1806, 7500), '84062': (43.8942, 5.1153, 1578),
    '84064': (43.8833, 5.0167, 2000), '84066': (43.8500, 5.2833, 298),
    '84068': (43.7622, 5.3583, 1090), '84073': (44.0556, 5.1278, 6000),
    '84086': (43.8333, 5.2833, 1200), '84094': (44.2572, 5.0922, 597),
    '84100': (43.7500, 5.1167, 300), '84119': (43.9408, 4.9353, 5029),
    '84139': (43.8833, 5.1667, 700), '84144': (43.8667, 5.5667, 300),
    # Batch 3 — 33 communes supplémentaires
    '04046': (44.0833, 6.5167, 200), '04094': (43.9667, 6.7500, 120),
    '04116': (43.8333, 5.9833, 300), '04216': (44.3333, 6.4167, 300),
    '04229': (44.4500, 6.6167, 400),
    '05029': (44.8833, 6.5167, 300), '05087': (44.9000, 6.6000, 200),
    '05093': (45.0167, 6.5333, 900), '05097': (44.3167, 5.7000, 600),
    '05118': (44.3833, 5.7167, 1500), '05151': (44.8667, 6.3833, 400),
    '06026': (43.6583, 6.9333, 2000), '06125': (44.0500, 6.9000, 200),
    '13002': (43.3356, 5.4878, 21000), '13030': (43.4306, 5.0444, 9000),
    '13039': (43.5300, 5.0400, 10000), '13064': (43.5833, 4.7333, 2500),
    '13071': (43.4100, 5.3100, 20000), '13089': (43.6333, 5.3500, 700),
    '13208': (43.2800, 5.3800, 870000),
    '83007': (43.5833, 6.7167, 2500), '83053': (43.1833, 5.8500, 2000),
    '83069': (43.2000, 5.9833, 12000), '83100': (43.2833, 6.1333, 3500),
    '83107': (43.3417, 6.0667, 3000), '83121': (43.5600, 6.2300, 4000),
    '83128': (43.1167, 5.8667, 18000),
    '84051': (43.8833, 5.1500, 7500), '84056': (43.8833, 5.0833, 4500),
    '84058': (43.8667, 5.3333, 700), '84077': (44.0500, 5.0167, 3000),
    '84091': (44.2500, 5.0833, 600), '84102': (43.7833, 5.2833, 1300),
    '84105': (43.7833, 5.0500, 5500), '84136': (44.1667, 4.8000, 1100),
    '84149': (44.1667, 4.9500, 1600),
    # Batch 4 — 18 communes (coords vérifiées API geo.api.gouv.fr)
    '04068': (43.8947, 5.7765, 838),   # Dauphin
    '04090': (44.0183, 6.6627, 196),   # Le Fugeret
    '04129': (43.8436, 5.6584, 54),    # Montjustin
    '04144': (43.8010, 6.3230, 347),   # La Palud-sur-Verdon
    '04174': (43.9600, 6.7282, 166),   # Saint-Benoît
    '04241': (43.8627, 5.7065, 192),   # Villemus
    '05037': (44.4838, 6.0527, 545),   # Châteauvieux
    '05057': (44.4500, 5.9992, 276),   # Fouillouse
    '05075': (44.5317, 5.9553, 500),   # Manteyer
    '05169': (44.3615, 5.5700, 50),    # Sorbiers
    '13013': (43.4231, 5.5846, 2009),  # Belcodène
    '13056': (43.3839, 5.0451, 48298), # Martigues
    '83038': (43.6259, 6.4420, 476),   # Châteaudouble
    '83043': (43.2446, 6.3454, 1870),  # Collobrières
    '83116': (43.4488, 5.8603, 17896), # Saint-Maximin-la-Sainte-Baume
    '84070': (44.0171, 5.1646, 1969),  # Malemort-du-Comtat
    '84072': (44.0528, 5.1333, 6285),  # Mazan
    '84135': (44.2096, 4.7983, 1699),  # Uchaux
    # Batch 5 — 9 communes
    '04150': (44.4546, 6.1321, 201),    # Piégut
    '04195': (44.416, 6.6163, 631),     # Saint-Pons
    '05124': (44.5945, 6.1473, 471),    # La Rochette
    '06114': (43.7455, 7.2875, 5896),   # Saint-André-de-la-Roche
    '06130': (43.6994, 6.8516, 3658),   # Saint-Vallier-de-Thiey
    '83028': (43.5687, 6.5735, 2124),   # Callas
    '83071': (43.1641, 6.2417, 10584),  # La Londe-les-Maures
    '83149': (43.5649, 6.2855, 1514),   # Villecroze
    '84104': (44.1927, 4.9962, 1436),   # Sablet
    # Batch 6 — 5 communes
    '84098': (44.2539, 5.0125, 626),     # Roaix
    '84001': (44.0055, 4.9585, 2960),    # Althen-des-Paluds
    '13078': (43.4066, 4.826, 8573),     # Port-Saint-Louis-du-Rhône
    '83140': (43.4108, 5.9281, 5207),    # Tourves
    '83011': (43.6344, 6.5439, 1433),    # Bargemon
    # Batch 7 — 4 communes
    '83051': (43.5085, 6.2324, 1118),    # Entrecasteaux
    '04202': (44.013, 6.7861, 131),      # Sausses
    '83031': (43.3695, 6.3703, 5140),    # Le Cannet-des-Maures
    '13093': (43.6926, 5.3891, 357),     # Saint-Estève-Janson
    '84057': (43.9467, 4.9178, 1700),     # Jonquerettes
}
for code, (lat, lng, pop) in HARDCODED.items():
    if code not in cache:
        cache[code] = {'lat': lat, 'lng': lng, 'population': pop}

with open('data/geocode_cache.json', 'w', encoding='utf-8') as f:
    json.dump(cache, f, ensure_ascii=False)

still_missing = all_codes_2023 - set(cache.keys())

print(f"  Cache final : {len(cache)} communes")
if still_missing:
    print(f"  ⚠️  Manquantes : {still_missing}")
else:
    print(f"  ✅ Couverture 100%")

print("\n=== Terminé. Lancer maintenant : python build_map_v2.py --year both ===")
