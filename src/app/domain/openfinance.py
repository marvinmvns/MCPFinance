from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class FieldType(str, Enum):
    """OpenAPI field types"""

    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


class FieldFormat(str, Enum):
    """Common OpenAPI formats"""

    DATE = "date"
    DATE_TIME = "date-time"
    EMAIL = "email"
    UUID = "uuid"
    URI = "uri"
    BYTE = "byte"
    BINARY = "binary"
    INT32 = "int32"
    INT64 = "int64"
    FLOAT = "float"
    DOUBLE = "double"


@dataclass(slots=True)
class FieldValidation:
    """Validation rules for a field"""

    pattern: str | None = None  # regex pattern
    min_length: int | None = None
    max_length: int | None = None
    minimum: float | None = None
    maximum: float | None = None
    enum: list[Any] | None = None
    format: FieldFormat | None = None


@dataclass(slots=True)
class SchemaField:
    """Represents a field in an OpenAPI schema"""

    name: str
    field_type: FieldType
    description: str | None = None
    required: bool = False
    validation: FieldValidation | None = None
    example: Any | None = None
    items_schema: SchemaField | None = None  # For arrays
    properties: dict[str, SchemaField] = field(default_factory=dict)  # For objects
    ref: str | None = None  # Schema reference


@dataclass(slots=True, frozen=True)
class EndpointPath:
    """Represents an API endpoint path"""

    path: str
    method: str  # GET, POST, PUT, DELETE, PATCH
    operation_id: str | None
    summary: str | None
    description: str | None
    request_schema: str | None  # Schema reference for request body
    response_schema: str | None  # Schema reference for 200 response
    parameters: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class OpenFinanceContract:
    """Represents a complete OpenFinance API contract"""

    name: str
    version: str | None
    description: str | None
    base_path: str | None
    endpoints: list[EndpointPath] = field(default_factory=list)
    schemas: dict[str, SchemaField] = field(default_factory=dict)  # components/schemas
    file_path: str | None = None
    category: str | None = None  # e.g., "consents", "accounts", "credit-cards"


@dataclass(slots=True)
class MockedData:
    """Represents mocked data for a schema"""

    schema_name: str
    contract_name: str
    data: dict[str, Any]
    correlation_ids: dict[str, str] = field(default_factory=dict)  # Links to other entities
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True)
class CorrelationRule:
    """Defines how contracts are correlated"""

    source_contract: str  # e.g., "consents"
    target_contract: str  # e.g., "accounts"
    source_field: str  # Field in source that maps to target
    target_field: str  # Field in target to match
    relationship: str  # "one-to-many", "one-to-one", "many-to-many"
