from sqlalchemy import func

from app.models import Branch, Product, User


def list_admin_overview() -> dict:
    return {
        "users": User.query.count(),
        "branches": Branch.query.count(),
        "products": Product.query.count(),
    }


def email_already_exists(email: str) -> bool:
    normalized_email = (email or "").strip().lower()
    return (
        User.query.filter(func.lower(User.email) == normalized_email).first() is not None
    )
