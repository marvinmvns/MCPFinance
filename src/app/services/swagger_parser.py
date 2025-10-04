from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from ..domain.openfinance import (
    CorrelationRule,
    EndpointPath,
    FieldFormat,
    FieldType,
    FieldValidation,
    OpenFinanceContract,
    SchemaField,
)


class SwaggerParser:
    """Advanced parser for OpenAPI/Swagger specifications with validation extraction"""

    def __init__(self) -> None:
        self.correlation_rules: list[CorrelationRule] = self._load_correlation_rules()

    def parse_file(self, file_path: Path) -> OpenFinanceContract | None:
        """Parse a single OpenAPI file (JSON or YAML)"""
        try:
            content = file_path.read_text("utf-8")
            if file_path.suffix.lower() in [".yaml", ".yml"]:
                spec = yaml.safe_load(content)
            else:
                spec = json.loads(content)

            return self._parse_spec(spec, file_path)
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return None

    def parse_directory(self, root_path: Path) -> list[OpenFinanceContract]:
        """Parse all OpenAPI files in directory recursively"""
        contracts: list[OpenFinanceContract] = []

        for pattern in ["*.json", "*.yaml", "*.yml"]:
            for file_path in root_path.rglob(pattern):
                if "node_modules" in str(file_path) or ".git" in str(file_path):
                    continue
                contract = self.parse_file(file_path)
                if contract:
                    contracts.append(contract)

        return contracts

    def _parse_spec(self, spec: dict[str, Any], file_path: Path) -> OpenFinanceContract:
        """Parse OpenAPI specification into OpenFinanceContract"""
        info = spec.get("info", {})
        name = info.get("title", file_path.stem)
        version = info.get("version")
        description = info.get("description")

        # Extract base path
        servers = spec.get("servers", [])
        base_path = servers[0].get("url") if servers else None

        # Determine category from file path or name
        category = self._extract_category(file_path, name)

        # Parse schemas from components
        components = spec.get("components", {})
        schemas = self._parse_schemas(components.get("schemas", {}))

        # Parse endpoints
        endpoints = self._parse_paths(spec.get("paths", {}))

        return OpenFinanceContract(
            name=name,
            version=version,
            description=description,
            base_path=base_path,
            endpoints=endpoints,
            schemas=schemas,
            file_path=str(file_path),
            category=category,
        )

    def _parse_schemas(self, schemas_dict: dict[str, Any]) -> dict[str, SchemaField]:
        """Parse components/schemas section"""
        parsed_schemas: dict[str, SchemaField] = {}

        for schema_name, schema_def in schemas_dict.items():
            field = self._parse_schema_field(schema_name, schema_def)
            parsed_schemas[schema_name] = field

        return parsed_schemas

    def _parse_schema_field(
        self, name: str, schema_def: dict[str, Any], parent_required: list[str] | None = None
    ) -> SchemaField:
        """Parse a schema field with all validation rules"""
        # Handle $ref
        if "$ref" in schema_def:
            ref = schema_def["$ref"].split("/")[-1]
            return SchemaField(
                name=name, field_type=FieldType.OBJECT, ref=ref, description=schema_def.get("description")
            )

        field_type_str = schema_def.get("type", "object")
        try:
            field_type = FieldType(field_type_str)
        except ValueError:
            field_type = FieldType.OBJECT

        # Extract validation rules
        validation = self._extract_validation(schema_def)

        # Check if required
        required = parent_required and name in parent_required

        # Parse nested properties for objects
        properties: dict[str, SchemaField] = {}
        if field_type == FieldType.OBJECT and "properties" in schema_def:
            required_fields = schema_def.get("required", [])
            for prop_name, prop_def in schema_def["properties"].items():
                properties[prop_name] = self._parse_schema_field(prop_name, prop_def, required_fields)

        # Parse items for arrays
        items_schema = None
        if field_type == FieldType.ARRAY and "items" in schema_def:
            items_schema = self._parse_schema_field(f"{name}_item", schema_def["items"])

        return SchemaField(
            name=name,
            field_type=field_type,
            description=schema_def.get("description"),
            required=required,
            validation=validation,
            example=schema_def.get("example"),
            items_schema=items_schema,
            properties=properties,
        )

    def _extract_validation(self, schema_def: dict[str, Any]) -> FieldValidation | None:
        """Extract validation rules from schema definition"""
        pattern = schema_def.get("pattern")
        min_length = schema_def.get("minLength")
        max_length = schema_def.get("maxLength")
        minimum = schema_def.get("minimum")
        maximum = schema_def.get("maximum")
        enum = schema_def.get("enum")
        format_str = schema_def.get("format")

        field_format = None
        if format_str:
            try:
                field_format = FieldFormat(format_str)
            except ValueError:
                pass

        if any([pattern, min_length, max_length, minimum, maximum, enum, field_format]):
            return FieldValidation(
                pattern=pattern,
                min_length=min_length,
                max_length=max_length,
                minimum=minimum,
                maximum=maximum,
                enum=enum,
                format=field_format,
            )

        return None

    def _parse_paths(self, paths_dict: dict[str, Any]) -> list[EndpointPath]:
        """Parse paths section into endpoint definitions"""
        endpoints: list[EndpointPath] = []

        for path, methods in paths_dict.items():
            for method, operation in methods.items():
                if method.upper() not in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    continue

                # Extract request/response schemas
                request_schema = None
                if "requestBody" in operation:
                    content = operation["requestBody"].get("content", {})
                    json_content = content.get("application/json", {})
                    schema = json_content.get("schema", {})
                    if "$ref" in schema:
                        request_schema = schema["$ref"].split("/")[-1]

                response_schema = None
                responses = operation.get("responses", {})
                success_response = responses.get("200") or responses.get("201")
                if success_response:
                    content = success_response.get("content", {})
                    json_content = content.get("application/json", {})
                    schema = json_content.get("schema", {})
                    if "$ref" in schema:
                        response_schema = schema["$ref"].split("/")[-1]

                endpoints.append(
                    EndpointPath(
                        path=path,
                        method=method.upper(),
                        operation_id=operation.get("operationId"),
                        summary=operation.get("summary"),
                        description=operation.get("description"),
                        request_schema=request_schema,
                        response_schema=response_schema,
                        parameters=operation.get("parameters", []),
                    )
                )

        return endpoints

    def _extract_category(self, file_path: Path, name: str) -> str:
        """Extract category from file path or contract name"""
        path_str = str(file_path).lower()

        categories = [
            "consents",
            "resources",
            "customers",
            "accounts",
            "credit-cards-accounts",
            "loans",
            "financings",
            "unarranged-accounts-overdraft",
            "invoice-financings",
            "bank-fixed-incomes",
            "credit-fixed-incomes",
            "variable-incomes",
            "treasure-titles",
            "funds",
            "exchanges",
            "acquiring-services",
            "automatic-payments",
            "capitalization-title",
            "pension",
        ]

        for category in categories:
            if category in path_str or category in name.lower():
                return category

        return "unknown"

    def _load_correlation_rules(self) -> list[CorrelationRule]:
        """Load predefined correlation rules for OpenFinance APIs"""
        return [
            # Consent -> Resources
            CorrelationRule(
                source_contract="consents",
                target_contract="resources",
                source_field="consentId",
                target_field="consentId",
                relationship="one-to-many",
            ),
            # Resources -> Accounts
            CorrelationRule(
                source_contract="resources",
                target_contract="accounts",
                source_field="accountId",
                target_field="accountId",
                relationship="one-to-one",
            ),
            # Accounts -> Transactions
            CorrelationRule(
                source_contract="accounts",
                target_contract="transactions",
                source_field="accountId",
                target_field="accountId",
                relationship="one-to-many",
            ),
            # Customer -> Accounts
            CorrelationRule(
                source_contract="customers",
                target_contract="accounts",
                source_field="customerId",
                target_field="customerId",
                relationship="one-to-many",
            ),
            # Credit Cards
            CorrelationRule(
                source_contract="credit-cards-accounts",
                target_contract="transactions",
                source_field="creditCardAccountId",
                target_field="creditCardAccountId",
                relationship="one-to-many",
            ),
        ]
