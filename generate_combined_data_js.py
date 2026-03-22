"""
Génère data.js combiné avec DATA_2023, DATA_2024 et DEPTS_GEOJSON.
Lit depuis data/paca_2023_map_data.json, data/paca_2024_map_data.json et le DEPTS_GEOJSON existant.

Usage: python generate_combined_data_js.py
"""
import json, re
from pathlib import Path

# 1. Charger les deux datasets
with open('data/paca_2023_map_data.json', 'r', encoding='utf-8') as f:
    data_2023 = json.load(f)
with open('data/paca_2024_map_data.json', 'r', encoding='utf-8') as f:
    data_2024 = json.load(f)

# 2. Extraire DEPTS_GEOJSON du data.js existant
with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
match = re.search(r'const DEPTS_GEOJSON\s*=\s*(\{.*\});', content, re.DOTALL)
if not match:
    raise RuntimeError("DEPTS_GEOJSON non trouvé dans data.js")
depts_geojson_str = match.group(1)

# 3. Écrire le nouveau data.js
with open('data.js', 'w', encoding='utf-8') as f:
    f.write('const DATA_2024 = ')
    json.dump(data_2024, f, ensure_ascii=False)
    f.write(';\n')
    f.write('const DATA_2023 = ')
    json.dump(data_2023, f, ensure_ascii=False)
    f.write(';\n')
    # Compat: DATA pointe vers 2024 par défaut
    f.write('let DATA = DATA_2024;\n')
    f.write(f'const DEPTS_GEOJSON = {depts_geojson_str};\n')

size = Path('data.js').stat().st_size
print(f"data.js généré: {size/1024:.0f} KB")
print(f"  DATA_2024: {len(data_2024)} communes")
print(f"  DATA_2023: {len(data_2023)} communes")
print(f"  DEPTS_GEOJSON: présent")
print(f"  DATA = DATA_2024 (défaut)")
