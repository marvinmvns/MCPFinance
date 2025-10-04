from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..domain.openfinance import CorrelationRule, MockedData, OpenFinanceContract


@dataclass(slots=True)
class CorrelatedDataSet:
    """Represents a set of correlated data across contracts"""

    primary_data: MockedData
    related_data: dict[str, list[MockedData]]  # contract_name -> list of related data


class CorrelationEngine:
    """Engine for correlating data across OpenFinance contracts"""

    def __init__(self, rules: list[CorrelationRule]) -> None:
        self.rules = rules
        self.data_store: dict[str, list[MockedData]] = {}  # contract_name -> data

    def add_contract_data(self, contract_name: str, data: list[MockedData]) -> None:
        """Add mocked data for a contract to the correlation store"""
        self.data_store[contract_name] = data

    def correlate_data(
        self, primary_contract: str, primary_id_field: str, primary_id_value: str
    ) -> CorrelatedDataSet | None:
        """Find all data correlated to a primary entity"""
        # Find primary data
        primary_data = self._find_data(primary_contract, primary_id_field, primary_id_value)
        if not primary_data:
            return None

        # Find all related data using correlation rules
        related_data: dict[str, list[MockedData]] = {}

        for rule in self.rules:
            if rule.source_contract == primary_contract:
                # Find related data in target contract
                related = self._find_related_data(primary_data, rule)
                if related:
                    if rule.target_contract not in related_data:
                        related_data[rule.target_contract] = []
                    related_data[rule.target_contract].extend(related)

                    # Recursively find data related to the related data
                    for rel_data in related:
                        nested = self._find_nested_correlations(rule.target_contract, rel_data)
                        for contract_name, nested_data in nested.items():
                            if contract_name not in related_data:
                                related_data[contract_name] = []
                            related_data[contract_name].extend(nested_data)

        return CorrelatedDataSet(primary_data=primary_data, related_data=related_data)

    def get_correlation_chain(
        self, start_contract: str, end_contract: str
    ) -> list[CorrelationRule] | None:
        """Find the chain of correlations from start to end contract"""
        # BFS to find path
        queue: list[tuple[str, list[CorrelationRule]]] = [(start_contract, [])]
        visited: set[str] = {start_contract}

        while queue:
            current, path = queue.pop(0)

            if current == end_contract:
                return path

            for rule in self.rules:
                if rule.source_contract == current and rule.target_contract not in visited:
                    visited.add(rule.target_contract)
                    queue.append((rule.target_contract, path + [rule]))

        return None

    def apply_correlation(
        self, source_data: MockedData, target_contract: str
    ) -> list[MockedData]:
        """Apply correlation rules to link source data to target contract"""
        for rule in self.rules:
            if (
                rule.source_contract in source_data.contract_name.lower()
                and rule.target_contract == target_contract.lower()
            ):
                return self._find_related_data(source_data, rule)

        return []

    def _find_data(
        self, contract_name: str, field_name: str, field_value: str
    ) -> MockedData | None:
        """Find data in store by contract and field value"""
        contract_data = self.data_store.get(contract_name, [])

        for data in contract_data:
            if self._get_nested_value(data.data, field_name) == field_value:
                return data

        return None

    def _find_related_data(
        self, source_data: MockedData, rule: CorrelationRule
    ) -> list[MockedData]:
        """Find data related by correlation rule"""
        source_value = self._get_nested_value(source_data.data, rule.source_field)
        if not source_value:
            return []

        target_data = self.data_store.get(rule.target_contract, [])
        related: list[MockedData] = []

        for data in target_data:
            target_value = self._get_nested_value(data.data, rule.target_field)
            if target_value == source_value:
                related.append(data)

                # Handle relationship types
                if rule.relationship == "one-to-one" and related:
                    break

        return related

    def _find_nested_correlations(
        self, contract_name: str, data: MockedData
    ) -> dict[str, list[MockedData]]:
        """Find nested correlations recursively"""
        nested: dict[str, list[MockedData]] = {}

        for rule in self.rules:
            if rule.source_contract == contract_name:
                related = self._find_related_data(data, rule)
                if related:
                    if rule.target_contract not in nested:
                        nested[rule.target_contract] = []
                    nested[rule.target_contract].extend(related)

        return nested

    def _get_nested_value(self, data: dict[str, Any], field_path: str) -> Any:
        """Get value from nested dict using dot notation (e.g., 'data.consentId')"""
        parts = field_path.split(".")
        current = data

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None

        return current

    def enrich_with_correlations(self, data: MockedData) -> dict[str, Any]:
        """Enrich mocked data with correlation information"""
        enriched = data.data.copy()

        # Find all correlations for this data
        for rule in self.rules:
            if rule.source_contract in data.contract_name.lower():
                source_value = self._get_nested_value(data.data, rule.source_field)
                if source_value:
                    # Add correlation hint
                    correlation_key = f"_correlations_{rule.target_contract}"
                    if correlation_key not in enriched:
                        enriched[correlation_key] = []

                    enriched[correlation_key].append(
                        {
                            "field": rule.target_field,
                            "value": source_value,
                            "relationship": rule.relationship,
                        }
                    )

        return enriched

    def build_correlation_graph(self) -> dict[str, list[str]]:
        """Build a graph of contract correlations"""
        graph: dict[str, list[str]] = {}

        for rule in self.rules:
            if rule.source_contract not in graph:
                graph[rule.source_contract] = []
            graph[rule.source_contract].append(rule.target_contract)

        return graph

    def get_correlation_rules_for_contract(
        self, contract_name: str
    ) -> list[CorrelationRule]:
        """Get all correlation rules involving a contract"""
        return [
            rule
            for rule in self.rules
            if rule.source_contract == contract_name or rule.target_contract == contract_name
        ]
