# clean-api

Serviço FastAPI com arquitetura Clean/Hexagonal, tipagem forte, segurança com JWT, observabilidade (logs estruturados, métricas Prometheus, tracing OpenTelemetry), repositórios assíncronos (SQLAlchemy 2.0 + Alembic), qualidade (ruff, black, mypy, pytest, bandit) e CI.

## Requisitos
- Python 3.12+
- Poetry (ou pip)
- Docker e Docker Compose (opcional)

## Execução local
1. Crie o ambiente e instale dependências:
   - make venv
2. Configure variáveis (.env):
   - copie `.env.example` para `.env` e ajuste se necessário
3. Rode a aplicação:
   - make run

Endpoints principais:
- `GET /v1/health` liveness
- `GET /v1/ready` readiness (verifica DB)
- `GET /v1/metrics` métricas Prometheus
- `GET /openapi.json` contrato OpenAPI
- `GET /v1/openfinance/contracts` sumariza contratos OpenFinance a partir da pasta `openfinance_specs`

## Segurança
- JWT HS256 com escopos. Operações de escrita exigem escopo `users:write`.
- Cabeçalho `Authorization: Bearer <token>`.

## Banco de Dados
- SQLAlchemy 2.0 assíncrono. Modelo `users(id, email, full_name, created_at)`
- Alembic já possui migração inicial `create_users`.

### Migração Alembic
```
alembic -c alembic.ini upgrade head
```
Para criar novas migrações:
```
alembic -c alembic.ini revision -m "<mensagem>"
```

## Docker
```
make docker-build
docker run -p 8000:8000 clean-api:latest
```
Ou usando Compose (inclui Postgres e Jaeger):
```
make docker-up
```

## Qualidade e Testes
- Lint: `make lint`
- Format: `make fmt`
- Testes: `make test`
- Cobertura: `make cov`

## Variáveis de ambiente (.env)
Veja `.env.example`. Principais:
- `DB_DSN` (padrão sqlite aiosqlite local)
- `JWT_SECRET`, `JWT_AUDIENCE`, `JWT_ISSUER`
- `ENABLE_TRACING`, `OTEL_EXPORTER_OTLP_ENDPOINT`
- `CORS_ORIGINS`

## Observabilidade
- Logs estruturados via structlog, com `X-Correlation-ID`
- Tracing OpenTelemetry opcional (ativado por `ENABLE_TRACING=true`)
- Métricas Prometheus em `/v1/metrics`

## Notas de Arquitetura
- Camadas em `src/app/`: domain, services, repositories, api, core
- Repositório SQL (`user_repo_sql.py`) e em memória (`user_repo_memory.py`)
- Middleware de idempotência (POST com `Idempotency-Key`) e correlation-id

## OpenFinance MCP - Sistema Completo ✅

Sistema completo de MCP (Model Context Protocol) para contratos OpenFinance Brasil com:

### Funcionalidades Implementadas

- ✅ **Parser Avançado de Swagger/OpenAPI**
  - Extração completa de schemas com validações regex
  - Suporte para JSON e YAML
  - Identificação automática de categorias

- ✅ **Gerador de Dados Mockados Inteligente**
  - Validações brasileiras (CPF, CNPJ, telefone)
  - Respeita patterns regex dos schemas
  - Geração baseada em tipos e formatos OpenAPI
  - Integração com Faker para dados realistas

- ✅ **Sistema de Correlação entre Contratos**
  - Relacionamentos configuráveis (one-to-one, one-to-many)
  - Grafo de correlações entre APIs
  - Navegação automática em dados relacionados
  - Regras predefinidas: consents → accounts → transactions

- ✅ **REST API Completa**
  - 8 endpoints para interação com contratos
  - Geração de mock data sob demanda
  - Consultas correlacionadas entre APIs
  - Query de endpoints com resposta mockada

- ✅ **Servidor MCP**
  - 5 ferramentas MCP para IA
  - Recursos navegáveis via URI
  - Integração stdio para Claude Code

- ✅ **Suporte gRPC**
  - Schema .proto completo
  - Servidor gRPC implementado
  - 6 serviços disponíveis

- ✅ **Testes Automatizados**
  - Suíte completa de testes
  - Cobertura de parser, mock generator e correlação

### Quick Start

```bash
# 1. Baixar contratos OpenFinance
make fetch-openfinance

# 2. Executar servidor REST
make run

# 3. Testar endpoints
curl http://localhost:8000/v1/openfinance/contracts
curl http://localhost:8000/v1/openfinance/correlations

# 4. Executar MCP server (opcional)
make run-mcp

# 5. Executar gRPC server (opcional)
make run-grpc
```

### Endpoints REST Disponíveis

- `GET /v1/openfinance/contracts` - Lista contratos
- `GET /v1/openfinance/contracts/{name}` - Detalhes de contrato
- `POST /v1/openfinance/contracts/{name}/mock` - Gera dados mockados
- `GET /v1/openfinance/correlations` - Grafo de correlações
- `GET /v1/openfinance/correlations/{contract}` - Correlações de um contrato
- `GET /v1/openfinance/data/correlated` - Dados correlacionados
- `GET /v1/openfinance/query/{contract}/{path}` - Query de endpoint
- `GET /v1/openfinance/categories` - Lista categorias

### Arquitetura

```
src/app/
├── domain/openfinance.py           # Entidades e Value Objects
├── services/
│   ├── swagger_parser.py          # Parser OpenAPI/Swagger
│   ├── mock_generator.py          # Gerador de dados mockados
│   ├── correlation_engine.py      # Engine de correlação
│   └── dictionary_loader.py       # Carregador de dicionários
├── api/routes/openfinance.py      # Endpoints REST
├── mcp/openfinance_server.py      # Servidor MCP
└── grpc_server/openfinance_grpc.py # Servidor gRPC

protos/openfinance.proto            # Schema gRPC
run_mcp_server.py                   # Script MCP standalone
```

### Documentação Completa

Veja [OPENFINANCE_MCP.md](OPENFINANCE_MCP.md) para documentação detalhada incluindo:
- Guia completo de uso
- Exemplos de API
- Sistema de correlação
- Desenvolvimento e extensão
