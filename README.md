# Coletor DAMA

Sistema web interno para operação de açougue e requisição entre filiais, com foco em uso prático no dia a dia operacional (tablet/celular), arquitetura modular e evolução contínua.

## Proposta do projeto

A plataforma integra 3 módulos principais:

- **Coletor operacional**: leitura de código de barras (scanner/câmera), agrupamento por produto e ajuste de quantidade.
- **Requisições de estoque**: criação, acompanhamento e mudança de status de requisições entre filiais e açougue.
- **Administração**: cadastro e gestão básica de usuários, filiais e produtos.

Objetivos principais:

- simplicidade operacional;
- código organizado para crescer sem virar monólito;
- separação de responsabilidades (rotas, serviços, models, templates);
- segurança básica com autenticação e autorização por perfil.

## Stack

- Python + Flask
- Flask-SQLAlchemy + Flask-Migrate (Alembic)
- Flask-Login + Flask-WTF
- PostgreSQL
- Jinja2 (renderização server-side)

## Estrutura de código

```text
coletor_dama/
├── app/
│   ├── __init__.py              # Application Factory e registro de módulos
│   ├── config.py                # Configurações por ambiente e variáveis .env
│   ├── extensions.py            # db, migrate, login_manager, csrf
│   ├── cli.py                   # comandos CLI (ex.: seed-initial)
│   │
│   ├── blueprints/
│   │   ├── auth/                # login/logout
│   │   ├── dashboard/           # visão inicial
│   │   ├── admin/               # módulo administrativo
│   │   ├── requests/            # requisições de estoque
│   │   ├── collector/           # módulo de coleta
│   │   └── api/                 # endpoints internos auxiliares
│   │
│   ├── models/                  # entidades SQLAlchemy
│   ├── services/                # serviços de domínio e integrações externas
│   ├── templates/               # telas Jinja2
│   ├── static/                  # assets estáticos
│   └── utils/                   # permissões e utilitários
│
├── run.py                       # ponto de entrada local
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
└── DOCKER.md
```

## Modelagem principal

Entidades já implementadas:

- `Role`
- `User`
- `Branch`
- `Product`
- `StockRequest`
- `StockRequestItem`
- `Collection`
- `CollectionItem`
- `RequestStatusHistory`

Relacionamentos cobrem:

- usuários e perfis;
- usuários e filiais;
- requisição com cabeçalho + itens;
- coleta com cabeçalho + itens;
- histórico de alteração de status.

## Perfis e permissões

Perfis iniciais:

- `administrador`
- `solicitante_filial`
- `acougueiro`
- `gestor_consulta`

Controle de acesso por decorator: `role_required(...)`.

## Rotas da plataforma

### Auth (`/auth`)

- `GET|POST /auth/login` - login
- `GET /auth/logout` - logout

### Dashboard (`/dashboard`)

- `GET /dashboard/` - página inicial autenticada

### Admin (`/admin`)

- `GET /admin/` - visão geral administrativa
- `GET|POST /admin/users` - listagem e criação de usuários
- `GET|POST /admin/branches` - listagem e criação de filiais
- `GET|POST /admin/products` - listagem e criação de produtos

### Requisições (`/requests`)

- `GET /requests/` - listagem com filtros
- `GET|POST /requests/new` - criação via formulário
- `POST /requests/` - criação via JSON (endpoint interno)
- `POST /requests/<request_id>/status` - mudança de status

Status disponíveis:

- `pendente`
- `em_separacao`
- `pronto`
- `entregue`
- `cancelado`

### Coletor (`/collector`)

- `GET /collector/` - tela operacional do coletor
- `POST /collector/scan` - leitura de código (form e JSON)
- `POST /collector/items/<item_id>/quantity` - editar quantidade
- `POST /collector/items/<item_id>/remove` - remover item
- `POST /collector/clear` - limpar coleta aberta
- `POST /collector/finalize` - finalizar coleta

### API interna (`/api`)

- `GET /api/health` - healthcheck
- `GET /api/products/by-barcode` - busca auxiliar por código
- `POST /api/sync/products` - sincronizar produtos via agent (auth por `X-API-KEY`)
- `POST /api/sync/finalizadas` - sincronizar CSVs da pasta `finalizadas` via agent (auth por `X-API-KEY`)

## Sincronização de produtos (agent)

O coletor consulta **somente** o banco local (`Product`). Portanto, antes de operar, é necessário alimentar `products` usando o agent que vai ao Postgres externo e envia os dados para o VPS.

### Query no banco externo

O agent executa:

```sql
SELECT codigo, nome
FROM produto;
```

### Endpoint no VPS

- `POST /api/sync/products`
- autenticação: header `X-API-KEY` (variável `SYNC_API_KEY` no VPS)
- payload:
  - `{ "items": [{"codigo": "...", "nome": "..."}, ...] }`

### Rodar o agent

```bash
cd agent
python sync_products.py
```

O arquivo de variáveis está em `agent/.env.example`.

### Execução contínua do agent

O `sync_products.py` agora roda em loop contínuo:

- sincroniza produtos a cada `SYNC_INTERVAL_SECONDS` (padrão: `3600` = 1 hora);
- sincroniza em tempo quase real os arquivos `.csv` da pasta `finalizadas`, verificando mudanças a cada `FINALIZADAS_POLL_SECONDS` (padrão: `5` segundos).

Variáveis relevantes do agent:

- `SYNC_INTERVAL_SECONDS`
- `FINALIZADAS_POLL_SECONDS`
- `FINALIZADAS_DIR` (opcional; se vazio, usa `../finalizadas`)

### Extração MGV6 (no coletor)

Parâmetros da extração de código do padrão MGV6:

- `MGV6_PRODUCT_CODE_START`
- `MGV6_PRODUCT_CODE_END`

## Setup rápido (local)

1. Criar e ativar ambiente virtual.
2. Instalar dependências:

```bash
pip install -r requirements.txt
```

3. Criar `.env` a partir do exemplo:

```bash
cp .env.example .env
```

No PowerShell:

```powershell
Copy-Item .env.example .env
```

4. Inicializar banco:

```bash
flask --app run.py db init
flask --app run.py db migrate -m "initial schema"
flask --app run.py db upgrade
```

5. Popular dados iniciais (roles + admin):

```bash
flask --app run.py seed-initial
```

6. Executar aplicação:

```bash
python run.py
```

## Usuário administrador inicial

Após `seed-initial`, use:

- e-mail: `admin@local.dev`
- senha: `admin123`

Esses valores podem ser alterados no `.env`:

- `ADMIN_NAME`
- `ADMIN_EMAIL`
- `ADMIN_PASSWORD`

## Docker

A documentação de containers está em `DOCKER.md`, com build, compose, migrations e seed.

## Status atual e próximos passos

Base funcional já implementada para MVP técnico:

- autenticação;
- módulo admin básico;
- módulo de requisições;
- módulo coletor;
- sincronização offline de produtos via agent (sem consulta externa em tempo real).

Evoluções recomendadas:

- edição/inativação no admin;
- tela de detalhe de requisição com histórico completo;
- testes automatizados (unitários e integração);
- observabilidade/logs estruturados para operação.
