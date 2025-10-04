from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from ...services.correlation_engine import CorrelationEngine
from ...services.mock_generator import MockDataGenerator
from ...services.swagger_parser import SwaggerParser

router = APIRouter(prefix="/openfinance", tags=["openfinance"])

# Global instances (will be initialized on startup)
_parser: SwaggerParser | None = None
_mock_generator: MockDataGenerator | None = None
_correlation_engine: CorrelationEngine | None = None
_contracts: dict[str, Any] = {}
_initialized = False


def _initialize(specs_dir: str = "openfinance_specs") -> None:
    """Initialize OpenFinance services"""
    global _parser, _mock_generator, _correlation_engine, _contracts, _initialized

    if _initialized:
        return

    _parser = SwaggerParser()
    _mock_generator = MockDataGenerator()
    _correlation_engine = CorrelationEngine(_parser.correlation_rules)

    root = Path(specs_dir)
    if root.exists():
        contracts = _parser.parse_directory(root)

        for contract in contracts:
            _contracts[contract.name] = contract

            # Generate and store mock data
            mocked_data = _mock_generator.generate_for_contract(contract, count=20)
            _correlation_engine.add_contract_data(contract.category or contract.name, mocked_data)

        print(f"Loaded {len(_contracts)} OpenFinance contracts")

    _initialized = True


@router.get("/contracts")
async def list_contracts(
    category: str | None = Query(default=None, description="Filter by category"),
    specs_dir: str = Query(default="openfinance_specs"),
) -> list[dict[str, Any]]:
    """List all available OpenFinance contracts"""
    _initialize(specs_dir)

    contracts = list(_contracts.values())

    if category:
        contracts = [c for c in contracts if c.category == category]

    return [
        {
            "name": c.name,
            "version": c.version,
            "category": c.category,
            "description": c.description,
            "endpoint_count": len(c.endpoints),
            "schema_count": len(c.schemas),
        }
        for c in contracts
    ]


@router.get("/contracts/{contract_name}")
async def get_contract_details(
    contract_name: str, specs_dir: str = Query(default="openfinance_specs")
) -> dict[str, Any]:
    """Get detailed information about a specific contract"""
    _initialize(specs_dir)

    contract = _contracts.get(contract_name)
    if not contract:
        raise HTTPException(status_code=404, detail=f"Contract not found: {contract_name}")

    return {
        "name": contract.name,
        "version": contract.version,
        "description": contract.description,
        "category": contract.category,
        "base_path": contract.base_path,
        "endpoints": [
            {
                "path": ep.path,
                "method": ep.method,
                "operation_id": ep.operation_id,
                "summary": ep.summary,
                "description": ep.description,
                "request_schema": ep.request_schema,
                "response_schema": ep.response_schema,
                "parameters": ep.parameters,
            }
            for ep in contract.endpoints
        ],
        "schemas": {
            name: {
                "type": schema.field_type.value,
                "description": schema.description,
                "required": schema.required,
                "properties": {
                    prop_name: {
                        "type": prop.field_type.value,
                        "description": prop.description,
                        "required": prop.required,
                        "validation": (
                            {
                                "pattern": prop.validation.pattern,
                                "min_length": prop.validation.min_length,
                                "max_length": prop.validation.max_length,
                                "format": prop.validation.format.value if prop.validation.format else None,
                            }
                            if prop.validation
                            else None
                        ),
                    }
                    for prop_name, prop in schema.properties.items()
                },
            }
            for name, schema in contract.schemas.items()
        },
    }


@router.post("/contracts/{contract_name}/mock")
async def generate_mock_data(
    contract_name: str,
    schema_name: str = Query(..., description="Schema name to generate data for"),
    count: int = Query(default=1, ge=1, le=100, description="Number of records to generate"),
    specs_dir: str = Query(default="openfinance_specs"),
) -> list[dict[str, Any]]:
    """Generate mock data for a contract schema"""
    _initialize(specs_dir)

    if not _mock_generator:
        raise HTTPException(status_code=500, detail="Mock generator not initialized")

    contract = _contracts.get(contract_name)
    if not contract:
        raise HTTPException(status_code=404, detail=f"Contract not found: {contract_name}")

    schema = contract.schemas.get(schema_name)
    if not schema:
        raise HTTPException(status_code=404, detail=f"Schema not found: {schema_name}")

    mocked_data = _mock_generator.generate_for_contract(contract, count=count)

    return [
        {
            "schema_name": data.schema_name,
            "data": data.data,
            "created_at": data.created_at.isoformat(),
            "correlation_ids": data.correlation_ids,
        }
        for data in mocked_data
        if data.schema_name == schema_name
    ]


