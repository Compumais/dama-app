def sanitize_request_payload(payload: dict) -> dict:
    items = payload.get("items") or []
    clean_items = []
    for item in items:
        if not isinstance(item, dict):
            continue
        clean_items.append(
            {
                "product_id": item.get("product_id"),
                "scanned_code": (item.get("scanned_code") or "").strip(),
                "quantity": item.get("quantity"),
                "notes": (item.get("notes") or "").strip(),
            }
        )

    return {
        "branch_id": payload.get("branch_id"),
        "notes": (payload.get("notes") or "").strip(),
        "items": clean_items,
    }
