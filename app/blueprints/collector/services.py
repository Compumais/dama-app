from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models import Collection, CollectionItem, Product, User
from app.models.collection import CollectionStatus
from app.services.barcode_service import parse_barcode

PROJECT_ROOT = Path(__file__).resolve().parents[3]
FINALIZED_DIR = PROJECT_ROOT / "finalizadas"


def get_or_create_open_collection(user_id: int, branch_id: int | None) -> Collection:
    collection = (
        Collection.query.filter_by(user_id=user_id, status=CollectionStatus.ABERTA)
        .order_by(Collection.created_at.desc())
        .first()
    )
    if collection:
        return collection

    collection = Collection(user_id=user_id, branch_id=branch_id)
    db.session.add(collection)
    db.session.flush()
    return collection


def add_scan_item(user_id: int, branch_id: int | None, barcode: str, quantity: float | str):
    parsed = parse_barcode(barcode)
    normalized = parsed["normalized"]
    product_code = parsed["product_code"]
    embedded_quantity = parsed.get("embedded_quantity")
    if not product_code:
        return {"success": False, "message": "Codigo MGV6 invalido para consulta.", "data": None}

    try:
        if quantity in (None, "", "null"):
            qty = Decimal(str(embedded_quantity if embedded_quantity else 1))
        else:
            qty = Decimal(str(quantity))
    except InvalidOperation:
        return {"success": False, "message": "Quantidade inválida.", "data": None}

    if qty <= 0:
        return {"success": False, "message": "Quantidade deve ser maior que zero.", "data": None}

    product = Product.query.filter_by(barcode=product_code, active=True).first()
    if not product:
        return {
            "success": False,
            "message": "Produto nao encontrado no banco local. Aguarde sincronizacao via agent e tente novamente.",
            "data": {"product_code": product_code},
        }

    collection = get_or_create_open_collection(user_id=user_id, branch_id=branch_id)
    existing_item = CollectionItem.query.filter_by(
        collection_id=collection.id,
        product_id=product.id,
    ).first()

    def _item_payload(item: CollectionItem) -> dict:
        p = item.product
        code = (p.internal_code if p and p.internal_code else item.scanned_code) or ""
        return {
            "id": item.id,
            "description": p.description if p else "-",
            "code": code,
            "unit": p.unit if p else "-",
            "quantity": format(Decimal(str(item.quantity)).normalize(), "f"),
        }

    if existing_item:
        existing_item.quantity = Decimal(existing_item.quantity) + qty
        db.session.commit()
        db.session.refresh(existing_item)
        return {
            "success": True,
            "message": "Item agrupado e quantidade incrementada.",
            "data": {
                "collection_id": collection.id,
                "item_id": existing_item.id,
                "updated": True,
                "item": _item_payload(existing_item),
            },
        }

    new_item = CollectionItem(
        collection_id=collection.id,
        product_id=product.id,
        scanned_code=product.internal_code or product_code or normalized,
        quantity=qty,
    )
    db.session.add(new_item)
    db.session.commit()
    db.session.refresh(new_item)
    return {
        "success": True,
        "message": "Item adicionado na coleta.",
        "data": {
            "collection_id": collection.id,
            "item_id": new_item.id,
            "updated": False,
            "item": _item_payload(new_item),
        },
    }


def preview_scan_item(user_id: int, branch_id: int | None, barcode: str, quantity: float | str = None):
    """
    Pré-visualiza a coleta sem persistir alteração.
    Retorna quantidade lida, total atual e total após confirmação.
    """
    parsed = parse_barcode(barcode)
    product_code = parsed["product_code"]
    embedded_quantity = parsed.get("embedded_quantity")
    if not product_code:
        return {"success": False, "message": "Codigo MGV6 invalido para consulta.", "data": None}

    try:
        if quantity in (None, "", "null"):
            qty_to_add = Decimal(str(embedded_quantity if embedded_quantity else 1))
        else:
            qty_to_add = Decimal(str(quantity))
    except InvalidOperation:
        return {"success": False, "message": "Quantidade inválida.", "data": None}

    if qty_to_add <= 0:
        return {"success": False, "message": "Quantidade deve ser maior que zero.", "data": None}

    product = Product.query.filter_by(barcode=product_code, active=True).first()
    if not product:
        return {
            "success": False,
            "message": "Produto nao encontrado no banco local. Aguarde sincronizacao via agent e tente novamente.",
            "data": {"product_code": product_code},
        }

    collection = get_or_create_open_collection(user_id=user_id, branch_id=branch_id)
    existing_item = CollectionItem.query.filter_by(
        collection_id=collection.id,
        product_id=product.id,
    ).first()

    current_total = Decimal(str(existing_item.quantity)) if existing_item else Decimal("0")
    next_total = current_total + qty_to_add

    return {
        "success": True,
        "message": "Confirme para adicionar o item.",
        "data": {
            "barcode": barcode,
            "qty_to_add": format(qty_to_add.normalize(), "f"),
            "current_total": format(current_total.normalize(), "f"),
            "next_total": format(next_total.normalize(), "f"),
            "product": {
                "id": product.id,
                "description": product.description,
                "code": product.internal_code or product.barcode or "",
                "unit": product.unit or "-",
            },
        },
    }


