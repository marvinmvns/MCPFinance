# OpenFinance MCP Server - Documentação Completa

## Visão Geral

Este é um servidor MCP (Model Context Protocol) completo para trabalhar com contratos OpenFinance Brasil. O sistema oferece:

- **Parsing avançado** de especificações OpenAPI/Swagger com extração de validações regex
- **Geração de dados mockados** usando Faker com validações brasileiras (CPF, CNPJ)
- **Sistema de correlação** para relacionar dados entre diferentes APIs
- **Exposição via REST API** com FastAPI
- **Suporte gRPC** para comunicação eficiente
- **Servidor MCP** para integração com ferramentas de IA

## Arquitetura

### Estrutura de Camadas

```
src/app/
├── domain/              # Entidades e Value Objects
│   └── openfinance.py  # Modelos do domínio OpenFinance
├── services/            # Lógica de negócio
│   ├── swagger_parser.py        # Parser de OpenAPI/Swagger
│   ├── mock_generator.py        # Gerador de dados mockados
│   ├── correlation_engine.py    # Engine de correlação
│   └── dictionary_loader.py     # Carregador de dicionários
├── api/routes/          # Endpoints REST
│   └── openfinance.py   # Rotas OpenFinance
├── mcp/                 # Servidor MCP
│   └── openfinance_server.py
└── grpc_server/         # Servidor gRPC
    └── openfinance_grpc.py
```

### Componentes Principais

#### 1. Swagger Parser (`swagger_parser.py`)
- Parse de arquivos OpenAPI (JSON/YAML)
- Extração de schemas com validações (pattern, minLength, maxLength, etc.)
- Identificação de endpoints e operações
- Categorização automática de contratos

#### 2. Mock Generator (`mock_generator.py`)
- Geração de dados respeitando validações regex
- Suporte para formatos brasileiros (CPF, CNPJ, telefone)
- Integração com Faker para dados realistas
- Geração baseada em tipos e formatos OpenAPI

#### 3. Correlation Engine (`correlation_engine.py`)
- Sistema de correlação entre contratos
- Suporte para relacionamentos (one-to-one, one-to-many)
- Navegação em grafo de correlações
- Enriquecimento de dados com referências cruzadas

#### 4. Dictionary Loader (`dictionary_loader.py`)
- Carregamento de dicionários OpenFinance
- Extração de exemplos e enums
- Enriquecimento de dados com valores do dicionário

## Configuração e Instalação

### 1. Instalar Dependências

```bash
# Criar ambiente virtual e instalar dependências
make venv

# Ou manualmente
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install poetry
poetry install
```

### 2. Baixar Contratos OpenFinance

```bash
# Baixar specs do repositório oficial
make fetch-openfinance

# Isso clonará https://github.com/OpenBanking-Brasil/openapi
# para o diretório openfinance_specs/
```

### 3. Estrutura de Diretórios Esperada

```
openfinance_specs/
├── swagger-apis/        # Contratos Swagger/OpenAPI
│   ├── consents/
│   ├── accounts/
│   ├── credit-cards/
│   └── ...
└── dictionary/          # Dicionários de dados
    ├── accounts.json
    ├── consents.json
    └── ...
```

## Uso

### REST API

#### Iniciar Servidor REST

```bash
make run
# Ou
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Endpoints Disponíveis

##### Listar Contratos
```bash
GET /v1/openfinance/contracts
GET /v1/openfinance/contracts?category=accounts

# Resposta:
[
  {
    "name": "Accounts API",
    "version": "2.0.0",
    "category": "accounts",
    "description": "...",
    "endpoint_count": 15,
    "schema_count": 20
  }
]
```

##### Detalhes de um Contrato
```bash
GET /v1/openfinance/contracts/{contract_name}

# Resposta:
{
  "name": "Accounts API",
  "version": "2.0.0",
  "endpoints": [...],
  "schemas": {
    "Account": {
      "type": "object",
      "properties": {
        "accountId": {
          "type": "string",
          "validation": {
            "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-...",
            "format": "uuid"
          }
        }
      }
    }
  }
}
```

##### Gerar Dados Mockados
```bash
POST /v1/openfinance/contracts/{contract_name}/mock?schema_name=Account&count=10

