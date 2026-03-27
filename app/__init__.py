import os

from flask import Flask, redirect, send_from_directory, url_for

from app.blueprints.admin import admin_bp
from app.blueprints.api import api_bp
from app.blueprints.auth import auth_bp
from app.blueprints.collector import collector_bp
from app.blueprints.dashboard import dashboard_bp
from app.blueprints.requests import requests_bp
from app.cli import seed_initial_command
from app.config import config_by_name
from app.extensions import csrf, db, login_manager, migrate, socketio
from app.models import User


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__)

    env_name = config_name or os.getenv("FLASK_ENV", "development")
    app.config.from_object(config_by_name.get(env_name, config_by_name["development"]))

    _init_extensions(app)
    _register_blueprints(app)
    _register_cli(app)
    _register_routes(app)

    return app


def _init_extensions(app: Flask) -> None:
    # Garante registro dos models no metadata para migrations/autogenerate.
    from app import models as _models  # noqa: F401

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    socketio.init_app(app)

    @login_manager.user_loader
    def load_user(user_id: str):
        if not user_id.isdigit():
            return None
        return User.query.get(int(user_id))


def _register_blueprints(app: Flask) -> None:
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(collector_bp)
    app.register_blueprint(requests_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)


def _register_routes(app: Flask) -> None:
    @app.get("/")
    def index():
        return redirect(url_for("dashboard.home"))

    # Service worker must be served from the app root to control the whole scope.
    @app.get("/sw.js")
    def service_worker():
        return send_from_directory(app.static_folder, "js/sw.js", mimetype="application/javascript")


def _register_cli(app: Flask) -> None:
    app.cli.add_command(seed_initial_command)