def get_open_collection_with_items(user_id: int):
    return (
        Collection.query.options(
            selectinload(Collection.items).selectinload(CollectionItem.product),
        )
        .filter_by(user_id=user_id, status=CollectionStatus.ABERTA)
        .order_by(Collection.created_at.desc())
        .first()
    )


def update_item_quantity(user_id: int, item_id: int, quantity: float | str):
    try:
        qty = Decimal(str(quantity))
    except InvalidOperation:
        return False, "Quantidade inválida."

    if qty <= 0:
        return False, "Quantidade deve ser maior que zero."

    item = (
        CollectionItem.query.join(Collection, CollectionItem.collection_id == Collection.id)
        .filter(
            CollectionItem.id == item_id,
            Collection.user_id == user_id,
            Collection.status == CollectionStatus.ABERTA,
        )
        .first()
    )
    if not item:
        return False, "Item não encontrado na coleta aberta."

    item.quantity = qty
    db.session.commit()
    return True, "Quantidade atualizada com sucesso."


def remove_item(user_id: int, item_id: int):
    item = (
        CollectionItem.query.join(Collection, CollectionItem.collection_id == Collection.id)
        .filter(
            CollectionItem.id == item_id,
            Collection.user_id == user_id,
            Collection.status == CollectionStatus.ABERTA,
        )
        .first()
    )
    if not item:
        return False, "Item não encontrado na coleta aberta."

    db.session.delete(item)
    db.session.commit()
    return True, "Item removido."


def clear_open_collection(user_id: int):
    collection = get_open_collection_with_items(user_id)
    if not collection:
        return False, "Nenhuma coleta aberta."

    for item in list(collection.items):
        db.session.delete(item)
    db.session.commit()
    return True, "Coleta limpa com sucesso."


def finalize_open_collection(user_id: int):
    collection = get_open_collection_with_items(user_id)
    if not collection:
        return False, "Nenhuma coleta aberta para finalizar."

    export_path = _export_collection_csv(collection)
    collection.status = CollectionStatus.FINALIZADA
    collection.finished_at = datetime.now(timezone.utc)
    db.session.commit()
    return True, f"Coleta finalizada com sucesso. CSV gerado em: {export_path}"


def _sanitize_filename_part(name: str) -> str:
    """Remove caracteres invalidos em nomes de arquivo (Windows/Unix)."""
    if not name or not str(name).strip():
        return ""
    cleaned = "".join(c if c not in '<>:"/\\|?*\n\r\t' else "_" for c in str(name).strip())
    cleaned = " ".join(cleaned.split())
    return cleaned[:80]


def _owner_label_for_export(collection: Collection) -> str:
    """Nome (ou identificador) do usuario da coleta para compor o nome do CSV."""
    owner = db.session.get(User, collection.user_id)
    if not owner:
        return f"user{collection.user_id}"
    if (owner.full_name or "").strip():
        part = _sanitize_filename_part(owner.full_name.strip())
        if part:
            return part
    email_local = (owner.email or "").split("@")[0].strip()
    if email_local:
        part = _sanitize_filename_part(email_local)
        if part:
            return part
    return f"user{collection.user_id}"


def _export_collection_csv(collection: Collection) -> str:
    FINALIZED_DIR.mkdir(parents=True, exist_ok=True)

    collection_date = datetime.now().strftime("%d-%m-%Y")
    owner_label = _owner_label_for_export(collection)
    base_name = f"coleta {collection_date} {owner_label}"
    target_path = FINALIZED_DIR / f"{base_name}.csv"

    suffix = 1
    while target_path.exists():
        suffix += 1
        target_path = FINALIZED_DIR / f"{base_name} ({suffix}).csv"

    lines = []
    for item in collection.items:
        code = (item.product.internal_code if item.product and item.product.internal_code else item.scanned_code) or ""
        qty = Decimal(str(item.quantity))
        qty_str = format(qty.normalize(), "f")
        lines.append(f"{code};{qty_str}")

    target_path.write_text("\n".join(lines), encoding="utf-8")
    return str(target_path)
