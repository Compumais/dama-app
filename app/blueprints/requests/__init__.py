from flask import Blueprint


requests_bp = Blueprint("requests", __name__, url_prefix="/requests")


from app.blueprints.requests import routes  # noqa: E402,F401
