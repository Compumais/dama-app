from flask import flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.blueprints.collector import collector_bp
from app.blueprints.collector.forms import ScanForm
from app.blueprints.collector.services import (
    add_scan_item,
    clear_open_collection,
    finalize_open_collection,
    get_open_collection_with_items,
    preview_scan_item,
    remove_item,
    update_item_quantity,
)
from app.extensions import csrf
from app.utils.permissions import role_required


@collector_bp.get("/")
@login_required
@role_required("administrador", "acougueiro")
def index():
    form = ScanForm()
    collection = get_open_collection_with_items(current_user.id)
    return render_template("collector/index.html", form=form, collection=collection)


@collector_bp.post("/scan")
@login_required
@role_required("administrador", "acougueiro")
@csrf.exempt
def scan_item():
    if request.is_json:
        barcode = request.json.get("barcode", "")
        quantity = request.json.get("quantity")
    else:
        barcode = request.form.get("barcode", "")
        quantity = request.form.get("quantity", "1")

    payload = add_scan_item(
        user_id=current_user.id,
        branch_id=current_user.branch_id,
        barcode=barcode,
        quantity=quantity,
    )

    if request.is_json:
        return jsonify(payload), (200 if payload["success"] else 400)

    flash(payload["message"], "success" if payload["success"] else "danger")
    return redirect(url_for("collector.index"))


@collector_bp.post("/scan/preview")
@login_required
@role_required("administrador", "acougueiro")
@csrf.exempt
def scan_preview():
    data = request.get_json(silent=True) or {}
    barcode = data.get("barcode", "")
    quantity = data.get("quantity")
    payload = preview_scan_item(
        user_id=current_user.id,
        branch_id=current_user.branch_id,
        barcode=barcode,
        quantity=quantity,
    )
    return jsonify(payload), (200 if payload["success"] else 400)


@collector_bp.post("/items/<int:item_id>/quantity")
@login_required
@role_required("administrador", "acougueiro")
def change_item_quantity(item_id: int):
    quantity = request.form.get("quantity", "")
    success, message = update_item_quantity(
        user_id=current_user.id,
        item_id=item_id,
        quantity=quantity,
    )
    flash(message, "success" if success else "danger")
    return redirect(url_for("collector.index"))


@collector_bp.post("/items/<int:item_id>/remove")
@login_required
@role_required("administrador", "acougueiro")
def delete_item(item_id: int):
    success, message = remove_item(current_user.id, item_id)
    flash(message, "success" if success else "danger")
    return redirect(url_for("collector.index"))


@collector_bp.post("/clear")
@login_required
@role_required("administrador", "acougueiro")
def clear_collection():
    success, message = clear_open_collection(current_user.id)
    flash(message, "success" if success else "warning")
    return redirect(url_for("collector.index"))


@collector_bp.post("/finalize")
@login_required
@role_required("administrador", "acougueiro")
def finalize_collection():
    success, message = finalize_open_collection(current_user.id)
    flash(message, "success" if success else "warning")
    return redirect(url_for("collector.index"))
