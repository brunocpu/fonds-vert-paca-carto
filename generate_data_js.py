"""Generate data.js from CSV + existing geocoded coords in old HTML.
Run: python generate_data_js.py
"""
import csv, json, re
from collections import defaultdict
from pathlib import Path

# === CONFIG ===
CSV_PATH = Path("data/fonds_vert_2024_source.csv")
OLD_HTML = Path("index.html")  # current index.html still has DEPTS_GEOJSON
OUTPUT = Path("data.js")

PACA_DEPTS = {'04', '05', '06', '13', '83', '84'}

# Corrections by (original_code, montant) -> corrected_code
MONTANT_CORRECTIONS = {
    ('75056', 4299851.00): '13054', ('54395', 1200000.00): '06085',
    ('13055', 2098064.06): '06083', ('13055', 1226000.00): '06088',
    ('13055', 1065000.00): '83137', ('13055', 946380.00): '04143',
    ('13055', 450000.00): '83098', ('13001', 250000.00): '04245',
    ('69123', 31000.00): '13077', ('13055', 315000.00): '04049',
    ('13055', 165000.00): '83098', ('13001', 225000.00): '84031',
    ('26220', 2500.00): '84138',
}

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
    return s.replace('\n',' ').replace('\r','').replace('\t',' ').strip() if s else ''

def norm(s):
    return s.replace('\u2019',"'").replace('\u2018',"'") if s else ''

# Step 1: extract coords from existing HTML DATA
print("Extracting coords from existing HTML...")
html = OLD_HTML.read_text(encoding='utf-8')
# Try to get DATA from script src or inline
m = re.search(r'const DATA\s*=\s*(\[.*?\]);', html, re.DOTALL)
if not m:
    # If data.js is separate, read from v3 json
    json_path = Path("data/paca_map_data_v3.json")
    if json_path.exists():
        with open(json_path) as f:
            existing = json.load(f)
    else:
        print("ERROR: no existing data found")
        exit(1)
else:
    existing = json.loads(m.group(1))

coords = {d['code']: d for d in existing}
print(f"  {len(coords)} communes with coords")

# Step 2: extract DEPTS_GEOJSON
m2 = re.search(r'const DEPTS_GEOJSON\s*=\s*(\{.*?\});', html, re.DOTALL)
geojson_str = m2.group(1) if m2 else '{}'

# Step 3: first pass - find dynamic corrections (Manosque, PAPI Maures)
print("Scanning CSV for dynamic corrections...")
with open(CSV_PATH, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row.get('nom_region') != "Provence-Alpes-Côte d'Azur":
            continue
        code = row.get('code_commune','').strip()
        nom = row.get('nom_du_projet','')
        try:
            mt = float((row.get('montant_engage','0') or '0').replace('\xa0','').replace(' ','').replace(',','.'))
        except: mt = 0
        if code == '13055' and ('MANOSQUE' in nom.upper() or 'ESCLANGON' in nom.upper()):
            MONTANT_CORRECTIONS[('13055', mt)] = '04112'
        if code == '13109' and 'PAPI' in nom.upper():
            MONTANT_CORRECTIONS[('13109', mt)] = '83086'

print(f"  {len(MONTANT_CORRECTIONS)} correction rules")

# Step 4: parse CSV with all corrections
print("Parsing CSV...")
communes = defaultdict(lambda: {'count':0,'montant':0,'demarches':defaultdict(float),'projets':[]})

with open(CSV_PATH, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row.get('nom_region') != "Provence-Alpes-Côte d'Azur":
            continue
        code = row.get('code_commune','').strip()
        try:
            mt = float((row.get('montant_engage','0') or '0').replace('\xa0','').replace(' ','').replace(',','.'))
        except: mt = 0
        key = (code, mt)
        if key in MONTANT_CORRECTIONS:
            code = MONTANT_CORRECTIONS[key]
        elif code[:2] not in PACA_DEPTS:
            continue
        dem = norm(row.get('demarche','') or '')
        ds = DEMARCHE_SHORT.get(dem, dem[:25] if dem else 'Autre')
        communes[code]['count'] += 1
        communes[code]['montant'] += mt
        communes[code]['demarches'][dem] += mt
        communes[code]['projets'].append({'nom':clean(row.get('nom_du_projet',''))[:80],'montant':mt,'demarche_short':ds})

# Step 5: build map data using existing coords
print("Building map data...")
map_data = []
for entry in existing:
    code = entry['code']
    if code in communes:
        c = communes[code]
        td = max(c['demarches'], key=c['demarches'].get)
        tds = DEMARCHE_SHORT.get(td, td[:25] if td else 'Autre')
        ps = sorted(c['projets'], key=lambda p: -p['montant'])
        map_data.append({
            'lat':entry['lat'],'lng':entry['lng'],'commune':entry['commune'],
            'code':code,'dept':entry['dept'],'code_dept':entry['code_dept'],
            'count':c['count'],'montant':c['montant'],
            'top_demarche':td,'demarche_short':tds,'projets':ps,
            'population':entry.get('population',0),
        })

map_data.sort(key=lambda x:-x['montant'])
total = sum(d['count'] for d in map_data)
montant = sum(d['montant'] for d in map_data)
print(f"  {len(map_data)} communes, {total} projets, {montant/1e6:.1f} M€")

# Step 6: write data.js
data_json = json.dumps(map_data, ensure_ascii=False)
with open(OUTPUT, 'w', encoding='utf-8') as f:
    f.write(f'const DATA = {data_json};\n')
    f.write(f'const DEPTS_GEOJSON = {geojson_str};\n')

print(f"Written: {OUTPUT} ({OUTPUT.stat().st_size/1024:.0f} KB)")
