"""
Récupère le nom officiel SIRENE pour chaque bénéficiaire Fonds Vert PACA.

Source : API publique recherche-entreprises.api.gouv.fr (data.gouv.fr, sans token).
Cache : data/siret_cache.json (clé = SIREN 9 chiffres).

Usage : python fetch_siret_names.py
"""
import csv, json, time, urllib.request
from pathlib import Path

PACA_REGION = "Provence-Alpes-Côte d'Azur"
CACHE_PATH = Path('data/siret_cache.json')
API = "https://recherche-entreprises.api.gouv.fr/search?q={}&page=1&per_page=1"

def collect_sirens():
    sirens = {}  # siren -> libellé observé (un parmi d'autres)
    # 2023
    with open('data/fonds_vert_2023_source.csv', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if r.get('nom_region','').strip() != PACA_REGION: continue
            s = (r.get('siren') or '').strip()
            b = (r.get('nom_beneficiaire_principal') or '').strip()
            if s and len(s) == 9 and s.isdigit():
                sirens.setdefault(s, b)
    # 2024
    with open('data/fonds_vert_2024_source.csv', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if r.get('nom_region','').strip() != PACA_REGION: continue
            siret = (r.get('siret_beneficiaire') or '').strip()
            b = (r.get('raison_sociale_beneficiaire') or '').strip()
            if siret and len(siret) >= 9 and siret[:9].isdigit():
                sirens.setdefault(siret[:9], b)
    return sirens

def fetch_one(siren):
    url = API.format(siren)
    req = urllib.request.Request(url, headers={'User-Agent': 'FondsVert-PACA/2.0'})
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        if data.get('results'):
            r = data['results'][0]
            return {
                'nom': r.get('nom_raison_sociale') or r.get('nom_complet') or '',
                'sigle': r.get('sigle'),
                'nature': r.get('nature_juridique'),
                'tranche_eff': r.get('tranche_effectif_salarie'),
            }
    except Exception as e:
        return {'_error': str(e)}
    return None

def main():
    cache = {}
    if CACHE_PATH.exists():
        cache = json.loads(CACHE_PATH.read_text(encoding='utf-8'))
        print(f"Cache existant : {len(cache)} entrées")

    sirens = collect_sirens()
    print(f"SIRENs uniques PACA : {len(sirens)}")

    todo = [s for s in sirens if s not in cache or cache[s].get('_error')]
    print(f"À fetcher : {len(todo)}\n")

    for i, s in enumerate(todo, 1):
        res = fetch_one(s)
        if res is None:
            cache[s] = {'nom': sirens[s], 'fallback': True}
            print(f"  [{i}/{len(todo)}] {s} -> ABSENT API, fallback CSV : {sirens[s]!r}")
        elif res.get('_error'):
            print(f"  [{i}/{len(todo)}] {s} -> ERROR : {res['_error']}")
            cache[s] = {'nom': sirens[s], 'fallback': True, '_error': res['_error']}
        else:
            cache[s] = res
            csv_name = sirens[s]
            if res['nom'] != csv_name:
                print(f"  [{i}/{len(todo)}] {s} : {csv_name!r} -> {res['nom']!r}")
        if i % 50 == 0:
            CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding='utf-8')
        time.sleep(0.15)

    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f"\nCache sauvegardé : {CACHE_PATH}")
    print(f"Total SIRENs résolus : {sum(1 for v in cache.values() if not v.get('fallback'))}/{len(cache)}")

if __name__ == '__main__':
    main()
