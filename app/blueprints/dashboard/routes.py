from flask import redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.blueprints.dashboard import dashboard_bp
from app.utils.landing import landing_endpoint_for_user


@dashboard_bp.get("/")
@login_required
def home():
    # Allows users that normally get auto-redirected (e.g. solicitante_filial) to access the hub.
    if request.args.get("hub") == "1":
        return render_template("dashboard/home.html", user=current_user)

    endpoint, kwargs = landing_endpoint_for_user(current_user)
    if endpoint != "dashboard.home":
        return redirect(url_for(endpoint, **kwargs))
    return render_template("dashboard/home.html", user=current_user)
