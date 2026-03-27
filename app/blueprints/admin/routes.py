from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.blueprints.admin import admin_bp

from app.blueprints.admin.forms import BranchForm, ProductForm, UserEditForm, UserForm
from app.blueprints.admin.services import (
    email_already_exists,
    email_already_exists_for_other,
    list_admin_overview,
)
from app.extensions import db
from app.models import Branch, Product, Role, User
from app.utils.permissions import role_required


@admin_bp.get("/")
@login_required
@role_required("administrador")
def index():
    return render_template("admin/index.html", overview=list_admin_overview())


@admin_bp.route("/branches", methods=["GET", "POST"])
@login_required
@role_required("administrador")
def branches():
    form = BranchForm()
    if form.validate_on_submit():
        branch_code = form.code.data.strip().upper()
        if Branch.query.filter_by(code=branch_code).first():
            flash("Ja existe filial com este codigo.", "warning")
            return redirect(url_for("admin.branches"))

        branch = Branch(
            name=form.name.data.strip(),
            code=branch_code,
            active=form.active.data,
        )
        db.session.add(branch)
        db.session.commit()
        flash("Filial criada com sucesso.", "success")
        return redirect(url_for("admin.branches"))

    branch_list = Branch.query.order_by(Branch.name.asc()).all()
    return render_template("admin/branches.html", form=form, branch_list=branch_list)


@admin_bp.route("/products", methods=["GET", "POST"])
@login_required
@role_required("administrador")
def products():
    form = ProductForm()
    if form.validate_on_submit():
        barcode = form.barcode.data.strip()
        if Product.query.filter_by(barcode=barcode).first():
            flash("Ja existe produto com este codigo de barras.", "warning")
            return redirect(url_for("admin.products"))

        product = Product(
            barcode=barcode,
            internal_code=(form.internal_code.data or "").strip() or None,
            description=form.description.data.strip(),
            unit=form.unit.data.strip().upper(),
            active=form.active.data,
        )
        db.session.add(product)
        db.session.commit()
        flash("Produto criado com sucesso.", "success")
        return redirect(url_for("admin.products"))

    product_list = Product.query.order_by(Product.description.asc()).all()
    return render_template("admin/products.html", form=form, product_list=product_list)


@admin_bp.route("/users", methods=["GET", "POST"])
@login_required
@role_required("administrador")
def users():
    form = UserForm()
    roles = Role.query.filter_by(active=True).order_by(Role.name.asc()).all()
    branches = Branch.query.filter_by(active=True).order_by(Branch.name.asc()).all()

    form.role_id.choices = [(role.id, role.name) for role in roles]
    form.branch_id.choices = [(0, "Sem filial")] + [
        (branch.id, branch.name) for branch in branches
    ]

    is_valid_submission = form.validate_on_submit()
    if is_valid_submission:
        email = form.email.data.strip().lower()
        if email_already_exists(email):
            flash("Ja existe usuario com este e-mail.", "warning")
            return redirect(url_for("admin.users"))

        user = User(
            full_name=form.full_name.data.strip(),
            email=email,
            role_id=form.role_id.data,
            branch_id=form.branch_id.data or None,
            active=form.active.data,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Usuario criado com sucesso.", "success")
        return redirect(url_for("admin.users"))
    elif form.is_submitted():
        field_messages = []
        for field_name, messages in form.errors.items():
            for message in messages:
                field_messages.append(f"{field_name}: {message}")
        if field_messages:
            flash("Nao foi possivel salvar o usuario. " + " | ".join(field_messages), "danger")
        else:
            flash("Nao foi possivel salvar o usuario. Verifique os dados informados.", "danger")

    edit_form = UserEditForm()
    edit_form.role_id.choices = [(role.id, role.name) for role in roles]
    edit_form.branch_id.choices = [(0, "Sem filial")] + [
        (branch.id, branch.name) for branch in branches
    ]

    user_list = User.query.order_by(User.full_name.asc()).all()
    return render_template(
        "admin/users.html",
        form=form,
        edit_form=edit_form,
        user_list=user_list,
    )


@admin_bp.route("/users/edit/<int:user_id>", methods=["GET", "POST"])
@login_required
@role_required("administrador")
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    roles = Role.query.filter_by(active=True).order_by(Role.name.asc()).all()
    branches = Branch.query.filter_by(active=True).order_by(Branch.name.asc()).all()

    form = UserEditForm()
    form.role_id.choices = [(role.id, role.name) for role in roles]
    form.branch_id.choices = [(0, "Sem filial")] + [
        (branch.id, branch.name) for branch in branches
    ]

    if request.method == "GET":
        return redirect(url_for("admin.users"))

    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        if email_already_exists_for_other(email, user.id):
            flash("Ja existe usuario com este e-mail.", "warning")
            return redirect(url_for("admin.users"))

        user.full_name = form.full_name.data.strip()
        user.email = email
        user.role_id = form.role_id.data
        user.branch_id = form.branch_id.data or None
        user.active = form.active.data
        new_password = (form.password.data or "").strip()
        if new_password:
            user.set_password(new_password)
        db.session.commit()
        flash("Usuario atualizado com sucesso.", "success")
        return redirect(url_for("admin.users"))

    if form.is_submitted():
        field_messages = []
        for field_name, messages in form.errors.items():
            for message in messages:
                field_messages.append(f"{field_name}: {message}")
        if field_messages:
            flash("Nao foi possivel atualizar o usuario. " + " | ".join(field_messages), "danger")
        else:
            flash("Nao foi possivel atualizar o usuario. Verifique os dados informados.", "danger")

    return redirect(url_for("admin.users"))

@admin_bp.route("/users/delete/<int:user_id>", methods=["GET", "POST"])
@login_required
@role_required("administrador")
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash("Usuario deletado com sucesso.", "success")
    return redirect(url_for("admin.users"))

@admin_bp.errorhandler(403)
def admin_forbidden(_error):
    flash("Voce nao possui permissao para acessar o modulo administrativo.", "danger")
    return redirect(url_for("dashboard.home"))
