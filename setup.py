"""
Setup script - télécharge le CSV et construit la carte.
Exécuter une seule fois : python setup.py
"""
import subprocess
import sys

print("=== Setup Cartographie Fonds Vert PACA 2024 ===")
print()
print("Étape 1: Téléchargement du CSV source...")
subprocess.run([sys.executable, "build_map.py"], check=True)
print()
print("Terminé ! Ouvrir fonds-vert-paca-carte.html dans Chrome.")
