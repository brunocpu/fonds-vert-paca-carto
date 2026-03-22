"""Fix geocode_cache.json: re-encode to UTF-8 and fill missing names."""
import json, urllib.request, time
from pathlib import Path

cache_path = Path('data/geocode_cache.json')

# Read with latin-1 fallback (Windows cp1252 damage)
with open(cache_path, 'rb') as f:
    raw = f.read()
try:
    content = raw.decode('utf-8')
except UnicodeDecodeError:
    print("⚠ Cache encoding cassé (latin-1), conversion en UTF-8...")
    content = raw.decode('latin-1')

cache = json.loads(content)
print(f"Cache: {len(cache)} entrées")

# Find entries without 'nom'
no_nom = [k for k, v in cache.items() if 'nom' not in v]
print(f"Entrées sans nom: {len(no_nom)}")

# Enrich from API with retries
fixed = 0
failed = []
for code in no_nom:
    for attempt in range(3):
        try:
            url = f"https://geo.api.gouv.fr/communes?code={code}&fields=nom,centre,population&limit=1"
            req = urllib.request.Request(url, headers={'User-Agent': 'FondsVert-PACA/2.0'})
            resp = urllib.request.urlopen(req, timeout=10)
            results = json.loads(resp.read())
            if results and results[0].get('nom'):
                cache[code]['nom'] = results[0]['nom']
                fixed += 1
                break
        except Exception as e:
            if attempt == 2:
                failed.append((code, str(e)))
            time.sleep(1)
    time.sleep(0.1)

print(f"Enrichis: {fixed}")
if failed:
    print(f"Échecs ({len(failed)}): {failed}")

# Rewrite in proper UTF-8
with open(cache_path, 'w', encoding='utf-8') as f:
    json.dump(cache, f, ensure_ascii=False)
print(f"Cache réécrit en UTF-8: {cache_path}")

# Final check
still_no = [k for k, v in cache.items() if 'nom' not in v]
print(f"Restant sans nom: {len(still_no)}")
if still_no:
    print(f"  Codes: {still_no}")