# Resposta:
[
  {
    "schema_name": "Account",
    "data": {
      "accountId": "550e8400-e29b-41d4-a716-446655440000",
      "accountType": "CONTA_CORRENTE",
      "balance": 1234.56,
      ...
    },
    "created_at": "2024-03-15T10:30:00Z",
    "correlation_ids": {
      "customerId": "abc-123"
    }
  }
]
```

##### Grafo de Correlação
```bash
GET /v1/openfinance/correlations

# Resposta:
{
  "graph": {
    "consents": ["resources", "accounts"],
    "accounts": ["transactions"],
    "credit-cards-accounts": ["transactions"]
  },
  "rules": [
    {
      "source_contract": "consents",
      "target_contract": "accounts",
      "source_field": "consentId",
      "target_field": "consentId",
      "relationship": "one-to-many"
    }
  ]
}
```

##### Dados Correlacionados
```bash
GET /v1/openfinance/data/correlated?primary_contract=consents&primary_id_field=consentId&primary_id_value=123

# Resposta:
{
  "primary_data": {
    "contract": "Consents API",
    "schema": "Consent",
    "data": {...}
  },
  "related_data": {
    "accounts": [
      {"schema": "Account", "data": {...}},
      {"schema": "Account", "data": {...}}
    ],
    "transactions": [...]
  }
}
```

##### Query de Endpoint
```bash
GET /v1/openfinance/query/{contract_name}/{endpoint_path}?method=GET

# Resposta:
{
  "endpoint": {
    "path": "/accounts",
    "method": "GET",
    "operation_id": "getAccounts",
    "summary": "List accounts"
  },
  "response": {
    "data": [...],
    "meta": {...}
  }
}
```

##### Categorias
```bash
GET /v1/openfinance/categories

# Resposta:
[
  "accounts",
  "consents",
  "credit-cards-accounts",
  "customers",
  "loans",
  ...
]
```

### MCP Server

#### Iniciar MCP Server

```bash
python run_mcp_server.py --specs-dir openfinance_specs
```

#### Ferramentas MCP Disponíveis

1. **list_contracts**
   - Lista todos os contratos disponíveis
   - Parâmetros: `category` (opcional)

2. **get_contract_details**
   - Obtém detalhes de um contrato específico
   - Parâmetros: `contract_name`

3. **generate_mock_data**
   - Gera dados mockados para um schema
   - Parâmetros: `contract_name`, `schema_name`, `count`

4. **get_correlated_data**
   - Obtém dados correlacionados entre contratos
   - Parâmetros: `primary_contract`, `primary_id_field`, `primary_id_value`

5. **get_correlation_graph**
   - Retorna o grafo de correlações

#### Recursos MCP

- `openfinance://contracts/{contract_name}` - Acesso direto a contratos

### gRPC Server

#### Compilar Protobuf

```bash
python -m grpc_tools.protoc \
  -I protos \
  --python_out=src/app/grpc_server \
  --grpc_python_out=src/app/grpc_server \
  protos/openfinance.proto
```

#### Iniciar Servidor gRPC

```bash
python -c "from src.app.grpc_server import serve_grpc; serve_grpc(port=50051)"
```

#### Serviços gRPC Disponíveis

- `ListContracts` - Lista contratos
- `GetContractDetails` - Detalhes de contrato
- `GenerateMockData` - Gera dados mockados
- `GetCorrelatedData` - Dados correlacionados
- `GetCorrelationGraph` - Grafo de correlações
- `QueryEndpoint` - Query de endpoint

## Sistema de Correlação

### Regras de Correlação Predefinidas

```python
# Consent -> Resources
consentId (consents) -> consentId (resources)

# Resources -> Accounts
accountId (resources) -> accountId (accounts)

# Accounts -> Transactions
accountId (accounts) -> accountId (transactions)

# Customer -> Accounts
customerId (customers) -> customerId (accounts)

# Credit Cards -> Transactions
creditCardAccountId (credit-cards) -> creditCardAccountId (transactions)
```

