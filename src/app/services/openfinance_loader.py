from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True, frozen=True)
class ContractSummary:
    name: str
    version: str | None
    paths: list[str]


def load_openapi_contracts(root: Path) -> list[ContractSummary]:
    summaries: list[ContractSummary] = []
    for path in root.rglob("*.json"):
        try:
            data = json.loads(path.read_text("utf-8"))
        except Exception:  # pragma: no cover - defensive
            continue
        info = data.get("info", {})
        name = str(info.get("title", path.stem))
        version = info.get("version")
        paths = list(sorted((data.get("paths") or {}).keys()))
        summaries.append(ContractSummary(name=name, version=version, paths=paths))
    return summaries


def generate_mock_from_schema(schema: dict[str, Any]) -> Any:
    # Very small mocker: choose example if provided, else default by type
    if "example" in schema:
        return schema["example"]
    t = schema.get("type")
    if t == "string":
        return "string"
    if t == "integer":
        return 0
    if t == "number":
        return 0.0
    if t == "boolean":
        return True
    if t == "array":
        return []
    if t == "object":
        return {}
    return None

