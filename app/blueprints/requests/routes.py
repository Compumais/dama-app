from flask import abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.orm import selectinload

from app.blueprints.requests import requests_bp
from app.blueprints.requests.forms import StockRequestForm, StockRequestStatusForm
from app.blueprints.requests.services import (
    change_stock_request_status,
    create_stock_request,
    list_stock_requests,
    list_stock_requests_for_consultation,
)
from app.extensions import csrf
from app.models import Branch, Product, StockRequest, StockRequestItem
from app.models.stock_request import StockRequestStatus
from app.utils.permissions import role_required


@requests_bp.get("/")
@login_required
@role_required("acougueiro")
def index():
    status = request.args.get("status", "").strip()
    # Default: show only new requests for the butcher flow.
    if not status:
        status = StockRequestStatus.PENDENTE.value

    request_list = list_stock_requests(status=status or None, branch_id=None)

    return render_template(
        "requests/index.html",
        request_list=request_list,
        selected_status=status,
    )


@requests_bp.route("/new", methods=["GET"])
@login_required
@role_required("administrador", "solicitante_filial")
def new():
    branches = Branch.query.filter_by(active=True).order_by(Branch.name.asc()).all()

    current_role_slug = (getattr(current_user.role, "slug", "") or "").strip().lower()
    default_branch_id = None
    can_choose_branch = True
    if current_role_slug == "solicitante_filial":
        can_choose_branch = False
        default_branch_id = current_user.branch_id
        branches = [b for b in branches if b.id == default_branch_id] if default_branch_id else []

    return render_template(
        "requests/new_mobile.html",
        branch_list=branches,
        default_branch_id=default_branch_id,
        can_choose_branch=can_choose_branch,
        current_role_slug=current_role_slug,
    )


@requests_bp.get("/mine")
@login_required
@role_required("solicitante_filial", "gestor_consulta", "administrador")
def mine():
    status = request.args.get("status", "").strip()
    if not status:
        status = StockRequestStatus.PENDENTE.value

    role_slug = (getattr(current_user.role, "slug", "") or "").strip().lower()
    request_list = list_stock_requests_for_consultation(
        role_slug=role_slug,
        user_id=current_user.id,
        status=status or None,
    )

    return render_template(
        "requests/mine.html",
        request_list=request_list,
        selected_status=status,
        role_slug=role_slug,
    )


@requests_bp.get("/mine/<int:request_id>")
@login_required
@role_required("solicitante_filial", "gestor_consulta", "administrador")
def mine_view(request_id: int):
    stock_request = (
        StockRequest.query.options(
            selectinload(StockRequest.branch),
            selectinload(StockRequest.requested_by),
            selectinload(StockRequest.items).selectinload(StockRequestItem.product),
        )
        .filter(StockRequest.id == request_id)
        .first_or_404()
    )
    role_slug = (getattr(current_user.role, "slug", "") or "").strip().lower()
    if role_slug == "solicitante_filial" and stock_request.requested_by_user_id != current_user.id:
        abort(403)

    return render_template("requests/view.html", stock_request=stock_request, read_only=True)


@requests_bp.route("/new-legacy", methods=["GET", "POST"])
@login_required
@role_required("administrador", "solicitante_filial")
def new_legacy():
    form = StockRequestForm()
    branches = Branch.query.filter_by(active=True).order_by(Branch.name.asc()).all()
    products = Product.query.filter_by(active=True).order_by(Product.description.asc()).all()

    form.branch_id.choices = [(branch.id, branch.name) for branch in branches]
    form.product_id.choices = [(product.id, product.description) for product in products]

    current_role_slug = (getattr(current_user.role, "slug", "") or "").strip().lower()
    if current_role_slug == "solicitante_filial" and current_user.branch_id:
        form.branch_id.data = current_user.branch_id

    if form.validate_on_submit():
        branch_id = form.branch_id.data
        if current_role_slug == "solicitante_filial":
            branch_id = current_user.branch_id if current_user.branch_id else 0

        payload = {
            "branch_id": branch_id,
            "notes": form.notes.data,
            "requested_by_user_id": current_user.id,
            "items": [
                {
                    "product_id": form.product_id.data,
                    "quantity": str(form.quantity.data),
                    "scanned_code": "",
                    "notes": form.item_notes.data,
                }
            ],
        }
        result = create_stock_request(payload)
        if result["success"]:
            flash(result["message"], "success")
            return redirect(url_for("requests.mine"))
        flash(result["message"], "danger")

    return render_template("requests/new.html", form=form, current_role_slug=current_role_slug)


@requests_bp.post("/")
@login_required
@role_required("administrador", "solicitante_filial")
@csrf.exempt
def create():
    data = request.get_json(silent=True) or {}
    data["requested_by_user_id"] = current_user.id
    result = create_stock_request(data)
    status_code = 201 if result["success"] else 400
    return jsonify(result), status_code


@requests_bp.post("/<int:request_id>/status")
@login_required
@role_required("acougueiro")
def update_status(request_id: int):
    stock_request = StockRequest.query.get_or_404(request_id)
    form = StockRequestStatusForm()
    form.status.choices = [(status.value, status.value) for status in StockRequestStatus]

    if form.validate_on_submit():
        success, message = change_stock_request_status(
            stock_request=stock_request,
            new_status_raw=form.status.data,
            changed_by_user_id=current_user.id,
            notes=form.notes.data,
        )
        flash(message, "success" if success else "danger")
    else:
        flash("Dados inválidos para atualização de status.", "danger")

    return redirect(
        url_for("requests.index", status=stock_request.status.value if stock_request else StockRequestStatus.PENDENTE.value)
    )


@requests_bp.get("/<int:request_id>")
@login_required
@role_required("acougueiro")
def view(request_id: int):
    stock_request = (
        StockRequest.query.options(
            selectinload(StockRequest.branch),
            selectinload(StockRequest.requested_by),
            selectinload(StockRequest.items).selectinload(StockRequestItem.product),
        )
        .filter(StockRequest.id == request_id)
        .first_or_404()
    )
    return render_template("requests/view.html", stock_request=stock_request)


@requests_bp.post("/<int:request_id>/ready")
@login_required
@role_required("acougueiro")
def mark_ready(request_id: int):
    stock_request = StockRequest.query.get_or_404(request_id)
    success, message = change_stock_request_status(
        stock_request=stock_request,
        new_status_raw=StockRequestStatus.PRONTO.value,
        changed_by_user_id=current_user.id,
        notes="Marcado como pronto",
    )
    flash(message, "success" if success else "danger")
    return redirect(url_for("requests.index", status=StockRequestStatus.PRONTO.value))
