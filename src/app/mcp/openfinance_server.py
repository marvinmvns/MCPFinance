from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.types import Resource, Tool

from ..domain.openfinance import OpenFinanceContract
from ..services.correlation_engine import CorrelationEngine
from ..services.mock_generator import MockDataGenerator
from ..services.swagger_parser import SwaggerParser


class OpenFinanceMCPServer:
    """MCP Server for OpenFinance contracts with mock data generation"""

    def __init__(self, specs_directory: str = "openfinance_specs") -> None:
        self.specs_dir = Path(specs_directory)
        self.server = Server("openfinance-mcp")
        self.parser = SwaggerParser()
        self.mock_generator = MockDataGenerator()
        self.contracts: dict[str, OpenFinanceContract] = {}
        self.correlation_engine = CorrelationEngine(self.parser.correlation_rules)

        self._setup_tools()
        self._setup_resources()

    def _setup_tools(self) -> None:
        """Setup MCP tools for OpenFinance operations"""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            return [
                Tool(
                    name="list_contracts",
                    description="List all available OpenFinance contracts with their endpoints",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "description": "Filter by category (e.g., accounts, consents)",
                            }
                        },
                    },
                ),
                Tool(
                    name="get_contract_details",
                    description="Get detailed information about a specific contract including schemas",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "contract_name": {
                                "type": "string",
                                "description": "Name of the contract",
                            }
                        },
                        "required": ["contract_name"],
                    },
                ),
                Tool(
                    name="generate_mock_data",
                    description="Generate mock data for a contract schema",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "contract_name": {"type": "string"},
                            "schema_name": {"type": "string"},
                            "count": {"type": "integer", "default": 1},
                        },
                        "required": ["contract_name", "schema_name"],
                    },
                ),
                Tool(
                    name="get_correlated_data",
                    description="Get data correlated across multiple contracts",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "primary_contract": {"type": "string"},
                            "primary_id_field": {"type": "string"},
                            "primary_id_value": {"type": "string"},
                        },
                        "required": ["primary_contract", "primary_id_field", "primary_id_value"],
                    },
                ),
                Tool(
                    name="get_correlation_graph",
                    description="Get the correlation graph showing relationships between contracts",
                    inputSchema={"type": "object", "properties": {}},
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[Any]:
            if name == "list_contracts":
                return await self._list_contracts(arguments.get("category"))

            if name == "get_contract_details":
                return await self._get_contract_details(arguments["contract_name"])

            if name == "generate_mock_data":
                return await self._generate_mock_data(
                    arguments["contract_name"],
                    arguments["schema_name"],
                    arguments.get("count", 1),
                )

            if name == "get_correlated_data":
                return await self._get_correlated_data(
                    arguments["primary_contract"],
                    arguments["primary_id_field"],
                    arguments["primary_id_value"],
                )

            if name == "get_correlation_graph":
                return await self._get_correlation_graph()

            return [{"error": f"Unknown tool: {name}"}]

    def _setup_resources(self) -> None:
        """Setup MCP resources for OpenFinance contracts"""

        @self.server.list_resources()
        async def list_resources() -> list[Resource]:
            resources: list[Resource] = []

            for contract in self.contracts.values():
                resources.append(
                    Resource(
                        uri=f"openfinance://contracts/{contract.name}",
                        name=f"{contract.name} ({contract.version})",
                        description=contract.description or "OpenFinance API contract",
                        mimeType="application/json",
                    )
                )

            return resources

        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            if uri.startswith("openfinance://contracts/"):
                contract_name = uri.replace("openfinance://contracts/", "")
                contract = self.contracts.get(contract_name)

                if contract:
                    return json.dumps(
                        {
                            "name": contract.name,
                            "version": contract.version,
                            "description": contract.description,
                            "category": contract.category,
                            "endpoints": [
                                {
                                    "path": ep.path,
                                    "method": ep.method,
                                    "summary": ep.summary,
                                    "operation_id": ep.operation_id,
                                }
                                for ep in contract.endpoints
                            ],
                            "schemas": list(contract.schemas.keys()),
                        },
                        indent=2,
                    )

            return json.dumps({"error": "Resource not found"})

    async def load_contracts(self) -> None:
        """Load all contracts from specs directory"""
        if not self.specs_dir.exists():
            print(f"Specs directory not found: {self.specs_dir}")
            return

        contracts = self.parser.parse_directory(self.specs_dir)

        for contract in contracts:
            self.contracts[contract.name] = contract

            # Generate mock data for each contract
            mocked_data = self.mock_generator.generate_for_contract(contract, count=5)
            self.correlation_engine.add_contract_data(contract.category or contract.name, mocked_data)

        print(f"Loaded {len(self.contracts)} contracts")

    async def _list_contracts(self, category: str | None = None) -> list[dict[str, Any]]:
        """List all contracts, optionally filtered by category"""
        contracts = list(self.contracts.values())

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

    async def _get_contract_details(self, contract_name: str) -> list[dict[str, Any]]:
        """Get detailed contract information"""
        contract = self.contracts.get(contract_name)

        if not contract:
            return [{"error": f"Contract not found: {contract_name}"}]

        return [
            {
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
                    }
                    for ep in contract.endpoints
                ],
                "schemas": {
                    name: {
                        "type": schema.field_type.value,
                        "description": schema.description,
                        "properties": list(schema.properties.keys()),
                    }
                    for name, schema in contract.schemas.items()
                },
            }
        ]

    async def _generate_mock_data(
        self, contract_name: str, schema_name: str, count: int
    ) -> list[dict[str, Any]]:
        """Generate mock data for a schema"""
        contract = self.contracts.get(contract_name)

        if not contract:
            return [{"error": f"Contract not found: {contract_name}"}]

        schema = contract.schemas.get(schema_name)
        if not schema:
            return [{"error": f"Schema not found: {schema_name}"}]

        mocked_data = self.mock_generator.generate_for_contract(contract, count=count)

        return [
            {
                "schema_name": data.schema_name,
                "data": data.data,
                "created_at": data.created_at.isoformat(),
            }
            for data in mocked_data
            if data.schema_name == schema_name
        ]

    async def _get_correlated_data(
        self, primary_contract: str, primary_id_field: str, primary_id_value: str
    ) -> list[dict[str, Any]]:
        """Get correlated data across contracts"""
        correlated = self.correlation_engine.correlate_data(
            primary_contract, primary_id_field, primary_id_value
        )

        if not correlated:
            return [{"error": "No correlated data found"}]

        return [
            {
                "primary_data": {
                    "contract": correlated.primary_data.contract_name,
                    "schema": correlated.primary_data.schema_name,
                    "data": correlated.primary_data.data,
                },
                "related_data": {
                    contract_name: [
                        {
                            "schema": data.schema_name,
                            "data": data.data,
                        }
                        for data in data_list
                    ]
                    for contract_name, data_list in correlated.related_data.items()
                },
            }
        ]

    async def _get_correlation_graph(self) -> list[dict[str, Any]]:
        """Get correlation graph"""
        graph = self.correlation_engine.build_correlation_graph()

        return [
            {
                "correlation_graph": graph,
                "rules": [
                    {
                        "source": rule.source_contract,
                        "target": rule.target_contract,
                        "source_field": rule.source_field,
                        "target_field": rule.target_field,
                        "relationship": rule.relationship,
                    }
                    for rule in self.correlation_engine.rules
                ],
            }
        ]

    def get_server(self) -> Server:
        """Get the MCP server instance"""
        return self.server