### Exemplo de Fluxo de Correlação

```
1. Consent criado com consentId: "urn:bancoex:123"
2. Resources associados ao consentId: "urn:bancoex:123"
3. Accounts retornados com accountId: "acc-456"
4. Transactions buscadas por accountId: "acc-456"
```

## Geração de Dados Mockados

### Validações Suportadas

- **Regex Pattern**: Geração compatível com padrões regex
- **Min/Max Length**: Strings com tamanho controlado
- **Min/Max Value**: Números dentro de ranges
- **Enum**: Valores de lista predefinida
- **Format**: date, date-time, email, uuid, uri

### Dados Brasileiros

- **CPF**: Geração com dígitos verificadores válidos
- **CNPJ**: Geração com dígitos verificadores válidos
- **Telefone**: Formato +55 (XX) XXXXX-XXXX
- **CEP**: Formato XXXXX-XXX

### Exemplo de Schema com Validação

```yaml
Account:
  type: object
  properties:
    accountId:
      type: string
      format: uuid
      pattern: "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    accountNumber:
      type: string
      pattern: "^[0-9]{6,12}$"
      minLength: 6
      maxLength: 12
    balance:
      type: number
      minimum: 0
      maximum: 999999999.99
    status:
      type: string
      enum: ["ACTIVE", "INACTIVE", "BLOCKED"]
```

## Testes

### Executar Testes

```bash
# Todos os testes
make test

# Com cobertura
make cov

# Teste específico
pytest tests/test_openfinance_system.py -v
```

### Suítes de Teste

- `TestSwaggerParser`: Testes do parser de Swagger
- `TestMockDataGenerator`: Testes de geração de dados
- `TestCorrelationEngine`: Testes de correlação
- `TestOpenFinanceEndpoints`: Testes de endpoints REST

## Desenvolvimento

### Adicionar Novo Contrato

1. Adicione o arquivo Swagger/OpenAPI em `openfinance_specs/swagger-apis/`
2. O parser carregará automaticamente
3. Categorize corretamente (veja `_extract_category` em `swagger_parser.py`)

### Adicionar Nova Correlação

Edite `swagger_parser.py`:

```python
def _load_correlation_rules(self) -> list[CorrelationRule]:
    return [
        # ... regras existentes ...
        CorrelationRule(
            source_contract="novo_contrato",
            target_contract="alvo",
            source_field="campoOrigem",
            target_field="campoDestino",
            relationship="one-to-many"
        )
    ]
```

### Estender Geração de Dados

Edite `mock_generator.py`:

```python
def _generate_typed_value(self, field: SchemaField, field_name: str, category: str, schema_name: str) -> Any:
    # Adicione padrões customizados
    if "novo_campo" in field_name.lower():
        return self._gerar_valor_customizado()
    # ...
```

## Comandos Úteis

```bash
# Desenvolvimento
make venv          # Criar ambiente virtual
make run           # Executar servidor REST
make test          # Executar testes
make lint          # Linting
make fmt           # Formatação

# OpenFinance
make fetch-openfinance  # Baixar specs

# Docker
make docker-build  # Build imagem
make docker-up     # Subir com compose
```

## Troubleshooting

### Erro: "Specs directory not found"
```bash
# Certifique-se de baixar os specs
make fetch-openfinance
```

### Erro: "Contract not found"
```bash
# Verifique se o diretório está correto
ls openfinance_specs/swagger-apis/

# Liste contratos disponíveis
curl http://localhost:8000/v1/openfinance/contracts
```

### Erro de validação regex
- Verifique o padrão regex no schema
- Revise `_generate_from_regex` em `mock_generator.py`

## Roadmap

- [ ] Persistência de dados mockados em SQLite
- [ ] Cache de contratos parseados
- [ ] Interface web para visualização
- [ ] Export de dados para CSV/Excel
- [ ] Validação de dados mockados contra schemas
- [ ] Suporte para webhooks simulados
- [ ] Dashboard de métricas
