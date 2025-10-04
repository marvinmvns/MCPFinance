# OpenFinance MCP - Examples

Este diretório contém exemplos de uso do sistema OpenFinance MCP.

## Executar Exemplos

### 1. Uso Programático

```bash
# Certifique-se de ter baixado os specs
make fetch-openfinance

# Execute o exemplo
python examples/openfinance_usage.py
```

Este exemplo demonstra:
- Parsing de contratos OpenAPI/Swagger
- Geração de dados mockados
- Sistema de correlação entre contratos
- Geração de dados brasileiros (CPF, CNPJ)

### 2. Uso via REST API

```bash
# Inicie o servidor
make run

# Em outro terminal, teste os endpoints:

# Listar contratos
curl http://localhost:8000/v1/openfinance/contracts

# Detalhes de um contrato
curl http://localhost:8000/v1/openfinance/contracts/AccountsAPI

# Gerar mock data
curl -X POST "http://localhost:8000/v1/openfinance/contracts/AccountsAPI/mock?schema_name=Account&count=5"

# Grafo de correlações
curl http://localhost:8000/v1/openfinance/correlations

# Dados correlacionados
curl "http://localhost:8000/v1/openfinance/data/correlated?primary_contract=consents&primary_id_field=consentId&primary_id_value=123"
```

### 3. Uso via MCP Server

```bash
# Inicie o MCP server
make run-mcp

# O servidor MCP está pronto para conexões stdio
# Pode ser usado com Claude Code ou outras ferramentas MCP
```

### 4. Uso via gRPC

```bash
# Compile o protobuf (primeira vez)
make compile-proto

# Inicie o servidor gRPC
make run-grpc

# Use um cliente gRPC para interagir
# Exemplo com grpcurl:
grpcurl -plaintext localhost:50051 list
grpcurl -plaintext localhost:50051 openfinance.OpenFinanceService/ListContracts
```

## Saída Esperada

### openfinance_usage.py

```
================================================================================
OpenFinance MCP - Example Usage
================================================================================

1. Initializing components...

2. Parsing OpenFinance contracts...
✅ Loaded 45 contracts

3. Available contracts:
   1. Accounts API (v2.0.0) - accounts
      Endpoints: 12, Schemas: 18
   2. Consents API (v1.0.0) - consents
      Endpoints: 8, Schemas: 10
   ... and 43 more

4. Generating mock data...
   Using contract: Accounts API
   ✅ Generated 15 mock records

   Example mock data for Account:
   {
      "accountId": "550e8400-e29b-41d4-a716-446655440000",
      "accountType": "CONTA_CORRENTE",
      "balance": 12345.67,
      ...
   }

5. Building correlation store...
   ✅ Added 15 records for accounts
   ✅ Added 10 records for consents
   ...

6. Correlation graph:
   consents → resources, accounts
   accounts → transactions
   ...

7. Correlation rules:
   consents.consentId → resources.consentId (one-to-many)
   accounts.accountId → transactions.accountId (one-to-many)
   ...

8. Finding correlated data...
   Primary: consents
   Searching by consentId = urn:bancoex:123
   ✅ Found correlated data:
      Primary: Consent
      → accounts: 3 records
      → transactions: 12 records

9. Brazilian data generation:
   CPF:   12345678901
   CNPJ:  12345678000195
   Phone: +5511987654321

================================================================================
Summary:
  - Contracts loaded: 45
  - Correlation rules: 5
  - Data stores: 15
================================================================================

✅ Example completed successfully!
```

## Estrutura do Sistema

```
src/app/
├── domain/openfinance.py           # Entidades
├── services/
│   ├── swagger_parser.py          # Parser
│   ├── mock_generator.py          # Gerador
│   ├── correlation_engine.py      # Correlação
│   └── dictionary_loader.py       # Dicionário
├── api/routes/openfinance.py      # REST
├── mcp/openfinance_server.py      # MCP
└── grpc_server/openfinance_grpc.py # gRPC
```

## Mais Informações

Veja [OPENFINANCE_MCP.md](../OPENFINANCE_MCP.md) para documentação completa.
