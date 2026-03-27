from datetime import datetime, timezone

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.blueprints.auth import auth_bp
from app.blueprints.auth.forms import LoginForm
from app.blueprints.auth.services import authenticate_user
from app.extensions import db
from app.utils.landing import landing_endpoint_for_user, landing_options_for_user


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        endpoint, kwargs = landing_endpoint_for_user(current_user)
        return redirect(url_for(endpoint, **kwargs))

    form = LoginForm()
    next_url = request.args.get("next") or request.form.get("next")
    if form.validate_on_submit():
        user = authenticate_user(form.email.data, form.password.data)
        if user:
            login_user(user, remember=form.remember_me.data)
            user.last_login_at = datetime.now(timezone.utc)
            db.session.commit()
            flash("Login realizado com sucesso.", "success")
            options = landing_options_for_user(user)
            if len(options) > 1:
                return render_template("auth/choose_destination.html", options=options)
            if next_url and next_url.startswith("/"):
                return redirect(next_url)
            endpoint, kwargs = landing_endpoint_for_user(user)
            return redirect(url_for(endpoint, **kwargs))

        flash("Credenciais invalidas.", "danger")

    return render_template("auth/login.html", form=form, next_url=next_url)


@auth_bp.get("/logout")
@login_required
def logout():
    logout_user()
    flash("Voce saiu da sessao.", "info")
    return redirect(url_for("auth.login"))
