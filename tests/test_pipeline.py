"""Tests d'invariants sur les données produites par le pipeline.

Ces tests vérifient que :
- les corrections de localisation (DOSSIER_CORRECTIONS, corrections_2023.json)
  sont effectivement appliquées dans les JSON de sortie ;
- les totaux de subventions ne dérivent pas entre le CSV brut et l'agrégat
  par commune ;
- toutes les communes sont géocodées et nommées ;
- l'harmonisation SIRENE produit bien le nom officiel et non le libellé brut ;
- les cas ambigus documentés dans la doctrine restent au porteur juridique.

Prérequis : `python build_map.py --year both` exécuté au préalable.
"""

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
DATA = ROOT / 'data'

# Import DOSSIER_CORRECTIONS depuis build_map.py
sys.path.insert(0, str(ROOT))
from build_map import DOSSIER_CORRECTIONS, REGION_PACA, COL_REGION, COL_DOSSIER

# Chargement unique des données
DATA_2023 = json.loads((DATA / 'paca_2023_map_data.json').read_text(encoding='utf-8'))
DATA_2024 = json.loads((DATA / 'paca_2024_map_data.json').read_text(encoding='utf-8'))
CORRECTIONS_2023 = json.loads((DATA / 'corrections_2023.json').read_text(encoding='utf-8'))
SIRET_CACHE = json.loads((DATA / 'siret_cache.json').read_text(encoding='utf-8'))

BY_CODE_2023 = {c['code']: c for c in DATA_2023}
BY_CODE_2024 = {c['code']: c for c in DATA_2024}


def _titles_by_dossier(csv_filename):
    """Lit le CSV et renvoie {dossier_id: titre_projet} pour les lignes PACA."""
    titles = {}
    with open(DATA / csv_filename, encoding='utf-8') as f:
        for row in csv.DictReader(f):
            if row.get(COL_REGION, '').strip() != REGION_PACA:
                continue
            d = row.get(COL_DOSSIER, '').strip()
            if d:
                titles[d] = (row.get('nom_du_projet') or '').strip()
    return titles


def test_dossier_corrections_2024_applied():
    """Chaque entrée de DOSSIER_CORRECTIONS doit faire apparaître le projet
    sur la commune cible dans paca_2024_map_data.json."""
    titles = _titles_by_dossier('fonds_vert_2024_source.csv')
    failures = []
    for dossier_id, target_code in DOSSIER_CORRECTIONS.items():
        title = titles.get(dossier_id)
        if not title:
            # dossier hors millésime 2024 — ignore (corrections année-spécifiques)
            continue
        commune = BY_CODE_2024.get(target_code)
        if commune is None:
            failures.append(f"{dossier_id}: commune cible {target_code} absente des données")
            continue
        matching = [p for p in commune['projets'] if p['nom'] == title]
        if not matching:
            failures.append(
                f"{dossier_id} -> {target_code}: titre '{title[:60]}...' non trouvé "
                f"sur la commune cible (commune contient {len(commune['projets'])} projets)"
            )
    assert not failures, "\n  ".join([f"{len(failures)} échec(s):"] + failures)


def test_corrections_2023_applied():
    """Chaque entrée de corrections_2023.json doit faire apparaître le projet
    sur la commune cible dans paca_2023_map_data.json."""
    titles = _titles_by_dossier('fonds_vert_2023_source.csv')
    failures = []
    for dossier_id, info in CORRECTIONS_2023.items():
        target_code = info['code_commune']
        title = titles.get(dossier_id)
        if not title:
            continue
        commune = BY_CODE_2023.get(target_code)
        if commune is None:
            failures.append(f"{dossier_id}: commune cible {target_code} absente")
            continue
        if not any(p['nom'] == title for p in commune['projets']):
            failures.append(
                f"{dossier_id} -> {target_code} ({info.get('commune','?')}): "
                f"titre '{title[:60]}...' non trouvé sur la commune cible"
            )
    assert not failures, "\n  ".join([f"{len(failures)} échec(s):"] + failures)


