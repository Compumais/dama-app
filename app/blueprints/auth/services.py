from sqlalchemy import func

from app.models import User

def authenticate_user(email: str, password: str):
    normalized_email = (email or "").strip().lower()
    if not normalized_email or not password:
        return None

    user = User.query.filter(func.lower(User.email) == normalized_email).first()
    if not user or not user.active:
        return None

    if user.check_password(password):
        return user

    return None
