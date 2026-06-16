from flask import Blueprint, jsonify, request
from app.models import (
    alerte_get_all_active,
    eleve_get_by_classe, eleve_get_by_id,
    matieres_get_by_classe,
    note_get_by_eleve_matiere, note_get_stats_by_classe_matiere,
    note_get_all_by_classe, alerte_count_by_eleve_classe,
    alerte_get_by_eleve
)

bp = Blueprint('routes_dashboard', __name__)


@bp.route('/api/dashboard/<int:classe_id>', methods=['GET'])
def dashboard_classe(classe_id):
    eleves = eleve_get_by_classe(classe_id)
    matieres = matieres_get_by_classe(classe_id)
    stats = note_get_stats_by_classe_matiere(classe_id)

    coef_map = {m['nom']: m['coefficient'] for m in matieres}

    # Batch fetch : 2 requêtes pour toute la classe au lieu de 2N
    all_notes_flat = note_get_all_by_classe(classe_id)
    alertes_count_map = alerte_count_by_eleve_classe(classe_id)

    notes_by_eleve = {}
    for n in all_notes_flat:
        notes_by_eleve.setdefault(n['eleve_id'], []).append(n)

    eleves_list = []
    alertes_count = sum(alertes_count_map.values())

    for eleve in eleves:
        eleve_notes = notes_by_eleve.get(eleve['id'], [])
        nb_alertes = alertes_count_map.get(eleve['id'], 0)

        if eleve_notes:
            notes_par_matiere = {}
            for n in eleve_notes:
                notes_par_matiere.setdefault(n['matiere_nom'], []).append(n['note'])
            total_pondere = sum(
                (sum(vals) / len(vals)) * coef_map.get(nom, 1)
                for nom, vals in notes_par_matiere.items()
            )
            total_coef = sum(coef_map.get(nom, 1) for nom in notes_par_matiere)
            moyenne = total_pondere / total_coef if total_coef else None
        else:
            moyenne = None

        if moyenne is None:
            niveau = 'aucune'
        elif moyenne >= 14:
            niveau = 'bon'
        elif moyenne >= 10:
            niveau = 'moyen'
        else:
            niveau = 'faible'

        eleves_list.append({
            'id': eleve['id'],
            'nom': eleve['nom'],
            'prenom': eleve['prenom'],
            'matricule': eleve['matricule'],
            'moyenne': round(moyenne, 2) if moyenne is not None else None,
            'niveau': niveau,
            'alertes': nb_alertes
        })

    return jsonify({
        'eleves_list': eleves_list,
        'alertes_count': alertes_count,
        'stats': stats,
        'matieres': [{'id': m['id'], 'nom': m['nom'], 'coefficient': m['coefficient']} for m in matieres]
    })


@bp.route('/api/dashboard/eleve/<int:eleve_id>', methods=['GET'])
def fiche_eleve(eleve_id):
    eleve = eleve_get_by_id(eleve_id)
    if not eleve:
        return jsonify({'error': 'Élève introuvable'}), 404

    notes = note_get_by_eleve_matiere(eleve_id)
    alertes = alerte_get_by_eleve(eleve_id)
    matieres = matieres_get_by_classe(eleve['classe_id'])

    # Grouper par matière pour les tendances
    courbes = {}
    tendances = []
    total_coef = 0
    total_pondere = 0

    for matiere in matieres:
        notes_matiere = [n for n in notes if n['matiere_nom'] == matiere['nom']]
        if not notes_matiere:
            continue

        notes_triees = sorted(notes_matiere, key=lambda n: n['date_note'])
        valeurs = [n['note'] for n in notes_triees]

        # Moyenne de la matière
        moyenne_matiere = sum(valeurs) / len(valeurs)
        total_pondere += moyenne_matiere * matiere['coefficient']
        total_coef += matiere['coefficient']

        # Tendance
        if len(valeurs) >= 3:
            moitie1 = sum(valeurs[:len(valeurs)//2]) / (len(valeurs)//2)
            moitie2 = sum(valeurs[len(valeurs)//2:]) / (len(valeurs) - len(valeurs)//2)
            diff = moitie2 - moitie1
            if diff > 1:
                trend = 'hausse'
            elif diff < -1:
                trend = 'baisse'
            else:
                trend = 'stable'
        else:
            trend = 'stable'

        tendances.append({
            'matiere': matiere['nom'],
            'coefficient': matiere['coefficient'],
            'moyenne': round(moyenne_matiere, 2),
            'trend': trend,
            'nb_notes': len(valeurs)
        })

        courbes[matiere['nom']] = [
            {'date': n['date_note'], 'note': n['note']} for n in notes_triees
        ]

    moyenne_generale = round(total_pondere / total_coef, 2) if total_coef > 0 else None

    return jsonify({
        'id': eleve['id'],
        'nom': eleve['nom'],
        'prenom': eleve['prenom'],
        'matricule': eleve['matricule'],
        'classe_nom': eleve['classe_nom'],
        'classe_niveau': eleve['classe_niveau'],
        'moyenne_generale': moyenne_generale,
        'notes': notes,
        'courbes': courbes,
        'tendances': tendances,
        'alertes': alertes
    })


@bp.route('/api/alertes', methods=['GET'])
def list_alertes():
    from app.models import annee_get_active
    annee = annee_get_active()
    annee_id = annee['id'] if annee else None
    alertes = alerte_get_all_active(annee_id)
    return jsonify({'alertes': alertes})


@bp.route('/api/alertes/<int:alerte_id>/resolve', methods=['PUT'])
def resolve_alerte(alerte_id):
    from app.models import alerte_resolve
    alerte_resolve(alerte_id)
    return jsonify({'success': True, 'message': 'Alerte résolue'})


@bp.route('/api/alertes/resolve-all', methods=['PUT'])
def resolve_all_alertes():
    from app.models import alerte_resolve_all_by_classe
    data = request.get_json() or {}
    classe_id = data.get('classe_id')
    if classe_id:
        alerte_resolve_all_by_classe(classe_id)
    return jsonify({'success': True})