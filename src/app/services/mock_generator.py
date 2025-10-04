from __future__ import annotations

import random
import re
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from faker import Faker

from ..domain.openfinance import (
    FieldFormat,
    FieldType,
    FieldValidation,
    MockedData,
    OpenFinanceContract,
    SchemaField,
)


class MockDataGenerator:
    """Advanced mock data generator with regex validation support"""

    def __init__(self, locale: str = "pt_BR") -> None:
        self.faker = Faker(locale)
        self.correlation_store: dict[str, dict[str, Any]] = {}

    def generate_for_contract(
        self, contract: OpenFinanceContract, count: int = 10
    ) -> list[MockedData]:
        """Generate mock data for all schemas in a contract"""
        mocked_data: list[MockedData] = []

        # Generate data for each schema
        for schema_name, schema in contract.schemas.items():
            for _ in range(count):
                data = self._generate_from_schema(schema, schema_name, contract.category or "")
                mocked = MockedData(
                    schema_name=schema_name, contract_name=contract.name, data=data
                )
                mocked_data.append(mocked)

                # Store correlation IDs for later linking
                self._store_correlation_ids(contract.category or "", schema_name, data)

        return mocked_data

    def _generate_from_schema(
        self, schema: SchemaField, schema_name: str, category: str
    ) -> dict[str, Any]:
        """Generate mock data from schema definition"""
        if schema.ref:
            # Handle reference - for now return placeholder
            return {"$ref": schema.ref}

        if schema.field_type == FieldType.OBJECT:
            result: dict[str, Any] = {}
            for prop_name, prop_schema in schema.properties.items():
                result[prop_name] = self._generate_field_value(
                    prop_schema, prop_name, category, schema_name
                )
            return result

        return {}

    def _generate_field_value(
        self, field: SchemaField, field_name: str, category: str, schema_name: str
    ) -> Any:
        """Generate value for a single field respecting validations"""
        # Use example if available
        if field.example is not None:
            return field.example

        # Handle arrays
        if field.field_type == FieldType.ARRAY:
            count = random.randint(1, 5)
            if field.items_schema:
                return [
                    self._generate_field_value(field.items_schema, f"{field_name}_item", category, schema_name)
                    for _ in range(count)
                ]
            return []

        # Handle objects
        if field.field_type == FieldType.OBJECT:
            result: dict[str, Any] = {}
            for prop_name, prop_schema in field.properties.items():
                result[prop_name] = self._generate_field_value(
                    prop_schema, prop_name, category, schema_name
                )
            return result

        # Handle enums
        if field.validation and field.validation.enum:
            return random.choice(field.validation.enum)

        # Generate based on field name patterns and validations
        return self._generate_typed_value(field, field_name, category, schema_name)

    def _generate_typed_value(
        self, field: SchemaField, field_name: str, category: str, schema_name: str
    ) -> Any:
        """Generate typed value based on field type and name patterns"""
        field_lower = field_name.lower()

        # Handle special OpenFinance patterns
        if "consent" in field_lower and "id" in field_lower:
            return f"urn:bancoex:{str(uuid.uuid4())}"

        if field_name == "consentId":
            consent_id = f"urn:bancoex:{str(uuid.uuid4())}"
            self._store_id("consent", consent_id)
            return consent_id

        if field_name in ["accountId", "accountid"]:
            account_id = str(uuid.uuid4())
            self._store_id("account", account_id)
            return account_id

        if field_name in ["customerId", "customerid"]:
            return str(uuid.uuid4())

        if "cpf" in field_lower:
            return self._generate_cpf()

        if "cnpj" in field_lower:
            return self._generate_cnpj()

        if "phone" in field_lower or "telephone" in field_lower:
            return self._generate_phone()

        if "email" in field_lower:
            return self.faker.email()

        # Handle by type
        if field.field_type == FieldType.STRING:
            return self._generate_string(field, field_name)

        if field.field_type == FieldType.INTEGER:
            return self._generate_integer(field)

        if field.field_type == FieldType.NUMBER:
            return self._generate_number(field)

        if field.field_type == FieldType.BOOLEAN:
            return random.choice([True, False])

        return None

    def _generate_string(self, field: SchemaField, field_name: str) -> str:
        """Generate string value respecting format and validation"""
        validation = field.validation

        # Handle format
        if validation and validation.format:
            if validation.format == FieldFormat.DATE:
                return self.faker.date()
            if validation.format == FieldFormat.DATE_TIME:
                return datetime.now(UTC).isoformat() + "Z"
            if validation.format == FieldFormat.EMAIL:
                return self.faker.email()
            if validation.format == FieldFormat.UUID:
                return str(uuid.uuid4())
            if validation.format == FieldFormat.URI:
                return self.faker.url()

        # Handle regex pattern
        if validation and validation.pattern:
            return self._generate_from_regex(validation.pattern, validation)

        # Generate based on field name
        field_lower = field_name.lower()
        if "name" in field_lower:
            return self.faker.name()
        if "address" in field_lower:
            return self.faker.address()
        if "city" in field_lower:
            return self.faker.city()
        if "state" in field_lower:
            return self.faker.state_abbr()
        if "country" in field_lower:
            return "BRA"
        if "code" in field_lower:
            return f"{random.randint(1000, 9999)}"
        if "description" in field_lower:
            return self.faker.sentence()

        # Default string with length constraints
        min_len = validation.min_length if validation and validation.min_length else 1
        max_len = validation.max_length if validation and validation.max_length else 50
        length = random.randint(min_len, min(max_len, 50))

        text = self.faker.text(max_nb_chars=length).strip()
        # Ensure text meets minimum length after stripping
        if len(text) < min_len:
            text = text + "x" * (min_len - len(text))
        return text[:max_len]

    def _generate_integer(self, field: SchemaField) -> int:
        """Generate integer value respecting constraints"""
        validation = field.validation
        minimum = int(validation.minimum) if validation and validation.minimum else 0
        maximum = int(validation.maximum) if validation and validation.maximum else 1000000

        return random.randint(minimum, maximum)

    def _generate_number(self, field: SchemaField) -> float:
        """Generate number value respecting constraints"""
        validation = field.validation
        minimum = validation.minimum if validation and validation.minimum else 0.0
        maximum = validation.maximum if validation and validation.maximum else 1000000.0

        return round(random.uniform(minimum, maximum), 2)

    def _generate_from_regex(self, pattern: str, validation: FieldValidation | None) -> str:
        """Generate string matching regex pattern (simplified approach)"""
        # Common OpenFinance patterns
        if pattern == r"^\d{11}$":  # CPF
            return self._generate_cpf()

        if pattern == r"^\d{14}$":  # CNPJ
            return self._generate_cnpj()

        if pattern.startswith(r"^urn:"):  # URN pattern
            return f"urn:bancoex:{str(uuid.uuid4())}"

        if r"\d{4}-\d{2}-\d{2}" in pattern:  # Date
            return self.faker.date()

        if "uuid" in pattern.lower():
            return str(uuid.uuid4())

        # Try to match simple patterns
        if re.match(r"\^\\d\{(\d+)\}\$", pattern):
            # Pattern like ^\d{10}$
            match = re.match(r"\^\\d\{(\d+)\}\$", pattern)
            if match:
                length = int(match.group(1))
                return "".join([str(random.randint(0, 9)) for _ in range(length)])

        # Default: generate string respecting length
        min_len = validation.min_length if validation and validation.min_length else 1
        max_len = validation.max_length if validation and validation.max_length else 20

        return self.faker.lexify(text="?" * random.randint(min_len, max_len))

    def _generate_cpf(self) -> str:
        """Generate valid Brazilian CPF"""
        # Generate 9 random digits
        cpf = [random.randint(0, 9) for _ in range(9)]

        # Calculate first digit
        sum1 = sum(cpf[i] * (10 - i) for i in range(9))
        digit1 = (sum1 * 10) % 11
        if digit1 == 10:
            digit1 = 0
        cpf.append(digit1)

        # Calculate second digit
        sum2 = sum(cpf[i] * (11 - i) for i in range(10))
        digit2 = (sum2 * 10) % 11
        if digit2 == 10:
            digit2 = 0
        cpf.append(digit2)

        return "".join(map(str, cpf))

    def _generate_cnpj(self) -> str:
        """Generate valid Brazilian CNPJ"""
        # Generate 12 random digits
        cnpj = [random.randint(0, 9) for _ in range(12)]

        # Calculate first digit
        weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        sum1 = sum(cnpj[i] * weights1[i] for i in range(12))
        digit1 = sum1 % 11
        digit1 = 0 if digit1 < 2 else 11 - digit1
        cnpj.append(digit1)

        # Calculate second digit
        weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        sum2 = sum(cnpj[i] * weights2[i] for i in range(13))
        digit2 = sum2 % 11
        digit2 = 0 if digit2 < 2 else 11 - digit2
        cnpj.append(digit2)

        return "".join(map(str, cnpj))

    def _generate_phone(self) -> str:
        """Generate Brazilian phone number"""
        ddd = random.randint(11, 99)
        number = random.randint(900000000, 999999999)
        return f"+55{ddd}{number}"

    def _store_correlation_ids(
        self, category: str, schema_name: str, data: dict[str, Any]
    ) -> None:
        """Store correlation IDs for linking data"""
        key = f"{category}:{schema_name}"
        if key not in self.correlation_store:
            self.correlation_store[key] = {}

        # Extract and store IDs
        for field_name in ["consentId", "accountId", "customerId", "creditCardAccountId"]:
            if field_name in data:
                self.correlation_store[key][field_name] = data[field_name]

    def _store_id(self, id_type: str, id_value: str) -> None:
        """Store ID for correlation"""
        if id_type not in self.correlation_store:
            self.correlation_store[id_type] = {}
        self.correlation_store[id_type]["last"] = id_value

    def get_correlation_id(self, id_type: str) -> str | None:
        """Get stored correlation ID"""
        return self.correlation_store.get(id_type, {}).get("last")
