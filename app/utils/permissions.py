from functools import wraps

from flask import abort
from flask_login import current_user


def role_required(*allowed_slugs: str):
    normalized = {slug.strip().lower() for slug in allowed_slugs if slug}

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            role_slug = (
                getattr(getattr(current_user, "role", None), "slug", "") or ""
            ).strip().lower()
            if normalized and role_slug not in normalized:
                return abort(403)
            return view_func(*args, **kwargs)

        return wrapper

    return decorator
