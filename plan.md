Quero que você atue como um arquiteto de software sênior e desenvolvedor full stack experiente em Flask, sistemas internos operacionais, aplicações para tablet/mobile, integração com leitores de código de barras e arquitetura modular limpa.

Sua tarefa é projetar e implementar a base de um sistema web interno 3 em 1 para operação de açougue e requisição entre filiais, com foco em simplicidade operacional, performance, organização do código, escalabilidade futura e boa usabilidade em tablets e celulares.

# Objetivo do sistema

O sistema será composto por 3 módulos principais integrados:

1. Coletor do açougueiro
2. Gestão de requisições de ajuste/abastecimento de estoque
3. Painel administrativo/configurações

O sistema será utilizado em ambiente operacional real, por usuários de filiais e por açougueiros, principalmente via tablet ou celular, com leitura de código de barras por scanner HID/bluetooth e possibilidade futura de leitura por câmera.

# Stack obrigatória

- Backend: Python + Flask
- Frontend: HTML renderizado com Jinja2
- Estilo: Tailwind CSS
- Banco de dados: PostgreSQL
- ORM: SQLAlchemy
- Migrações: Alembic / Flask-Migrate
- Autenticação: Flask-Login
- Variáveis de ambiente: python-dotenv
- JavaScript: apenas o necessário para interações leves
- Opcional e recomendado: HTMX para atualização parcial de interface sem transformar o projeto em SPA

# Diretrizes gerais de arquitetura

Quero uma arquitetura limpa, modular e profissional, evitando código monolítico ou bagunçado.

## Requisitos obrigatórios de arquitetura

- Estruturar o projeto com Flask Application Factory
- Separar por Blueprints
- Separar responsabilidades em camadas:
  - routes/controllers
  - services
  - models
  - repositories ou acesso a dados quando fizer sentido
  - templates
  - static
- Não colocar regra de negócio diretamente nas rotas
- Não colocar lógica complexa diretamente no template
- Criar base preparada para crescimento
- Código legível, organizado e padronizado
- Preparar o projeto para uso em produção futuramente

# Estrutura desejada do projeto

Sugira e implemente uma estrutura semelhante a esta:

project/
│
├── app/
│   ├── __init__.py
│   ├── extensions.py
│   ├── config.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── role.py
│   │   ├── branch.py
│   │   ├── product.py
│   │   ├── stock_request.py
│   │   ├── stock_request_item.py
│   │   ├── collection.py
│   │   ├── collection_item.py
│   │   └── request_status_history.py
│   │
│   ├── blueprints/
│   │   ├── auth/
│   │   │   ├── routes.py
│   │   │   ├── forms.py
│   │   │   └── services.py
│   │   │
│   │   ├── dashboard/
│   │   │   └── routes.py
│   │   │
│   │   ├── collector/
│   │   │   ├── routes.py
│   │   │   ├── services.py
│   │   │   └── utils.py
│   │   │
│   │   ├── requests/
│   │   │   ├── routes.py
│   │   │   ├── services.py
│   │   │   └── filters.py
│   │   │
│   │   ├── admin/
│   │   │   ├── routes.py
│   │   │   ├── services.py
│   │   │   └── forms.py
│   │   │
│   │   └── api/
│   │       ├── routes.py
│   │       └── services.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── product_service.py
│   │   ├── collector_service.py
│   │   ├── stock_request_service.py
│   │   ├── admin_service.py
│   │   └── barcode_service.py
│   │
│   ├── templates/
│   │   ├── base.html
│   │   ├── components/
│   │   ├── auth/
│   │   ├── dashboard/
│   │   ├── collector/
│   │   ├── requests/
│   │   └── admin/
│   │
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── img/
│   │
│   └── utils/
│       ├── decorators.py
│       ├── permissions.py
│       ├── validators.py
│       └── helpers.py
│
├── migrations/
├── requirements.txt
├── .env.example
├── run.py
└── README.md

# Contexto funcional do sistema

