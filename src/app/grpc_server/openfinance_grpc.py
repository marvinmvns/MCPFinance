from __future__ import annotations

import asyncio
import json
from concurrent import futures
from pathlib import Path
from typing import Any

import grpc

# Import generated gRPC code (will be generated from .proto)
# from protos import openfinance_pb2, openfinance_pb2_grpc

from ..services.correlation_engine import CorrelationEngine
from ..services.mock_generator import MockDataGenerator
from ..services.swagger_parser import SwaggerParser


class OpenFinanceGRPCService:
    """gRPC service implementation for OpenFinance"""

    def __init__(self, specs_directory: str = "openfinance_specs") -> None:
        self.specs_dir = Path(specs_directory)
        self.parser = SwaggerParser()
        self.mock_generator = MockDataGenerator()
        self.contracts: dict[str, Any] = {}
        self.correlation_engine = CorrelationEngine(self.parser.correlation_rules)
        self.mocked_data_store: dict[str, list[Any]] = {}

    async def load_contracts(self) -> None:
        """Load all contracts from specs directory"""
        if not self.specs_dir.exists():
            print(f"Specs directory not found: {self.specs_dir}")
            return

        contracts = self.parser.parse_directory(self.specs_dir)

        for contract in contracts:
            self.contracts[contract.name] = contract

            # Generate mock data for each contract
            mocked_data = self.mock_generator.generate_for_contract(contract, count=10)
            self.correlation_engine.add_contract_data(contract.category or contract.name, mocked_data)

            # Store for quick access
            self.mocked_data_store[contract.name] = mocked_data

        print(f"Loaded {len(self.contracts)} contracts for gRPC service")

    def ListContracts(self, request: Any, context: Any) -> Any:
        """List all contracts"""
        # Implementation will use generated protobuf classes
        contracts = list(self.contracts.values())

        if hasattr(request, "category") and request.category:
            contracts = [c for c in contracts if c.category == request.category]

        # Return protobuf response (placeholder)
        return {"contracts": contracts}

    def GetContractDetails(self, request: Any, context: Any) -> Any:
        """Get contract details"""
        contract = self.contracts.get(request.contract_name)

        if not contract:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Contract not found: {request.contract_name}")
            return {}

        return contract

    def GenerateMockData(self, request: Any, context: Any) -> Any:
        """Generate mock data"""
        contract = self.contracts.get(request.contract_name)

        if not contract:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Contract not found: {request.contract_name}")
            return {}

        mocked_data = self.mock_generator.generate_for_contract(contract, count=request.count or 1)

        return {"data": mocked_data}

    def GetCorrelatedData(self, request: Any, context: Any) -> Any:
        """Get correlated data"""
        correlated = self.correlation_engine.correlate_data(
            request.primary_contract, request.primary_id_field, request.primary_id_value
        )

        if not correlated:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("No correlated data found")
            return {}

        return correlated

    def GetCorrelationGraph(self, request: Any, context: Any) -> Any:
        """Get correlation graph"""
        graph = self.correlation_engine.build_correlation_graph()
        rules = self.correlation_engine.rules

        return {"graph": graph, "rules": rules}

    def QueryEndpoint(self, request: Any, context: Any) -> Any:
        """Query an endpoint with mock data"""
        contract = self.contracts.get(request.contract_name)

        if not contract:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Contract not found: {request.contract_name}")
            return {}

        # Find endpoint
        endpoint = None
        for ep in contract.endpoints:
            if ep.path == request.endpoint_path and ep.method == request.method:
                endpoint = ep
                break

        if not endpoint:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Endpoint not found: {request.method} {request.endpoint_path}")
            return {}

        # Generate mock response
        if endpoint.response_schema:
            schema = contract.schemas.get(endpoint.response_schema)
            if schema:
                mock_data = self.mock_generator._generate_from_schema(
                    schema, endpoint.response_schema, contract.category or ""
                )
                return {
                    "status_code": 200,
                    "response_json": json.dumps(mock_data),
                    "headers": {"Content-Type": "application/json"},
                }

        return {"status_code": 200, "response_json": "{}", "headers": {}}


def serve_grpc(port: int = 50051, specs_dir: str = "openfinance_specs") -> None:
    """Start gRPC server"""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    service = OpenFinanceGRPCService(specs_dir)
    asyncio.run(service.load_contracts())

    # Register service (will use generated code)
    # openfinance_pb2_grpc.add_OpenFinanceServiceServicer_to_server(service, server)

    # Enable reflection for debugging
    # from grpc_reflection.v1alpha import reflection
    # SERVICE_NAMES = (
    #     openfinance_pb2.DESCRIPTOR.services_by_name['OpenFinanceService'].full_name,
    #     reflection.SERVICE_NAME,
    # )
    # reflection.enable_server_reflection(SERVICE_NAMES, server)

    server.add_insecure_port(f"[::]:{port}")
    server.start()
    print(f"gRPC server started on port {port}")
    server.wait_for_termination()


if __name__ == "__main__":
    serve_grpc()
