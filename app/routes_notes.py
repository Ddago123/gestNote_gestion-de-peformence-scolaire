import csv
import io
from datetime import datetime
from flask import Blueprint, jsonify, request
from app.models import (
    eleve_get_by_classe, eleve_get_by_matricule,
    matieres_get_by_classe,
    note_create, note_update, note_delete, note_import_bulk,
    note_get_existing_keys,
    alerte_create
)

bp = Blueprint('routes_notes', __name__)

SEUILS_ALERTES = {
    'baisse_performance': {'seuil_moyenne': 2, 'seuil_consecutif': 10, 'nb_consecutif': 2, 'severite': 3},
    'excellence': {'seuil': 17, 'nb_notes': 5, 'severite': 1},
    'difficulte': {'seuil': 8, 'nb_consecutif': 3, 'severite': 5},
    'progression': {'hausse': 2, 'nb_notes': 5, 'severite': 2},
}


def generer_alertes_pour_eleve(eleve_id, matiere_id, eleve_notes):
    """Analyse les notes d'un élève pour une matière et génère les alertes."""
    alertes_generees = []

    if len(eleve_notes) < 2:
        return alertes_generees

    notes_triees = sorted(eleve_notes, key=lambda n: n['date_note'])
    notes_vals = [n['note'] for n in notes_triees]

    # 1. Vérifier baisse de performance
    if len(notes_vals) >= 5:
        dernieres_5 = notes_vals[-5:]
        precedentes = notes_vals[:-5]
        if precedentes:
            moyenne_recents = sum(dernieres_5) / 5
            moyenne_anciens = sum(precedentes) / len(precedentes)
            if moyenne_anciens - moyenne_recents >= SEUILS_ALERTES['baisse_performance']['seuil_moyenne']:
                a_id = alerte_create(
                    eleve_id, 'baisse_performance', SEUILS_ALERTES['baisse_performance']['severite'],
                    f'Baisse de performance détectée (moyenne récente: {moyenne_recents:.1f}/20)',
                    matiere_id
                )
                if a_id:
                    alertes_generees.append(a_id)

    # 2. Vérifier deux notes consécutives < 10
    consecutif_bas = 1 if notes_vals[-1] < 10 else 0
    for n in reversed(notes_vals[:-1]):
        if n < 10:
            consecutif_bas += 1
        else:
            break
    if consecutif_bas >= SEUILS_ALERTES['baisse_performance']['nb_consecutif']:
        a_id = alerte_create(
            eleve_id, 'notes_basses_consecutives', 3,
            f'{consecutif_bas} notes consécutives en dessous de 10/20',
            matiere_id
        )
        if a_id:
            alertes_generees.append(a_id)

    # 3. Vérifier excellence
    if len(notes_vals) >= SEUILS_ALERTES['excellence']['nb_notes']:
        dernieres = notes_vals[-SEUILS_ALERTES['excellence']['nb_notes']:]
        if sum(dernieres) / len(dernieres) >= SEUILS_ALERTES['excellence']['seuil']:
            a_id = alerte_create(
                eleve_id, 'excellence', SEUILS_ALERTES['excellence']['severite'],
                f'Excellence maintenue (moyenne: {sum(dernieres)/len(dernieres):.1f}/20)',
                matiere_id
            )
            if a_id:
                alertes_generees.append(a_id)

    # 4. Vérifier difficulté persistante
    consecutif_tres_bas = 1 if notes_vals[-1] < 8 else 0
    for n in reversed(notes_vals[:-1]):
        if n < 8:
            consecutif_tres_bas += 1
        else:
            break
    if consecutif_tres_bas >= SEUILS_ALERTES['difficulte']['nb_consecutif']:
        a_id = alerte_create(
            eleve_id, 'difficulte_persistante', SEUILS_ALERTES['difficulte']['severite'],
            f'Difficulté persistante : {consecutif_tres_bas} notes consécutives < 8/20',
            matiere_id
        )
        if a_id:
            alertes_generees.append(a_id)

    # 5. Vérifier progression
    if len(notes_vals) >= SEUILS_ALERTES['progression']['nb_notes']:
        dernieres = notes_vals[-SEUILS_ALERTES['progression']['nb_notes']:]
        moitie1 = dernieres[:len(dernieres)//2]
        moitie2 = dernieres[len(dernieres)//2:]
        if moitie1 and moitie2:
            moy1 = sum(moitie1) / len(moitie1)
            moy2 = sum(moitie2) / len(moitie2)
            if moy2 - moy1 >= SEUILS_ALERTES['progression']['hausse']:
                a_id = alerte_create(
                    eleve_id, 'progression', SEUILS_ALERTES['progression']['severite'],
                    f'Progression encourageante (+{moy2 - moy1:.1f} points)',
                    matiere_id
                )
                if a_id:
                    alertes_generees.append(a_id)

    return alertes_generees


@bp.route('/api/notes/import/preview', methods=['POST'])
def preview_import():
    if 'file' not in request.files:
        return jsonify({'error': 'Aucun fichier fourni'}), 400

    file = request.files['file']
    classe_id = request.form.get('classe_id', type=int)
    matiere_id = request.form.get('matiere_id', type=int)
    if not classe_id or not matiere_id:
        return jsonify({'error': 'classe_id et matiere_id requis'}), 400

    eleves = {e['matricule']: e for e in eleve_get_by_classe(classe_id)}
    matieres = matieres_get_by_classe(classe_id)
    matiere = next((m for m in matieres if m['id'] == matiere_id), None)
    if not matiere:
        return jsonify({'error': 'Matière introuvable'}), 404

    existing_keys = note_get_existing_keys(matiere_id)

    stream = io.StringIO(file.stream.read().decode('utf-8-sig'), newline=None)
    reader = csv.DictReader(stream)

    preview = []
    warnings = []
    errors = []
    for i, row in enumerate(reader, start=2):
        matricule = row.get('matricule', '').strip()
        nom_eleve = row.get('nom_eleve', '').strip()
        note_str = row.get('note', '').strip()
        date_note = row.get('date', '').strip()

        if not matricule:
            errors.append({'ligne': i, 'erreur': 'Matricule manquant'})
            continue

        eleve = eleves.get(matricule)
        if not eleve:
            errors.append({'ligne': i, 'matricule': matricule, 'erreur': 'Matricule inconnu dans cette classe'})
            continue

        try:
            note_val = float(note_str.replace(',', '.'))
        except (ValueError, AttributeError):
            errors.append({'ligne': i, 'matricule': matricule, 'erreur': 'Note non numérique'})
            continue

        if note_val < 0 or note_val > 20:
            errors.append({'ligne': i, 'matricule': matricule, 'erreur': 'Note hors limite (0-20)'})
            continue

        effective_date = date_note if date_note else datetime.now().strftime('%Y-%m-%d')
        if (eleve['id'], effective_date) in existing_keys:
            warnings.append({'ligne': i, 'matricule': matricule, 'message': 'Note déjà saisie pour cette date (doublon)', 'note': note_val})

        if note_val >= 18:
            warnings.append({'ligne': i, 'matricule': matricule, 'message': 'Note très élevée', 'note': note_val})

        if note_val < 4:
            warnings.append({'ligne': i, 'matricule': matricule, 'message': 'Note très basse (élève absent ?)', 'note': note_val})

        preview.append({
            'matricule': matricule,
            'nom_eleve': f"{eleve['nom']} {eleve['prenom']}",
            'note': note_val,
            'date': date_note
        })

    return jsonify({
        'preview': preview,
        'matiere': matiere['nom'],
        'warnings': warnings,
        'errors': errors
    })


@bp.route('/api/notes/import', methods=['POST'])
def import_notes():
    if 'file' not in request.files:
        return jsonify({'error': 'Aucun fichier fourni'}), 400

    file = request.files['file']
    classe_id = request.form.get('classe_id', type=int)
    matiere_id = request.form.get('matiere_id', type=int)
    if not classe_id or not matiere_id:
        return jsonify({'error': 'classe_id et matiere_id requis'}), 400

    eleves = {e['matricule']: e for e in eleve_get_by_classe(classe_id)}
    existing_keys = note_get_existing_keys(matiere_id)

    stream = io.StringIO(file.stream.read().decode('utf-8-sig'), newline=None)
    reader = csv.DictReader(stream)

    notes_data = []
    errors = []
    skipped = 0
    for i, row in enumerate(reader, start=2):
        matricule = row.get('matricule', '').strip()
        note_str = row.get('note', '').strip()
        date_note = row.get('date', '').strip()

        if not matricule:
            errors.append({'ligne': i, 'erreur': 'Matricule manquant'})
            continue

        eleve = eleves.get(matricule)
        if not eleve:
            errors.append({'ligne': i, 'matricule': matricule, 'erreur': 'Matricule inconnu'})
            continue

        try:
            note_val = float(note_str.replace(',', '.'))
        except (ValueError, AttributeError):
            errors.append({'ligne': i, 'matricule': matricule, 'erreur': 'Note non numérique'})
            continue

        if note_val < 0 or note_val > 20:
            errors.append({'ligne': i, 'matricule': matricule, 'erreur': 'Note hors limite'})
            continue

        if not date_note:
            date_note = datetime.now().strftime('%Y-%m-%d')

        if (eleve['id'], date_note) in existing_keys:
            skipped += 1
            continue

        notes_data.append((eleve['id'], matiere_id, note_val, date_note))

    if errors:
        return jsonify({'success': False, 'count': 0, 'errors': errors}), 400

    count = note_import_bulk(notes_data)

    # Générer les alertes pour les notes importées
    alertes = []
    for eleve_id, _, note_val, date_note in notes_data:
        from app.models import note_get_by_eleve_matiere
        eleve_notes = note_get_by_eleve_matiere(eleve_id, matiere_id)
        alertes.extend(generer_alertes_pour_eleve(eleve_id, matiere_id, eleve_notes))

    return jsonify({'success': True, 'count': count, 'skipped': skipped, 'alertes': len(alertes)})


@bp.route('/api/notes/manuel', methods=['POST'])
def add_note_manuel():
    data = request.get_json()
    if not data or 'eleve_id' not in data or 'matiere_id' not in data or 'note' not in data:
        return jsonify({'error': 'Champs requis : eleve_id, matiere_id, note'}), 400

    note_val = data['note']
    if note_val < 0 or note_val > 20:
        return jsonify({'error': 'Note hors limite (0-20)'}), 400

    date_note = data.get('date', datetime.now().strftime('%Y-%m-%d'))
    note_id = note_create(data['eleve_id'], data['matiere_id'], note_val, date_note, 'manuel')

    # Générer alertes
    from app.models import note_get_by_eleve_matiere
    eleve_notes = note_get_by_eleve_matiere(data['eleve_id'], data['matiere_id'])
    alertes = generer_alertes_pour_eleve(data['eleve_id'], data['matiere_id'], eleve_notes)

    return jsonify({'id': note_id, 'success': True, 'alertes': len(alertes)}), 201


@bp.route('/api/notes/<int:note_id>', methods=['PUT'])
def edit_note(note_id):
    data = request.get_json()
    if not data or 'note' not in data:
        return jsonify({'error': 'Champ note requis'}), 400
    note_val = data['note']
    if note_val < 0 or note_val > 20:
        return jsonify({'error': 'Note hors limite (0-20)'}), 400
    date_note = data.get('date', datetime.now().strftime('%Y-%m-%d'))
    note_update(note_id, note_val, date_note)
    return jsonify({'success': True, 'message': 'Note modifiée'})


@bp.route('/api/notes/<int:note_id>', methods=['DELETE'])
def remove_note(note_id):
    note_delete(note_id)
    return jsonify({'success': True, 'message': 'Note supprimée'})