## Módulo 1: Coletor do açougueiro

Este módulo funcionará como uma espécie de coletor operacional.

### Objetivo
O açougueiro irá escanear etiquetas com código de barras e o sistema deverá:

- identificar o produto
- adicionar em uma lista
- agrupar por código/produto
- somar a quantidade automaticamente
- exibir a lista consolidada em tempo real

### Comportamento esperado
- O usuário abre uma coleta
- Escaneia vários códigos
- Cada leitura adiciona ou incrementa a quantidade do item correspondente
- A tela mostra:
  - código de barras
  - descrição
  - quantidade acumulada
  - unidade de medida
- O usuário pode:
  - editar quantidade
  - remover item
  - limpar coleta
  - finalizar coleta

### Requisitos técnicos
- O sistema deve estar preparado para dois cenários:
  1. código de barras representando apenas o produto
  2. código de barras contendo peso ou quantidade embutida futuramente
- Por enquanto, implementar inicialmente o modo simples: código identifica produto e soma +1 ou quantidade manual
- Estruturar o código para permitir futura expansão de parsing avançado de etiquetas
- Criar um serviço/barcode_service.py preparado para regras futuras de interpretação de código

## Módulo 2: Requisições de ajuste/abastecimento de estoque

Este módulo será usado pelas filiais para solicitar produtos ao açougue.

### Fluxo esperado
- Usuário da filial faz login
- Acessa tela de nova requisição
- Escaneia ou busca um produto
- Adiciona item com quantidade
- Pode incluir múltiplos itens na mesma requisição
- Envia a requisição

### Cada requisição deve registrar
- filial solicitante
- usuário solicitante
- data e hora
- status
- observação opcional
- lista de itens

### Cada item da requisição deve conter
- produto
- código lido
- quantidade
- observação opcional

### Visualização do açougueiro
O açougueiro deve conseguir visualizar as requisições em tablet de forma organizada:

- agrupadas por filial
- com filtros por status
- ordenadas por data/hora
- com destaque para requisições pendentes

### Status da requisição
Implementar inicialmente os seguintes status:
- pendente
- em_separacao
- pronto
- entregue
- cancelado

### Também implementar histórico de status
Toda alteração de status deve gerar um registro em request_status_history.

## Módulo 3: Administração / Configurações

Este módulo será usado para gerenciar a base do sistema.

### Deve conter telas para:
- cadastro de usuários
- cadastro de filiais
- cadastro de produtos
- cadastro de perfis/permissões
- ativação/inativação de usuários e filiais
- parâmetros futuros do sistema

# Regras de negócio principais

## Usuários e permissões
O sistema deve ter controle de perfis.

Perfis iniciais:
- Administrador
- Solicitante de filial
- Açougueiro
- Gestor/Consulta

### Regras
- Administrador acessa tudo
- Solicitante cria e acompanha requisições da própria filial
- Açougueiro visualiza e atende requisições
- Gestor pode consultar dados e relatórios futuramente

Implementar sistema de autorização com decorators, sem espalhar ifs de permissão pelo sistema.

## Produtos
Cada produto deve ter pelo menos:
- id
- código de barras
- código interno opcional
- descrição
- unidade de medida
- ativo

## Filiais
Cada filial deve ter:
- id
- nome
- código
- ativa

## Coletas
Uma coleta do açougueiro deve possuir:
- id
- usuário responsável
- filial opcional se necessário
- status
- data de criação
- data de finalização

## Requisições
Uma requisição deve possuir:
- id
- filial
- usuário solicitante
- status
- observação
- created_at
- updated_at

# Modelagem inicial obrigatória

Implemente os models com SQLAlchemy para as seguintes entidades:

- Role
- User
- Branch
- Product
- StockRequest
- StockRequestItem
- Collection
- CollectionItem
- RequestStatusHistory

Defina os relacionamentos corretamente entre as tabelas.

