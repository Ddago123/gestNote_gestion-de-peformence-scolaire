import csv
import io
from flask import Blueprint, jsonify, request
from app.models import (
    annee_get_active,
    eleve_get_by_classe, eleve_get_by_id,
    eleve_create, eleve_delete, eleve_search,
    eleve_import_bulk, eleve_get_by_matricule,
    note_get_by_eleve_matiere, alerte_get_by_eleve
)

bp = Blueprint('routes_eleves', __name__)


@bp.route('/api/eleves/classe/<int:classe_id>', methods=['GET'])
def list_eleves(classe_id):
    eleves = eleve_get_by_classe(classe_id)
    return jsonify({'eleves': eleves})


@bp.route('/api/eleves/import', methods=['POST'])
def import_eleves():
    if 'file' not in request.files:
        return jsonify({'error': 'Aucun fichier fourni'}), 400

    file = request.files['file']
    classe_id = request.form.get('classe_id', type=int)
    if not classe_id:
        return jsonify({'error': 'classe_id requis'}), 400

    stream = io.StringIO(file.stream.read().decode('utf-8-sig'), newline=None)
    reader = csv.DictReader(stream)

    errors = []
    eleves_data = []
    for i, row in enumerate(reader, start=2):
        matricule = row.get('matricule', '').strip()
        nom = row.get('nom', '').strip()
        prenom = row.get('prenom', '').strip()
        date_naissance = row.get('date_naissance', '').strip()

        if not matricule:
            errors.append({'ligne': i, 'matricule': '', 'erreur': 'Matricule manquant'})
            continue
        if not nom:
            errors.append({'ligne': i, 'matricule': matricule, 'erreur': 'Nom manquant'})
            continue
        if not prenom:
            errors.append({'ligne': i, 'matricule': matricule, 'erreur': 'Prénom manquant'})
            continue
        if eleve_get_by_matricule(classe_id, matricule):
            errors.append({'ligne': i, 'matricule': matricule, 'erreur': 'Matricule déjà existant dans cette classe'})
            continue

        eleves_data.append((matricule, nom, prenom, date_naissance))

    if errors:
        return jsonify({'success': False, 'count': 0, 'errors': errors}), 400

    created, import_errors = eleve_import_bulk(classe_id, eleves_data)

    return jsonify({'success': True, 'count': created, 'errors': import_errors})


@bp.route('/api/eleves/<int:eleve_id>', methods=['GET'])
def get_eleve(eleve_id):
    eleve = eleve_get_by_id(eleve_id)
    if not eleve:
        return jsonify({'error': 'Élève introuvable'}), 404

    notes = note_get_by_eleve_matiere(eleve_id)
    alertes = alerte_get_by_eleve(eleve_id)

    # Grouper les notes par matière
    courbes = {}
    for n in notes:
        matiere = n['matiere_nom']
        if matiere not in courbes:
            courbes[matiere] = []
        courbes[matiere].append({'date': n['date_note'], 'note': n['note']})

    return jsonify({
        'id': eleve['id'],
        'nom': eleve['nom'],
        'prenom': eleve['prenom'],
        'matricule': eleve['matricule'],
        'date_naissance': eleve['date_naissance'],
        'classe_nom': eleve['classe_nom'],
        'classe_niveau': eleve['classe_niveau'],
        'notes': notes,
        'courbes': courbes,
        'alertes': alertes
    })


@bp.route('/api/eleves', methods=['POST'])
def create_eleve():
    data = request.get_json()
    if not data or 'classe_id' not in data or 'matricule' not in data or 'nom' not in data or 'prenom' not in data:
        return jsonify({'error': 'Champs requis : classe_id, matricule, nom, prenom'}), 400
    eleve_id, error = eleve_create(
        data['classe_id'], data['matricule'],
        data['nom'], data['prenom'],
        data.get('date_naissance', '')
    )
    if error:
        return jsonify({'error': error}), 400
    return jsonify({'id': eleve_id}), 201


@bp.route('/api/eleves/<int:eleve_id>', methods=['DELETE'])
def delete_eleve(eleve_id):
    eleve_delete(eleve_id)
    return jsonify({'success': True, 'message': 'Élève supprimé'})


@bp.route('/api/eleves/search', methods=['GET'])
def search_eleves():
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify({'error': 'Requête trop courte (min 2 caractères)'}), 400
    annee = annee_get_active()
    if not annee:
        return jsonify({'error': 'Aucune année active'}), 404
    eleves = eleve_search(annee['id'], query)
    return jsonify({'eleves': eleves})