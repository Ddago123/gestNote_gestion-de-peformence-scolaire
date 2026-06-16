from flask import Blueprint, jsonify, request
from app.models import (
    annee_get_active,
    classe_get_by_annee, classe_get_by_id,
    classe_create, classe_delete,
    matieres_get_by_classe, coefficient_upsert
)

bp = Blueprint('routes_classes', __name__)


@bp.route('/api/classes', methods=['GET'])
def list_classes():
    annee = annee_get_active()
    if not annee:
        return jsonify({'error': 'Aucune année active'}), 404
    classes = classe_get_by_annee(annee['id'])
    return jsonify({'classes': classes})


@bp.route('/api/classes', methods=['POST'])
def create_classe():
    annee = annee_get_active()
    if not annee:
        return jsonify({'error': 'Aucune année active'}), 400
    data = request.get_json()
    if not data or 'nom' not in data or 'niveau' not in data:
        return jsonify({'error': 'Les champs nom et niveau sont requis'}), 400
    classe_id, error = classe_create(annee['id'], data['nom'], data['niveau'])
    if error:
        return jsonify({'error': error}), 400
    return jsonify({'id': classe_id, 'nom': data['nom'], 'niveau': data['niveau']}), 201


@bp.route('/api/classes/<int:classe_id>', methods=['GET'])
def get_classe(classe_id):
    classe = classe_get_by_id(classe_id)
    if not classe:
        return jsonify({'error': 'Classe introuvable'}), 404
    matieres = matieres_get_by_classe(classe_id)
    classe['matieres'] = matieres
    return jsonify(classe)


@bp.route('/api/classes/<int:classe_id>', methods=['DELETE'])
def delete_classe(classe_id):
    classe_delete(classe_id)
    return jsonify({'success': True, 'message': 'Classe supprimée'})


@bp.route('/api/coefficients/<int:classe_id>', methods=['GET'])
def get_coefficients(classe_id):
    matieres = matieres_get_by_classe(classe_id)
    return jsonify({'coefficients': [{'matiere': m['nom'], 'coefficient': m['coefficient']} for m in matieres]})


@bp.route('/api/coefficients', methods=['POST'])
def set_coefficient():
    data = request.get_json()
    if not data or 'classe_id' not in data or 'matiere' not in data or 'coefficient' not in data:
        return jsonify({'error': 'Champs requis : classe_id, matiere, coefficient'}), 400
    success, error = coefficient_upsert(data['classe_id'], data['matiere'], data['coefficient'])
    if not success:
        return jsonify({'error': error}), 400
    return jsonify({'success': True, 'message': 'Coefficient mis à jour'})