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


def email_already_exists_for_other(email: str, exclude_user_id: int) -> bool:
    normalized_email = (email or "").strip().lower()
    return (
        User.query.filter(
            func.lower(User.email) == normalized_email,
            User.id != exclude_user_id,
        ).first()
        is not None
    )
