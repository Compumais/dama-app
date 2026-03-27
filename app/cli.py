import os

import click
from flask.cli import with_appcontext

from app.extensions import db
from app.models import Branch, Role, User


@click.command("seed-initial")
@with_appcontext
def seed_initial_command():
    role_map = {
        "administrador": "Administrador",
        "solicitante_filial": "Solicitante de filial",
        "acougueiro": "Açougueiro",
        "gestor_consulta": "Gestor/Consulta",
    }

    for slug, name in role_map.items():
        role = Role.query.filter_by(slug=slug).first()
        if not role:
            db.session.add(Role(name=name, slug=slug, active=True))

    default_branch = Branch.query.filter_by(code="MATRIZ").first()
    if not default_branch:
        default_branch = Branch(name="Matriz", code="MATRIZ", active=True)
        db.session.add(default_branch)

    db.session.flush()

    admin_role = Role.query.filter_by(slug="administrador").first()
    admin_email = os.getenv("ADMIN_EMAIL", "admin@local.dev").strip().lower()
    admin_user = User.query.filter_by(email=admin_email).first()

    if not admin_user:
        admin_user = User(
            full_name=os.getenv("ADMIN_NAME", "Administrador"),
            email=admin_email,
            role_id=admin_role.id,
            branch_id=default_branch.id,
            active=True,
        )
        admin_user.set_password(os.getenv("ADMIN_PASSWORD", "admin123"))
        db.session.add(admin_user)

    db.session.commit()
    click.echo("Seed inicial concluido com sucesso.")
