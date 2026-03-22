"""Patch the 11 remaining entries without 'nom' in geocode_cache.json."""
import json
from pathlib import Path

HARDCODED = {
    '13117': 'Vitrolles',
    '83092': 'Pignans',
    '04206': 'Sigonce',
    '83145': 'Varages',
    '84024': "Cabrières-d'Aigues",
    '13051': 'Lançon-Provence',
    '04242': 'Villeneuve',
    '04178': 'Saint-Pierre',
    '05118': 'Réallon',
    '13201': 'Marseille',
    '13208': 'Marseille',
}

cache_path = Path('data/geocode_cache.json')
with open(cache_path, 'r', encoding='utf-8') as f:
    cache = json.load(f)

patched = 0
for code, nom in HARDCODED.items():
    if code in cache:
        cache[code]['nom'] = nom
        patched += 1
        print(f"  {code} → {nom}")
    else:
        print(f"  ⚠ {code} absent du cache")

with open(cache_path, 'w', encoding='utf-8') as f:
    json.dump(cache, f, ensure_ascii=False)

no_nom = [k for k, v in cache.items() if 'nom' not in v]
print(f"\nPatché: {patched}")
print(f"Restant sans nom: {len(no_nom)}")
if no_nom:
    print(f"  {no_nom}")
