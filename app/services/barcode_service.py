import re
import os

def normalize_barcode(raw_value: str) -> str:
    return (raw_value or "").strip()


def parse_barcode(raw_barcode: str) -> dict:
    """
    Extrai o codigo de produto no padrao MGV6.
    Regras:
    - se vier exatamente 6 digitos, usa direto
    - se iniciar com '2' e tiver ao menos 7 digitos, usa posicoes 2..7
    - fallback: primeiros 6 digitos
    """
    normalized = normalize_barcode(raw_barcode)
    digits_only = re.sub(r"\D", "", normalized)
    product_code = _extract_mgv6_product_code(digits_only)
    embedded_quantity = _extract_mgv6_embedded_quantity(digits_only)

    return {
        "raw": raw_barcode,
        "normalized": normalized,
        "product_code": product_code,
        "embedded_quantity": embedded_quantity,
    }


def _extract_mgv6_product_code(digits_only: str) -> str:
    """
    Padrão da imagem MGV6:
    - aplicação: 2
    - código do produto: CCCC (4 dígitos)
    - separador: 0
    - quantidade/peso: PPPPPP ou QQQQQQ
    - dígito verificador

    Também permite ajuste por variáveis de ambiente.
    """
    if len(digits_only) < 6:
        return ""

    start_pos = int(os.getenv("MGV6_PRODUCT_CODE_START", "2"))
    end_pos = int(os.getenv("MGV6_PRODUCT_CODE_END", "5"))
    # Converte posições 1-based inclusivas para slice Python.
    start_idx = max(start_pos - 1, 0)
    end_idx = min(end_pos, len(digits_only))

    code = digits_only[start_idx:end_idx]

    # Fallback conservador para EAN-13 com aplicação "2" e separador "0".
    if not code and len(digits_only) >= 6 and digits_only.startswith("2"):
        if digits_only[5] == "0":
            return digits_only[1:5]
        return digits_only[1:6]
    return code


def _extract_mgv6_embedded_quantity(digits_only: str):
    if len(digits_only) < 12:
        return None

    qty_start_env = os.getenv("MGV6_QTY_START")
    qty_end_env = os.getenv("MGV6_QTY_END")
    # Heuristica para EAN-13 MGV6 no formato do exemplo do usuario:
    # 2 + CCCC + 0 + QQQQQQ + DV  => quantidade em 7..12.
    if qty_start_env and qty_end_env:
        qty_start = int(qty_start_env)
        qty_end = int(qty_end_env)
    elif len(digits_only) == 13 and digits_only.startswith("2") and digits_only[5] == "0":
        qty_start = 7
        qty_end = 12
    else:
        qty_start = 7
        qty_end = 12

    qty_decimals = int(os.getenv("MGV6_QTY_DECIMALS", "3"))

    start_idx = max(qty_start - 1, 0)
    end_idx = min(qty_end, len(digits_only))
    qty_digits = digits_only[start_idx:end_idx]

    if not qty_digits.isdigit():
        return None

    qty_value = int(qty_digits)
    if qty_decimals > 0:
        return qty_value / (10 ** qty_decimals)
    return float(qty_value)
