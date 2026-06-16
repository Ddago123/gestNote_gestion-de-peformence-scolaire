from flask import Flask, send_from_directory, session, jsonify, request
import os
from app.database import init_db


def create_app():
    app = Flask(__name__)
    app.config.from_mapping(DATABASE='app/scolaire.db')
    app.secret_key = os.environ.get('SECRET_KEY', 'gestNote-dev-2024-change-in-prod')

    with app.app_context():
        init_db()

    from app.routes_annees import bp as bp_annees
    from app.routes_classes import bp as bp_classes
    from app.routes_eleves import bp as bp_eleves
    from app.routes_notes import bp as bp_notes
    from app.routes_dashboard import bp as bp_dashboard
    from app.routes_auth import bp as bp_auth

    app.register_blueprint(bp_auth)
    app.register_blueprint(bp_annees)
    app.register_blueprint(bp_classes)
    app.register_blueprint(bp_eleves)
    app.register_blueprint(bp_notes)
    app.register_blueprint(bp_dashboard)

    @app.before_request
    def require_auth():
        path = request.path
        if path.startswith('/api/') and not path.startswith('/api/auth/'):
            if not session.get('authenticated'):
                return jsonify({'error': 'Non authentifié', 'code': 401}), 401

    # Route pour servir index.html à la racine
    @app.route('/')
    def index():
        return send_from_directory(os.path.join(app.root_path, 'templates'), 'index.html')

    return app