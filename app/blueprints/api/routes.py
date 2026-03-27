import os
import base64
import hashlib
from pathlib import Path

from dotenv import load_dotenv
from flask import current_app, jsonify, request
from flask_login import login_required

from app.blueprints.api import api_bp
from app.extensions import csrf
from app.blueprints.api.services import (
    lookup_product_by_barcode,
    search_products,
    upsert_products_from_agent,
)
from app.config import BASE_DIR


@api_bp.get("/health")
def health():
    return jsonify({"status": "ok"}), 200


@api_bp.get("/products/by-barcode")
@login_required
def get_product_by_barcode():
    barcode = request.args.get("barcode", "").strip()
    product = lookup_product_by_barcode(barcode)
    return jsonify(product), 200


@api_bp.get("/products/search")
@login_required
def search_products_endpoint():
    q = request.args.get("q", "").strip()
    limit = request.args.get("limit", type=int) or 15
    return jsonify({"results": search_products(q, limit=limit)}), 200


@api_bp.post("/sync/products")
@csrf.exempt
def sync_products():
    """
    Endpoint para o agent sincronizar produtos do banco externo para o VPS.
    Autenticacao via header: X-API-KEY.
    """
    # Re-carrega .env (sem depender de restart) para garantir que SYNC_API_KEY
    # esteja disponivel no processo atual.
    load_dotenv(BASE_DIR / ".env")

    expected_key = os.getenv("SYNC_API_KEY", "") or current_app.config.get("SYNC_API_KEY", "")
    provided_key = request.headers.get("X-API-KEY", "")

    if not expected_key:
        return jsonify({"success": False, "message": "SYNC_API_KEY nao configurada."}), 500

    if not provided_key or provided_key != expected_key:
        return jsonify({"success": False, "message": "Nao autorizado."}), 401

    payload = request.get_json(silent=True) or {}
    items = payload.get("items") or []

    result = upsert_products_from_agent(items)
    status_code = 200 if result.get("success") else 400
    return jsonify(result), status_code


@api_bp.post("/sync/finalizadas")
@csrf.exempt
def sync_finalizadas():
    """
    Recebe arquivos CSV de finalizadas enviados pelo agent.
    """
    load_dotenv(BASE_DIR / ".env")

    expected_key = os.getenv("SYNC_API_KEY", "") or current_app.config.get("SYNC_API_KEY", "")
    provided_key = request.headers.get("X-API-KEY", "")

    if not expected_key:
        return jsonify({"success": False, "message": "SYNC_API_KEY nao configurada."}), 500

    if not provided_key or provided_key != expected_key:
        return jsonify({"success": False, "message": "Nao autorizado."}), 401

    payload = request.get_json(silent=True) or {}
    filename = (payload.get("filename") or "").strip()
    content_b64 = payload.get("content_base64") or ""
    sent_sha256 = (payload.get("sha256") or "").strip().lower()

    if not filename or not content_b64:
        return jsonify({"success": False, "message": "Payload invalido."}), 400

    safe_name = Path(filename).name
    if not safe_name.lower().endswith(".csv"):
        return jsonify({"success": False, "message": "Apenas arquivos .csv sao aceitos."}), 400

    try:
        file_bytes = base64.b64decode(content_b64)
    except Exception:
        return jsonify({"success": False, "message": "content_base64 invalido."}), 400

    calc_sha256 = hashlib.sha256(file_bytes).hexdigest().lower()
    if sent_sha256 and sent_sha256 != calc_sha256:
        return jsonify({"success": False, "message": "Hash sha256 nao confere."}), 400

    target_dir = Path(BASE_DIR) / "finalizadas_sync"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / safe_name

    target_path.write_bytes(file_bytes)
    return jsonify(
        {
            "success": True,
            "message": "Arquivo sincronizado.",
            "filename": safe_name,
            "sha256": calc_sha256,
            "saved_to": str(target_path),
        }
    ), 200
