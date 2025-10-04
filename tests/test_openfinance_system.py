from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.domain.openfinance import (
    CorrelationRule,
    FieldType,
    FieldValidation,
    MockedData,
    SchemaField,
)
from app.services.correlation_engine import CorrelationEngine
from app.services.mock_generator import MockDataGenerator
from app.services.swagger_parser import SwaggerParser


class TestSwaggerParser:
    """Test Swagger/OpenAPI parser"""

    def test_parser_initialization(self):
        parser = SwaggerParser()
        assert parser is not None
        assert len(parser.correlation_rules) > 0

    def test_parse_simple_schema(self):
        parser = SwaggerParser()
        schema_def = {
            "type": "object",
            "properties": {
                "id": {"type": "string", "pattern": r"^\d{10}$"},
                "name": {"type": "string", "minLength": 1, "maxLength": 100},
                "age": {"type": "integer", "minimum": 0, "maximum": 150},
            },
            "required": ["id", "name"],
        }

        schema = parser._parse_schema_field("TestSchema", schema_def)

        assert schema.name == "TestSchema"
        assert schema.field_type == FieldType.OBJECT
        assert len(schema.properties) == 3
        assert "id" in schema.properties
        assert "name" in schema.properties
        assert "age" in schema.properties

        # Check validations
        id_field = schema.properties["id"]
        assert id_field.validation is not None
        assert id_field.validation.pattern == r"^\d{10}$"

        name_field = schema.properties["name"]
        assert name_field.validation is not None
        assert name_field.validation.min_length == 1
        assert name_field.validation.max_length == 100


class TestMockDataGenerator:
    """Test mock data generator"""

    def test_generator_initialization(self):
        generator = MockDataGenerator()
        assert generator is not None
        assert generator.faker is not None

    def test_generate_cpf(self):
        generator = MockDataGenerator()
        cpf = generator._generate_cpf()

        assert len(cpf) == 11
        assert cpf.isdigit()

    def test_generate_cnpj(self):
        generator = MockDataGenerator()
        cnpj = generator._generate_cnpj()

        assert len(cnpj) == 14
        assert cnpj.isdigit()

    def test_generate_from_validation(self):
        generator = MockDataGenerator()

        # Test string with length constraints
        field = SchemaField(
            name="test_field",
            field_type=FieldType.STRING,
            validation=FieldValidation(min_length=5, max_length=10),
        )

        value = generator._generate_string(field, "test_field")
        assert 5 <= len(value) <= 10

    def test_generate_integer_with_constraints(self):
        generator = MockDataGenerator()

        field = SchemaField(
            name="age",
            field_type=FieldType.INTEGER,
            validation=FieldValidation(minimum=18, maximum=65),
        )

        value = generator._generate_integer(field)
        assert 18 <= value <= 65

    def test_generate_enum_value(self):
        generator = MockDataGenerator()

        field = SchemaField(
            name="status",
            field_type=FieldType.STRING,
            validation=FieldValidation(enum=["ACTIVE", "INACTIVE", "PENDING"]),
        )

        value = generator._generate_field_value(field, "status", "test", "TestSchema")
        assert value in ["ACTIVE", "INACTIVE", "PENDING"]


class TestCorrelationEngine:
    """Test correlation engine"""

    def test_engine_initialization(self):
        rules = [
            CorrelationRule(
                source_contract="consents",
                target_contract="accounts",
                source_field="consentId",
                target_field="consentId",
                relationship="one-to-many",
            )
        ]

        engine = CorrelationEngine(rules)
        assert engine is not None
        assert len(engine.rules) == 1

    def test_add_and_find_data(self):
        rules = [
            CorrelationRule(
                source_contract="consents",
                target_contract="accounts",
                source_field="consentId",
                target_field="consentId",
                relationship="one-to-many",
            )
        ]

        engine = CorrelationEngine(rules)

        # Add mock data
        consent_data = MockedData(
            schema_name="Consent",
            contract_name="Consents API",
            data={"consentId": "123", "status": "ACTIVE"},
        )

        account_data = MockedData(
            schema_name="Account",
            contract_name="Accounts API",
            data={"accountId": "456", "consentId": "123"},
        )

        engine.add_contract_data("consents", [consent_data])
        engine.add_contract_data("accounts", [account_data])

        # Find correlated data
        correlated = engine.correlate_data("consents", "consentId", "123")

        assert correlated is not None
        assert correlated.primary_data.data["consentId"] == "123"
        assert "accounts" in correlated.related_data
        assert len(correlated.related_data["accounts"]) == 1

    def test_correlation_graph(self):
        rules = [
            CorrelationRule(
                source_contract="consents",
                target_contract="accounts",
                source_field="consentId",
                target_field="consentId",
                relationship="one-to-many",
            ),
            CorrelationRule(
                source_contract="accounts",
                target_contract="transactions",
                source_field="accountId",
                target_field="accountId",
                relationship="one-to-many",
            ),
        ]

        engine = CorrelationEngine(rules)
        graph = engine.build_correlation_graph()

        assert "consents" in graph
        assert "accounts" in graph["consents"]
        assert "transactions" in graph["accounts"]

    def test_correlation_chain(self):
        rules = [
            CorrelationRule(
                source_contract="consents",
                target_contract="accounts",
                source_field="consentId",
                target_field="consentId",
                relationship="one-to-many",
            ),
            CorrelationRule(
                source_contract="accounts",
                target_contract="transactions",
                source_field="accountId",
                target_field="accountId",
                relationship="one-to-many",
            ),
        ]

        engine = CorrelationEngine(rules)
        chain = engine.get_correlation_chain("consents", "transactions")

        assert chain is not None
        assert len(chain) == 2
        assert chain[0].source_contract == "consents"
        assert chain[1].target_contract == "transactions"


class TestOpenFinanceEndpoints:
    """Test OpenFinance REST endpoints"""

    def test_list_contracts_endpoint(self, client):
        # Note: This will only work if openfinance_specs directory exists
        response = client.get("/v1/openfinance/contracts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_categories_endpoint(self, client):
        response = client.get("/v1/openfinance/categories")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_correlation_graph_endpoint(self, client):
        response = client.get("/v1/openfinance/correlations")
        assert response.status_code == 200
        data = response.json()
        assert "graph" in data
        assert "rules" in data
        assert isinstance(data["rules"], list)
