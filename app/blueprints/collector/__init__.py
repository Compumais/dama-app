from flask import Blueprint


collector_bp = Blueprint("collector", __name__, url_prefix="/collector")


from app.blueprints.collector import routes  # noqa: E402,F401
