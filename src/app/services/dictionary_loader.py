from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


class OpenFinanceDictionaryLoader:
    """Loader for OpenFinance dictionary to enhance data generation"""

    def __init__(self, dictionary_path: str = "openfinance_specs/dictionary") -> None:
        self.dictionary_path = Path(dictionary_path)
        self.dictionaries: dict[str, dict[str, Any]] = {}

    def load_dictionaries(self) -> dict[str, dict[str, Any]]:
        """Load all dictionary files"""
        if not self.dictionary_path.exists():
            print(f"Dictionary path not found: {self.dictionary_path}")
            return {}

        for file_path in self.dictionary_path.rglob("*.json"):
            try:
                data = json.loads(file_path.read_text("utf-8"))
                category = self._extract_category_from_path(file_path)
                self.dictionaries[category] = data
                print(f"Loaded dictionary: {category}")
            except Exception as e:
                print(f"Error loading dictionary {file_path}: {e}")

        for file_path in self.dictionary_path.rglob("*.yaml"):
            try:
                data = yaml.safe_load(file_path.read_text("utf-8"))
                category = self._extract_category_from_path(file_path)
                self.dictionaries[category] = data
                print(f"Loaded dictionary: {category}")
            except Exception as e:
                print(f"Error loading dictionary {file_path}: {e}")

        return self.dictionaries

    def get_field_examples(self, category: str, field_name: str) -> list[Any] | None:
        """Get example values for a field from dictionary"""
        if category not in self.dictionaries:
            return None

        dictionary = self.dictionaries[category]

        # Search for field in dictionary
        examples = self._find_field_examples(dictionary, field_name)
        return examples if examples else None

    def get_enum_values(self, category: str, enum_name: str) -> list[str] | None:
        """Get enum values from dictionary"""
        if category not in self.dictionaries:
            return None

        dictionary = self.dictionaries[category]

        # Look for enums in dictionary
        if "enums" in dictionary and enum_name in dictionary["enums"]:
            return dictionary["enums"][enum_name]

        # Search in nested structures
        enums = self._find_enum_values(dictionary, enum_name)
        return enums if enums else None

    def _extract_category_from_path(self, file_path: Path) -> str:
        """Extract category from file path"""
        # Example: openfinance_specs/dictionary/accounts.json -> accounts
        return file_path.stem

    def _find_field_examples(self, data: dict[str, Any], field_name: str) -> list[Any] | None:
        """Recursively search for field examples in dictionary"""
        if not isinstance(data, dict):
            return None

        # Direct match
        if field_name in data:
            value = data[field_name]
            if isinstance(value, list):
                return value
            return [value]

        # Search in nested structures
        for key, value in data.items():
            if isinstance(value, dict):
                result = self._find_field_examples(value, field_name)
                if result:
                    return result
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                for item in value:
                    result = self._find_field_examples(item, field_name)
                    if result:
                        return result

        return None

    def _find_enum_values(self, data: dict[str, Any], enum_name: str) -> list[str] | None:
        """Recursively search for enum values in dictionary"""
        if not isinstance(data, dict):
            return None

        # Check if this is an enum definition
        if "enum" in data and isinstance(data["enum"], list):
            return data["enum"]

        # Search for specific enum name
        if enum_name in data:
            value = data[enum_name]
            if isinstance(value, list):
                return value
            if isinstance(value, dict) and "values" in value:
                return value["values"]

        # Search in nested structures
        for key, value in data.items():
            if isinstance(value, dict):
                result = self._find_enum_values(value, enum_name)
                if result:
                    return result

        return None

    def enhance_mock_data(self, category: str, field_name: str, default_value: Any) -> Any:
        """Enhance mock data with dictionary values"""
        examples = self.get_field_examples(category, field_name)

        if examples:
            import random

            return random.choice(examples)

        return default_value

    def get_all_categories(self) -> list[str]:
        """Get all loaded dictionary categories"""
        return list(self.dictionaries.keys())

    def get_dictionary_summary(self) -> dict[str, Any]:
        """Get summary of loaded dictionaries"""
        summary = {}

        for category, data in self.dictionaries.items():
            summary[category] = {
                "fields": self._count_fields(data),
                "enums": self._count_enums(data),
            }

        return summary

    def _count_fields(self, data: Any, count: int = 0) -> int:
        """Count total fields in dictionary"""
        if isinstance(data, dict):
            count += len(data.keys())
            for value in data.values():
                count = self._count_fields(value, count)
        elif isinstance(data, list):
            for item in data:
                count = self._count_fields(item, count)

        return count

    def _count_enums(self, data: Any, count: int = 0) -> int:
        """Count total enums in dictionary"""
        if isinstance(data, dict):
            if "enum" in data or "enums" in data:
                count += 1
            for value in data.values():
                count = self._count_enums(value, count)
        elif isinstance(data, list):
            for item in data:
                count = self._count_enums(item, count)

        return count
