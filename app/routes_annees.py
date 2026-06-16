from flask import Blueprint, jsonify, request
from app.models import annee_get_all, annee_get_active, annee_create, annee_activate

bp = Blueprint('routes_annees', __name__)


@bp.route('/api/annees', methods=['GET'])
def list_annees():
    annees = annee_get_all()
    return jsonify({'annees': annees})


@bp.route('/api/annees', methods=['POST'])
def create_annee():
    data = request.get_json()
    if not data or 'annee' not in data:
        return jsonify({'error': 'Le champ annee est requis'}), 400
    annee_id, error = annee_create(data['annee'])
    if error:
        return jsonify({'error': error}), 400
    return jsonify({'id': annee_id, 'annee': data['annee'], 'active': False}), 201


@bp.route('/api/annees/active', methods=['GET'])
def get_active():
    annee = annee_get_active()
    if not annee:
        return jsonify({'error': 'Aucune année active'}), 404
    return jsonify(annee)


@bp.route('/api/annees/<int:annee_id>/activate', methods=['PUT'])
def activate(annee_id):
    annee_activate(annee_id)
    return jsonify({'success': True, 'message': 'Année activée'})