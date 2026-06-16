"""
Utilitaire pour générer des fichiers CSV de notes aléatoires.
Usage: python randomize_notes.py <fichier_eleves.csv> <matiere> <classe_id>
"""

import csv
import random
import sys
from datetime import datetime, timedelta


def generer_notes(fichier_eleves, matiere, nb_series=3):
    with open(fichier_eleves, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        eleves = list(reader)

    dates = []
    for i in range(nb_series):
        d = datetime.now() - timedelta(days=(nb_series - i) * 30)
        dates.append(d.strftime('%Y-%m-%d'))

    output_name = f"notes_{matiere.replace(' ', '_').lower()}.csv"
    with open(output_name, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['matricule', 'nom_eleve', 'note', 'date'])
        for eleve in eleves:
            niveau = random.choice(['faible', 'moyen', 'bon'])
            base = {'faible': 7, 'moyen': 11, 'bon': 15}[niveau]

            nom = eleve.get('nom') or eleve.get('nom_eleve') or ''
            prenom = eleve.get('prenom') or eleve.get('prenom_eleve') or ''
            # Certains CSV de notes (ou autres) peuvent ne fournir que nom_eleve
            # auquel cas on mettra nom_eleve tel quel dans nom.
            if not prenom and 'nom_eleve' in eleve and 'prenom' not in eleve:
                prenom = ''

            nom_complet = (f"{nom} {prenom}".strip()).strip()

            for date in dates:
                note = max(0, min(20, round(base + random.uniform(-3, 3), 1)))
                writer.writerow([eleve['matricule'], nom_complet, note, date])


    print(f"✅ {len(eleves)} élèves x {nb_series} séries = {len(eleves) * nb_series} notes générées")
    print(f"📄 Fichier: {output_name}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python randomize_notes.py <fichier_eleves.csv> [matiere] [nb_series]")
        sys.exit(1)

    fichier = sys.argv[1]
    matiere = sys.argv[2] if len(sys.argv) > 2 else 'matiere'
    nb_series = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    generer_notes(fichier, matiere, nb_series)



