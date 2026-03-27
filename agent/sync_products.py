import os
import time
import base64
import hashlib
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Variavel de ambiente obrigatoria ausente: {name}")
    return value


def _build_external_database_url() -> str:
    host = _required_env("EXTERNAL_DB_HOST")
    port = os.getenv("EXTERNAL_DB_PORT", "5432").strip()
    database = _required_env("EXTERNAL_DB_NAME")
    username = _required_env("EXTERNAL_DB_USER")
    password = _required_env("EXTERNAL_DB_PASSWORD")
    driver = os.getenv("EXTERNAL_DB_DRIVER", "psycopg2").strip()
    return f"postgresql+{driver}://{username}:{password}@{host}:{port}/{database}"


def _vps_sync_endpoint() -> str:
    base_url = _required_env("VPS_API_URL").rstrip("/")
    return f"{base_url}/api/sync/products"


def _vps_finalizadas_endpoint() -> str:
    base_url = _required_env("VPS_API_URL").rstrip("/")
    return f"{base_url}/api/sync/finalizadas"


def _batch_size() -> int:
    try:
        return max(1, int(os.getenv("AGENT_BATCH_SIZE", "500")))
    except ValueError:
        return 500


def _sync_interval_seconds() -> int:
    try:
        return max(60, int(os.getenv("SYNC_INTERVAL_SECONDS", "3600")))
    except ValueError:
        return 3600


def _finalizadas_poll_seconds() -> int:
    try:
        return max(2, int(os.getenv("FINALIZADAS_POLL_SECONDS", "5")))
    except ValueError:
        return 5


def _finalizadas_dir() -> Path:
    configured = (os.getenv("FINALIZADAS_DIR") or "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return Path(__file__).resolve().parents[1] / "finalizadas"


def _safe_response_json(response: requests.Response) -> dict:
    """
    Parseia resposta como JSON; se nao for JSON, devolve um payload descritivo.
    Isso evita quebrar o agent quando o VPS retorna HTML (ex: erro CSRF/debug).
    """
    try:
        return response.json()
    except Exception:
        # Mantem o erro legivel para troubleshooting.
        return {
            "success": False,
            "message": "Resposta nao-JSON do VPS.",
            "vps_status": response.status_code,
            "content_type": response.headers.get("content-type"),
            "raw_preview": (response.text or "")[:400],
        }


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest().lower()


def _run_products_sync(engine, endpoint: str, sync_api_key: str, batch_size: int) -> None:
    print("[products] iniciando sincronizacao")
    batch: list[dict[str, Any]] = []
    created_total = 0
    updated_total = 0
    sent_total = 0

    sql = text(
        """
        SELECT CAST(codigo AS TEXT) AS codigo,
               nome
        FROM produto
        """
    )
    with engine.connect() as connection:
        result = connection.execute(sql)
        for row in result:
            codigo = (row[0] or "").strip()
            nome = (row[1] or "").strip()
            if not codigo or not nome:
                continue

            batch.append({"codigo": codigo, "nome": nome})
            if len(batch) >= batch_size:
                payload = {"items": batch}
                response = requests.post(
                    endpoint,
                    json=payload,
                    headers={"X-API-KEY": sync_api_key},
                    timeout=60,
                )
                response_data = _safe_response_json(response)
                if response.status_code != 200 or not response_data.get("success"):
                    raise RuntimeError(
                        f"Falha ao sincronizar batch. status={response.status_code}, resp={response_data}"
                    )
                created_total += int(response_data.get("created", 0))
                updated_total += int(response_data.get("updated", 0))
                sent_total += len(batch)
                print(
                    f"[sync] enviado={sent_total} created={created_total} updated={updated_total}"
                )
                batch = []

        if batch:
            payload = {"items": batch}
            response = requests.post(
                endpoint,
                json=payload,
                headers={"X-API-KEY": sync_api_key},
                timeout=60,
            )
            response_data = _safe_response_json(response)
            if response.status_code != 200 or not response_data.get("success"):
                raise RuntimeError(
                    f"Falha ao sincronizar batch final. status={response.status_code}, resp={response_data}"
                )
            created_total += int(response_data.get("created", 0))
            updated_total += int(response_data.get("updated", 0))
            sent_total += len(batch)
            print(
                f"[sync] finalizado. enviado={sent_total} created={created_total} updated={updated_total}"
            )
    print("[products] sincronizacao concluida")


def _sync_finalizadas_once(
    finalizadas_dir: Path,
    endpoint: str,
    sync_api_key: str,
    state: dict[str, tuple[float, int, str]],
) -> None:
    if not finalizadas_dir.exists():
        return

    for file_path in sorted(finalizadas_dir.glob("*.csv")):
        try:
            stat = file_path.stat()
            mtime = stat.st_mtime
            size = stat.st_size
            cache_key = str(file_path.resolve())
            previous = state.get(cache_key)

            if previous and previous[0] == mtime and previous[1] == size:
                continue

            content = file_path.read_bytes()
            sha256 = _sha256_bytes(content)
            if previous and previous[2] == sha256:
                state[cache_key] = (mtime, size, sha256)
                continue

            payload = {
                "filename": file_path.name,
                "content_base64": base64.b64encode(content).decode("ascii"),
                "sha256": sha256,
                "mtime": mtime,
            }
            response = requests.post(
                endpoint,
                json=payload,
                headers={"X-API-KEY": sync_api_key},
                timeout=60,
            )
            response_data = _safe_response_json(response)
            if response.status_code != 200 or not response_data.get("success"):
                print(
                    f"[finalizadas] erro ao enviar {file_path.name}: "
                    f"status={response.status_code} resp={response_data}"
                )
                continue

            state[cache_key] = (mtime, size, sha256)
            print(f"[finalizadas] sincronizado: {file_path.name}")
        except Exception as exc:
            print(f"[finalizadas] falha em {file_path.name}: {exc}")


def main() -> None:
    load_dotenv()

    external_db_url = _build_external_database_url()
    engine = create_engine(external_db_url, pool_pre_ping=True)

    products_endpoint = _vps_sync_endpoint()
    finalizadas_endpoint = _vps_finalizadas_endpoint()
    sync_api_key = _required_env("SYNC_API_KEY")

    batch_size = _batch_size()
    sync_interval = _sync_interval_seconds()
    poll_interval = _finalizadas_poll_seconds()
    finalizadas_dir = _finalizadas_dir()
    finalizadas_state: dict[str, tuple[float, int, str]] = {}

    print(
        "[agent] iniciado com "
        f"SYNC_INTERVAL_SECONDS={sync_interval}, "
        f"FINALIZADAS_POLL_SECONDS={poll_interval}, "
        f"FINALIZADAS_DIR={finalizadas_dir}"
    )

    next_products_sync_at = 0.0
    while True:
        now = time.time()
        if now >= next_products_sync_at:
            try:
                _run_products_sync(
                    engine=engine,
                    endpoint=products_endpoint,
                    sync_api_key=sync_api_key,
                    batch_size=batch_size,
                )
            except Exception as exc:
                print(f"[products] erro na sincronizacao: {exc}")
            finally:
                next_products_sync_at = time.time() + sync_interval

        _sync_finalizadas_once(
            finalizadas_dir=finalizadas_dir,
            endpoint=finalizadas_endpoint,
            sync_api_key=sync_api_key,
            state=finalizadas_state,
        )

        time.sleep(poll_interval)


if __name__ == "__main__":
    main()

