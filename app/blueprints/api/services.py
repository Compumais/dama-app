from __future__ import annotations

from sqlalchemy import func

from app.extensions import db
from app.models import Product
from app.services.barcode_service import parse_barcode


def lookup_product_by_barcode(barcode: str) -> dict:
    raw = (barcode or "").strip()
    parsed = parse_barcode(raw)
    product_code = parsed.get("product_code") or ""
    normalized = parsed.get("normalized") or raw

    if not product_code:
        return {
            "found": False,
            "barcode": normalized,
            "message": "Codigo invalido para consulta.",
        }

    product = Product.query.filter_by(barcode=product_code, active=True).first()
    if not product:
        return {
            "found": False,
            "barcode": product_code,
            "message": "Produto nao encontrado no banco local. Sincronize via agent.",
        }

    embedded_quantity = parsed.get("embedded_quantity")

    return {
        "found": True,
        "barcode": product.barcode,
        "embedded_quantity": embedded_quantity,
        "product": {
            "id": product.id,
            "barcode": product.barcode,
            "description": product.description,
            "unit": product.unit,
        },
    }


def search_products(query: str, limit: int = 15) -> list[dict]:
    q = (query or "").strip()
    if not q:
        return []

    safe_limit = max(1, min(int(limit or 15), 30))
    like = f"%{q.lower()}%"
    products = (
        Product.query.filter(Product.active.is_(True))
        .filter(func.lower(Product.description).like(like) | func.lower(Product.barcode).like(like))
        .order_by(Product.description.asc())
        .limit(safe_limit)
        .all()
    )
    return [
        {
            "id": p.id,
            "barcode": p.barcode,
            "description": p.description,
            "unit": p.unit,
        }
        for p in products
    ]


def upsert_products_from_agent(items: list[dict]) -> dict:
    """
    Upsert local de produtos com base em dados recebidos do agent.

    Mapeamento (conforme planilha do banco externo):
    - produto.codigo -> Product.barcode e Product.internal_code
    - produto.nome -> Product.description
    - unit -> "UN"
    - active -> True
    """
    if not items:
        return {"success": False, "message": "Lista de itens vazia.", "created": 0, "updated": 0}

    created = 0
    updated = 0
    processed = 0

    # Cache simples para evitar queries repetidas quando o payload tem duplicatas
    seen_codes = {}

    for raw in items:
        if not isinstance(raw, dict):
            continue

        codigo = (raw.get("codigo") or raw.get("code") or raw.get("barcode") or "").strip()
        nome = (raw.get("nome") or raw.get("name") or raw.get("description") or "").strip()

        if not codigo or not nome:
            continue

        processed += 1

        if codigo in seen_codes:
            product = seen_codes[codigo]
        else:
            product = Product.query.filter_by(barcode=codigo).first()
            seen_codes[codigo] = product

        if product:
            product.internal_code = codigo
            product.description = nome
            product.unit = "UN"
            product.active = True
            updated += 1
        else:
            product = Product(
                barcode=codigo,
                internal_code=codigo,
                description=nome,
                unit="UN",
                active=True,
            )
            db.session.add(product)
            created += 1

    if processed == 0:
        return {"success": False, "message": "Nenhum item valido para sincronizacao.", "created": 0, "updated": 0}

    db.session.commit()
    return {
        "success": True,
        "message": "Sincronizacao concluida.",
        "created": created,
        "updated": updated,
    }
