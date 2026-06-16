import hmac
import os
from flask import Blueprint, request, session, jsonify

bp = Blueprint('routes_auth', __name__)

ADMIN_USER = os.environ.get('GESTNOTE_USER', 'admin')
ADMIN_PASS = os.environ.get('GESTNOTE_PASS', 'gestNote2024')


@bp.route('/api/auth/status', methods=['GET'])
def auth_status():
    return jsonify({'authenticated': session.get('authenticated', False)})


@bp.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username', '')
    password = data.get('password', '')
    user_ok = hmac.compare_digest(str(username), ADMIN_USER)
    pass_ok = hmac.compare_digest(str(password), ADMIN_PASS)
    if user_ok and pass_ok:
        session['authenticated'] = True
        session.permanent = True
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Identifiants incorrects'}), 401


@bp.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})