@router.get("/correlations")
async def get_correlation_graph(specs_dir: str = Query(default="openfinance_specs")) -> dict[str, Any]:
    """Get the correlation graph showing relationships between contracts"""
    _initialize(specs_dir)

    if not _correlation_engine:
        raise HTTPException(status_code=500, detail="Correlation engine not initialized")

    graph = _correlation_engine.build_correlation_graph()

    return {
        "graph": graph,
        "rules": [
            {
                "source_contract": rule.source_contract,
                "target_contract": rule.target_contract,
                "source_field": rule.source_field,
                "target_field": rule.target_field,
                "relationship": rule.relationship,
            }
            for rule in _correlation_engine.rules
        ],
    }


@router.get("/correlations/{contract_name}")
async def get_contract_correlations(
    contract_name: str, specs_dir: str = Query(default="openfinance_specs")
) -> dict[str, Any]:
    """Get correlation rules for a specific contract"""
    _initialize(specs_dir)

    if not _correlation_engine:
        raise HTTPException(status_code=500, detail="Correlation engine not initialized")

    rules = _correlation_engine.get_correlation_rules_for_contract(contract_name)

    return {
        "contract": contract_name,
        "rules": [
            {
                "source_contract": rule.source_contract,
                "target_contract": rule.target_contract,
                "source_field": rule.source_field,
                "target_field": rule.target_field,
                "relationship": rule.relationship,
            }
            for rule in rules
        ],
    }


@router.get("/data/correlated")
async def get_correlated_data(
    primary_contract: str = Query(..., description="Primary contract name"),
    primary_id_field: str = Query(..., description="ID field name in primary contract"),
    primary_id_value: str = Query(..., description="ID value to search for"),
    specs_dir: str = Query(default="openfinance_specs"),
) -> dict[str, Any]:
    """Get data correlated across multiple contracts"""
    _initialize(specs_dir)

    if not _correlation_engine:
        raise HTTPException(status_code=500, detail="Correlation engine not initialized")

    correlated = _correlation_engine.correlate_data(primary_contract, primary_id_field, primary_id_value)

    if not correlated:
        raise HTTPException(status_code=404, detail="No correlated data found")

    return {
        "primary_data": {
            "contract": correlated.primary_data.contract_name,
            "schema": correlated.primary_data.schema_name,
            "data": correlated.primary_data.data,
        },
        "related_data": {
            contract_name: [
                {"schema": data.schema_name, "data": data.data} for data in data_list
            ]
            for contract_name, data_list in correlated.related_data.items()
        },
    }


@router.get("/query/{contract_name}/{endpoint_path:path}")
async def query_endpoint(
    contract_name: str,
    endpoint_path: str,
    method: str = Query(default="GET", description="HTTP method"),
    specs_dir: str = Query(default="openfinance_specs"),
) -> dict[str, Any]:
    """Query a contract endpoint with mocked response"""
    _initialize(specs_dir)

    if not _mock_generator:
        raise HTTPException(status_code=500, detail="Mock generator not initialized")

    contract = _contracts.get(contract_name)
    if not contract:
        raise HTTPException(status_code=404, detail=f"Contract not found: {contract_name}")

    # Find endpoint
    endpoint = None
    for ep in contract.endpoints:
        if ep.path == f"/{endpoint_path}" and ep.method == method.upper():
            endpoint = ep
            break

    if not endpoint:
        raise HTTPException(
            status_code=404, detail=f"Endpoint not found: {method} /{endpoint_path}"
        )

    # Generate mock response
    response_data = {}
    if endpoint.response_schema:
        schema = contract.schemas.get(endpoint.response_schema)
        if schema:
            response_data = _mock_generator._generate_from_schema(
                schema, endpoint.response_schema, contract.category or ""
            )

    return {
        "endpoint": {
            "path": endpoint.path,
            "method": endpoint.method,
            "operation_id": endpoint.operation_id,
            "summary": endpoint.summary,
        },
        "response": response_data,
    }


@router.get("/categories")
async def list_categories(specs_dir: str = Query(default="openfinance_specs")) -> list[str]:
    """List all available contract categories"""
    _initialize(specs_dir)

    categories = set()
    for contract in _contracts.values():
        if contract.category:
            categories.add(contract.category)

    return sorted(list(categories))
