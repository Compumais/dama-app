from __future__ import annotations


def landing_endpoint_for_user(user) -> tuple[str, dict]:
    """
    Decides where the user should land after login / when opening the app.
    Returns (endpoint, kwargs) to be used with url_for().
    """
    role_slug = (getattr(getattr(user, "role", None), "slug", "") or "").strip().lower()

    if role_slug == "acougueiro":
        return ("collector.index", {})

    if role_slug == "solicitante_filial":
        # Default to the mobile-first creation flow.
        return ("requests.new", {})

    if role_slug == "gestor_consulta":
        return ("requests.mine", {})

    # administrador or unknown roles: keep the dashboard as a hub.
    return ("dashboard.home", {})


def landing_options_for_user(user) -> list[dict]:
    role_slug = (getattr(getattr(user, "role", None), "slug", "") or "").strip().lower()

    if role_slug == "acougueiro":
        return [
            {"endpoint": "requests.index", "label": "Requisições"},
            {"endpoint": "collector.index", "label": "Coletor"},
        ]

    if role_slug == "administrador":
        return [
            {"endpoint": "dashboard.home", "label": "Dashboard", "kwargs": {"hub": "1"}},
            {"endpoint": "admin.index", "label": "Administração"},
            {"endpoint": "requests.mine", "label": "Requisições"},
            {"endpoint": "collector.index", "label": "Coletor"},
        ]

    if role_slug == "solicitante_filial":
        return [
            {"endpoint": "requests.new", "label": "Nova requisição"},
            {"endpoint": "requests.mine", "label": "Minhas requisições"},
        ]

    if role_slug == "gestor_consulta":
        return [
            {"endpoint": "requests.mine", "label": "Consultar requisições"},
            {"endpoint": "dashboard.home", "label": "Dashboard", "kwargs": {"hub": "1"}},
        ]

    endpoint, kwargs = landing_endpoint_for_user(user)
    return [{"endpoint": endpoint, "label": "Continuar", "kwargs": kwargs}]

