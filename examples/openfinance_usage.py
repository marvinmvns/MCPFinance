#!/usr/bin/env python
"""
OpenFinance MCP - Example Usage

This script demonstrates how to use the OpenFinance MCP system programmatically.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.services.correlation_engine import CorrelationEngine
from app.services.mock_generator import MockDataGenerator
from app.services.swagger_parser import SwaggerParser


async def main():
    """Demonstrate OpenFinance MCP usage"""
    print("=" * 80)
    print("OpenFinance MCP - Example Usage")
    print("=" * 80)

    # Initialize components
    print("\n1. Initializing components...")
    parser = SwaggerParser()
    mock_generator = MockDataGenerator()
    correlation_engine = CorrelationEngine(parser.correlation_rules)

    # Parse contracts
    print("\n2. Parsing OpenFinance contracts...")
    specs_dir = Path("openfinance_specs")

    if not specs_dir.exists():
        print(f"❌ Directory not found: {specs_dir}")
        print("Run 'make fetch-openfinance' first to download specs")
        return

    contracts = parser.parse_directory(specs_dir)
    print(f"✅ Loaded {len(contracts)} contracts")

    # Display contracts
    print("\n3. Available contracts:")
    for i, contract in enumerate(contracts[:5], 1):
        print(f"   {i}. {contract.name} (v{contract.version}) - {contract.category}")
        print(f"      Endpoints: {len(contract.endpoints)}, Schemas: {len(contract.schemas)}")

    if len(contracts) > 5:
        print(f"   ... and {len(contracts) - 5} more")

    # Generate mock data
    print("\n4. Generating mock data...")
    if contracts:
        contract = contracts[0]
        print(f"   Using contract: {contract.name}")

        mocked_data = mock_generator.generate_for_contract(contract, count=3)
        print(f"   ✅ Generated {len(mocked_data)} mock records")

        # Display first mock
        if mocked_data:
            first_mock = mocked_data[0]
            print(f"\n   Example mock data for {first_mock.schema_name}:")
            print(f"   {json.dumps(first_mock.data, indent=6, ensure_ascii=False)[:500]}...")

    # Add data to correlation engine
    print("\n5. Building correlation store...")
    for contract in contracts:
        mocked_data = mock_generator.generate_for_contract(contract, count=5)
        correlation_engine.add_contract_data(contract.category or contract.name, mocked_data)
        print(f"   ✅ Added {len(mocked_data)} records for {contract.category}")

    # Show correlation graph
    print("\n6. Correlation graph:")
    graph = correlation_engine.build_correlation_graph()
    for source, targets in list(graph.items())[:5]:
        print(f"   {source} → {', '.join(targets)}")

    # Show correlation rules
    print("\n7. Correlation rules:")
    for rule in correlation_engine.rules[:5]:
        print(
            f"   {rule.source_contract}.{rule.source_field} → "
            f"{rule.target_contract}.{rule.target_field} ({rule.relationship})"
        )

    # Example: Find correlated data
    print("\n8. Finding correlated data...")
    if correlation_engine.data_store:
        # Get first contract with data
        first_contract = list(correlation_engine.data_store.keys())[0]
        first_data = correlation_engine.data_store[first_contract][0]

        # Try to find correlations
        print(f"   Primary: {first_contract}")

        # Find a field that might correlate
        for field_name in ["consentId", "accountId", "customerId"]:
            if field_name in first_data.data:
                value = first_data.data[field_name]
                print(f"   Searching by {field_name} = {value}")

                correlated = correlation_engine.correlate_data(first_contract, field_name, value)

                if correlated:
                    print(f"   ✅ Found correlated data:")
                    print(f"      Primary: {correlated.primary_data.schema_name}")
                    for contract_name, data_list in correlated.related_data.items():
                        print(f"      → {contract_name}: {len(data_list)} records")
                break

    # Example: Generate CPF and CNPJ
    print("\n9. Brazilian data generation:")
    cpf = mock_generator._generate_cpf()
    cnpj = mock_generator._generate_cnpj()
    phone = mock_generator._generate_phone()
    print(f"   CPF:   {cpf}")
    print(f"   CNPJ:  {cnpj}")
    print(f"   Phone: {phone}")

    # Summary
    print("\n" + "=" * 80)
    print("Summary:")
    print(f"  - Contracts loaded: {len(contracts)}")
    print(f"  - Correlation rules: {len(correlation_engine.rules)}")
    print(f"  - Data stores: {len(correlation_engine.data_store)}")
    print("=" * 80)

    print("\n✅ Example completed successfully!")
    print("\nNext steps:")
    print("  1. Run REST API: make run")
    print("  2. Run MCP server: make run-mcp")
    print("  3. Run gRPC server: make run-grpc")
    print("  4. See docs: OPENFINANCE_MCP.md")


if __name__ == "__main__":
    asyncio.run(main())