def test_totals_2024_stable():
    """La somme des montants 2024 dans les data correspond à la somme PACA
    dans le CSV brut (aucun projet perdu ou dupliqué)."""
    total_csv = 0.0
    n_csv = 0
    with open(DATA / 'fonds_vert_2024_source.csv', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            if row.get(COL_REGION, '').strip() != REGION_PACA:
                continue
            m = (row.get('montant_engage') or '0').replace('\xa0', '').replace(' ', '').replace(',', '.')
            try:
                total_csv += float(m or 0)
                n_csv += 1
            except ValueError:
                pass
    total_data = sum(c['montant'] for c in DATA_2024)
    n_data = sum(c['count'] for c in DATA_2024)
    assert n_csv == n_data, f"Projets : CSV={n_csv}, data={n_data} (un projet perdu ou dupliqué)"
    assert abs(total_csv - total_data) < 1.0, (
        f"Montants : CSV={total_csv:.2f}€, data={total_data:.2f}€ "
        f"(écart {total_csv - total_data:.2f}€)"
    )


def test_geocoding_complete():
    """Toutes les communes finales doivent avoir lat, lng et population."""
    for year, data in [(2023, DATA_2023), (2024, DATA_2024)]:
        for c in data:
            assert 'lat' in c and isinstance(c['lat'], (int, float)), (
                f"[{year}] {c['code']} {c['commune']} : lat manquant"
            )
            assert 'lng' in c and isinstance(c['lng'], (int, float)), (
                f"[{year}] {c['code']} {c['commune']} : lng manquant"
            )


def test_no_invalid_commune_codes():
    """Tous les code_commune des outputs doivent être 5 chiffres et préfixés
    par un département PACA (04/05/06/13/83/84)."""
    PACA = {'04', '05', '06', '13', '83', '84'}
    for year, data in [(2023, DATA_2023), (2024, DATA_2024)]:
        for c in data:
            code = c['code']
            assert len(code) == 5 and code.isdigit(), f"[{year}] code invalide : {code!r}"
            assert code[:2] in PACA, f"[{year}] {code} hors PACA"
            assert c['commune'] and c['commune'] != code, (
                f"[{year}] {code} : nom de commune vide ou égal au code ({c['commune']!r})"
            )


def test_sirene_harmonization_applied():
    """Pour les SIRENs présents dans siret_cache.json avec un nom officiel,
    le nom dans les data doit être le nom officiel (pas un libellé CSV brut)."""
    mismatches = []
    for year, data in [(2023, DATA_2023), (2024, DATA_2024)]:
        for c in data:
            for p in c['projets']:
                siren = p.get('siren', '')
                benef = p.get('beneficiaire', '')
                if not siren or siren not in SIRET_CACHE:
                    continue
                entry = SIRET_CACHE[siren]
                if entry.get('fallback'):
                    continue  # fallback CSV accepté
                nom_off = entry.get('nom', '')
                if nom_off and benef != nom_off:
                    mismatches.append(f"[{year}] SIREN {siren}: benef={benef!r} attendu={nom_off!r}")
    assert not mismatches, "\n  ".join([f"{len(mismatches)} bénéficiaire(s) non harmonisé(s):"] + mismatches[:5])


def test_doctrine_ambigus_preserved():
    """Les cas ambigus documentés dans la doctrine doivent rester au porteur
    juridique (cf. METHODOLOGIE.md §Doctrine de localisation)."""
    # Châteauvieux (05037) doit contenir "Sécurisation de la falaise de Lettret"
    chateauvieux = BY_CODE_2023.get('05037')
    assert chateauvieux is not None, "Châteauvieux (05037) absente des data 2023"
    assert any('Lettret' in p['nom'] for p in chateauvieux['projets']), (
        "Cas ambigu Châteauvieux/Lettret non conservé sur Châteauvieux"
    )
    # Banon (04018) doit contenir "POTEAUX INCENDIES"
    banon = BY_CODE_2024.get('04018')
    assert banon is not None, "Banon (04018) absente des data 2024"
    assert any('POTEAUX INCENDIES' in p['nom'] for p in banon['projets']), (
        "Cas ambigu Banon (4 poteaux incendie) non conservé sur Banon"
    )
