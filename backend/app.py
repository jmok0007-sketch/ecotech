"""Flask application factory and entry point.

Run locally:  python app.py
Run in EB:    gunicorn app:app
"""
from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from db.connection import init_pool, close_pool
from routes.health_routes import health_bp
from routes.emissions_routes import emissions_bp
from routes.disposal_routes import disposal_bp
from routes.chat_routes import chat_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app, resources={r"/api/*": {"origins": Config.CORS_ORIGINS}})

    init_pool()

    # Healthcheck (used by EB load balancer)
    @app.route("/")
    def index():
        return jsonify({"service": "ecotech-backend", "status": "ok"})

    @app.route("/api/health")
    def healthcheck():
        return jsonify({"status": "ok"})

    # Feature blueprints
    app.register_blueprint(health_bp, url_prefix="/api/health")
    app.register_blueprint(emissions_bp, url_prefix="/api/emissions")
    app.register_blueprint(disposal_bp, url_prefix="/api/map")
    app.register_blueprint(chat_bp, url_prefix="/api/ai")

    @app.errorhandler(404)
    def not_found(_):
        return jsonify({"detail": "Not found"}), 404

    @app.errorhandler(500)
    def server_error(err):
        return jsonify({"detail": "Internal server error", "error": str(err)}), 500

    @app.teardown_appcontext
    def teardown(_):
        pass

    return app


app = create_app()


if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=Config.PORT, debug=Config.DEBUG)
    finally:
        close_pool()
