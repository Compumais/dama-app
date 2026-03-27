# Docker no projeto Coletor DAMA

Este documento explica os arquivos Docker criados e como usar o ambiente local com containers.

## Arquivos criados

### `Dockerfile`

Responsável por montar a imagem da aplicação Flask.

Principais pontos:

- Usa imagem base `python:3.12-slim`.
- Define `WORKDIR` como `/app`.
- Instala dependências com `pip install -r requirements.txt`.
- Copia o código do projeto para dentro da imagem.
- Expõe a porta `5000`.
- Inicia a aplicação com `python run.py`.

### `docker-compose.yml`

Orquestra os serviços da aplicação e banco PostgreSQL.

Serviços:

- `web`:
  - Build a partir do `Dockerfile`.
  - Carrega variáveis do arquivo `.env`.
  - Sobrescreve `DATABASE_URL` para usar o host interno `db`.
  - Publica porta `5000`.
  - Depende do `db` com healthcheck.
- `db`:
  - Usa imagem `postgres:16-alpine`.
  - Cria banco `coletor_dama`.
  - Usuário/senha padrão: `postgres/postgres`.
  - Publica porta `5432`.
  - Usa volume persistente `postgres_data`.

### `.dockerignore`

Evita enviar arquivos desnecessários para o build, acelerando o processo e reduzindo tamanho da imagem.

Ignora, por exemplo:

- caches Python (`__pycache__`, `*.pyc`)
- ambientes virtuais (`.venv`, `venv`)
- metadados de IDE (`.idea`, `.vscode`)
- `.git` e logs

## Como subir o ambiente

## 1) Ajustar `.env`

Garanta que existe um `.env` na raiz do projeto.

Pode copiar de `.env.example`:

```bash
cp .env.example .env
```

No Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

## 2) Build e subida dos containers

```bash
docker compose up --build -d
```

## 3) Ver logs da aplicação

```bash
docker compose logs -f web
```

## 4) Executar migrations

Se você já tiver migrations criadas:

```bash
docker compose exec web flask --app run.py db upgrade
```

Se ainda for criar a migration inicial:

```bash
docker compose exec web flask --app run.py db init
docker compose exec web flask --app run.py db migrate -m "initial schema"
docker compose exec web flask --app run.py db upgrade
```

## 5) Rodar seed inicial

```bash
docker compose exec web flask --app run.py seed-initial
```

## 5.1) Sincronizar produtos via agent

Como o coletor consulta somente o banco local, antes de operar você deve alimentar a tabela `products` via o agent sincronizador.

1. Configure no seu `.env` da VPS o valor `SYNC_API_KEY`.
2. Rode o agent local (no servidor do banco externo) apontando para a API do VPS:
   - endpoint: `${VPS_API_URL}/api/sync/products`
   - header: `X-API-KEY: SYNC_API_KEY`

## 6) Acessar sistema

- App Flask: [http://localhost:5000](http://localhost:5000)
- PostgreSQL: `localhost:5432`

## Comandos úteis

Parar containers:

```bash
docker compose stop
```

Derrubar containers e rede:

```bash
docker compose down
```

Derrubar tudo incluindo volume do banco (apaga dados):

```bash
docker compose down -v
```