## Regras de modelagem
- usar timestamps
- usar soft delete apenas se fizer sentido, senão usar campo ativo
- quantidade deve aceitar decimal, pois futuramente pode representar peso
- produtos devem ter unidade de medida
- requests e collections devem ter cabeçalho + itens

# Interface e UX

O sistema será usado em operação real. Portanto:

## Requisitos de usabilidade
- interface responsiva para tablet e celular
- telas simples, grandes e rápidas
- botões grandes
- foco em operação com toque
- campos preparados para scanner HID
- feedback visual claro ao escanear item
- mensagens de erro objetivas
- evitar telas poluídas

## Layout desejado
- um layout administrativo limpo
- um layout operacional mais direto
- navbar ou menu lateral dependendo da tela
- cards, tabelas simples e formulários claros
- usar Tailwind CSS com visual profissional e moderno, sem exageros

## Scanner HID
Considere que o leitor de código de barras funcionará como teclado, preenchendo um input e enviando Enter.

A interface deve:
- ter campo de leitura destacado
- capturar leitura rapidamente
- processar submissão sem fricção
- manter foco no input de leitura sempre que possível

# API interna e rotas auxiliares

Mesmo usando templates Jinja2, quero uma camada mínima de endpoints internos para operações assíncronas e futuras integrações.

Crie rotas ou endpoints para:
- buscar produto por código
- adicionar item à coleta
- atualizar quantidade de item
- criar requisição
- alterar status de requisição
- listar requisições com filtros

Esses endpoints podem ser usados com HTMX ou fetch simples.

# Funcionalidades mínimas do MVP

Implemente o esqueleto funcional do MVP com:

1. Login/logout
2. Controle de sessão
3. Dashboard inicial
4. Cadastro de usuários
5. Cadastro de filiais
6. Cadastro de produtos
7. Tela de nova requisição
8. Tela de listagem de requisições
9. Tela operacional do açougueiro
10. Tela de coletor
11. Alteração de status da requisição
12. Histórico de status
13. Controle básico de permissões

# Requisitos de qualidade

- código limpo
- nomes claros
- comentários apenas quando necessário
- sem duplicação desnecessária
- seguir boas práticas de Flask
- criar base pronta para crescer
- organizar imports
- usar classes ou funções de serviço quando necessário
- tratar erros com elegância
- validar formulários e dados de entrada
- criar mensagens flash adequadas
- proteger rotas com login e permissão
- preparar o projeto para manutenção futura

# Entregáveis esperados

Quero que você gere:

1. A estrutura de diretórios do projeto
2. Os arquivos iniciais principais
3. O código base do Flask com application factory
4. Configuração do PostgreSQL
5. Models com SQLAlchemy
6. Blueprints iniciais
7. Templates base
8. Exemplo de autenticação
9. Exemplo de CRUD administrativo
10. Exemplo funcional da tela de requisição
11. Exemplo funcional da tela de coletor
12. Seed inicial para perfis e usuário administrador
13. requirements.txt
14. .env.example
15. README.md com instruções de setup

# Forma de implementação

Implemente em etapas, com código completo e consistente, respeitando a arquitetura definida.

## Ordem desejada
1. Base do projeto e configuração
2. Extensions e application factory
3. Models
4. Autenticação
5. Permissões
6. Módulo administrativo
7. Módulo de requisições
8. Módulo de coletor
9. Templates e layout
10. Seeds e documentação

# Importante

- Não crie uma SPA
- Não use React
- Não complique desnecessariamente
- Não jogue toda a lógica no frontend
- Não faça código improvisado
- Não quebre a modularização
- Não use SQLite, o banco deve ser PostgreSQL
- Não simplifique demais a modelagem de requisições e itens
- Não ignore o controle de permissões

# Quero que você entregue

- o código inicial do projeto
- os arquivos principais completos
- a estrutura pronta para rodar
- as explicações curtas sobre cada parte importante
- sugestões objetivas de próximos passos ao final

Se precisar escolher entre simplicidade operacional e sofisticação técnica exagerada, priorize simplicidade operacional com arquitetura limpa.