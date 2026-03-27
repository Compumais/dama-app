from decimal import Decimal, InvalidOperation

from sqlalchemy.orm import selectinload

from app.blueprints.requests.filters import sanitize_request_payload
from app.extensions import db, socketio
from app.models import Product, RequestStatusHistory, StockRequest, StockRequestItem
from app.models.stock_request import StockRequestStatus


ALLOWED_TRANSITIONS = {
    StockRequestStatus.PENDENTE: {
        StockRequestStatus.PRONTO,
    },
    StockRequestStatus.PRONTO: {
        # Two-status flow: nothing after "pronto" for now.
    },
    StockRequestStatus.ENTREGUE: set(),
    StockRequestStatus.CANCELADO: set(),
}


def create_stock_request(payload: dict):
    clean_payload = sanitize_request_payload(payload)
    try:
        branch_id = int(clean_payload.get("branch_id"))
    except (TypeError, ValueError):
        return {"success": False, "message": "Filial invalida.", "data": None}

    items = []
    for item in clean_payload["items"]:
        try:
            product_id = int(item["product_id"])
            quantity = Decimal(str(item["quantity"]))
        except (KeyError, TypeError, ValueError, InvalidOperation):
            return {"success": False, "message": "Item invalido na requisição.", "data": None}

        if quantity <= 0:
            return {"success": False, "message": "Quantidade deve ser maior que zero.", "data": None}

        product = Product.query.get(product_id)
        if not product or not product.active:
            return {"success": False, "message": "Produto nao encontrado ou inativo.", "data": None}

        scanned_code = item["scanned_code"] or product.barcode
        items.append(
            StockRequestItem(
                product_id=product.id,
                scanned_code=scanned_code,
                quantity=quantity,
                notes=item["notes"] or None,
            )
        )

    if not items:
        return {"success": False, "message": "Informe pelo menos um item.", "data": None}

    stock_request = StockRequest(
        branch_id=branch_id,
        requested_by_user_id=int(payload["requested_by_user_id"]),
        notes=clean_payload["notes"] or None,
    )
    stock_request.items = items
    db.session.add(stock_request)
    db.session.flush()
    _append_status_history(
        stock_request=stock_request,
        previous_status=None,
        new_status=stock_request.status,
        changed_by_user_id=stock_request.requested_by_user_id,
        notes="Requisição criada",
    )
    db.session.commit()
    _emit_request_event("request_created", stock_request)

    return {
        "success": True,
        "message": "Requisicao criada com sucesso.",
        "data": {"id": stock_request.id},
    }


def list_stock_requests(status: str | None = None, branch_id: int | None = None):
    query = StockRequest.query.options(
        selectinload(StockRequest.branch),
        selectinload(StockRequest.requested_by),
        selectinload(StockRequest.items).selectinload(StockRequestItem.product),
    ).order_by(StockRequest.created_at.desc())

    if status:
        try:
            parsed_status = StockRequestStatus(status)
            query = query.filter(StockRequest.status == parsed_status)
        except ValueError:
            pass

    if branch_id:
        query = query.filter(StockRequest.branch_id == branch_id)

    return query.all()


def list_stock_requests_for_consultation(
    *,
    role_slug: str,
    user_id: int,
    status: str | None = None,
):
    """
    Listagem para perfis que nao operam a fila do acougue:
    - solicitante_filial: apenas requisicoes criadas pelo proprio usuario
    - gestor_consulta / administrador: todas as requisicoes (consulta)
    """
    query = StockRequest.query.options(
        selectinload(StockRequest.branch),
        selectinload(StockRequest.requested_by),
        selectinload(StockRequest.items).selectinload(StockRequestItem.product),
    ).order_by(StockRequest.created_at.desc())

    if status:
        try:
            parsed_status = StockRequestStatus(status)
            query = query.filter(StockRequest.status == parsed_status)
        except ValueError:
            pass

    slug = (role_slug or "").strip().lower()
    if slug == "solicitante_filial":
        query = query.filter(StockRequest.requested_by_user_id == user_id)

    return query.all()


def change_stock_request_status(
    stock_request: StockRequest,
    new_status_raw: str,
    changed_by_user_id: int,
    notes: str | None = None,
):
    try:
        new_status = StockRequestStatus(new_status_raw)
    except ValueError:
        return False, "Status invalido."

    current_status = stock_request.status
    if new_status == current_status:
        return False, "A requisição já está neste status."

    allowed_next = ALLOWED_TRANSITIONS.get(current_status, set())
    if new_status not in allowed_next:
        return False, "Transição de status não permitida."

    stock_request.status = new_status
    _append_status_history(
        stock_request=stock_request,
        previous_status=current_status,
        new_status=new_status,
        changed_by_user_id=changed_by_user_id,
        notes=(notes or "").strip() or None,
    )
    db.session.commit()
    _emit_request_event("request_status_changed", stock_request)
    return True, "Status atualizado com sucesso."


def _append_status_history(
    stock_request: StockRequest,
    previous_status: StockRequestStatus | None,
    new_status: StockRequestStatus,
    changed_by_user_id: int,
    notes: str | None,
):
    history = RequestStatusHistory(
        stock_request_id=stock_request.id,
        previous_status=previous_status,
        new_status=new_status,
        changed_by_user_id=changed_by_user_id,
        notes=notes,
    )
    db.session.add(history)


def _emit_request_event(event_name: str, stock_request: StockRequest) -> None:
    socketio.emit(
        "requests_updated",
        {
            "event": event_name,
            "request_id": stock_request.id,
            "status": stock_request.status.value,
            "branch_id": stock_request.branch_id,
        },
    )
