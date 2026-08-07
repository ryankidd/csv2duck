"""Column schemas for validating CSV rows before they're loaded."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, create_model

_TYPES: dict[str, type] = {
    "string": str,
    "integer": int,
    "float": float,
    "boolean": bool,
}


class ColumnSpec(BaseModel):
    name: str
    type: str
    required: bool = True


def load_schema(path: Path) -> list[ColumnSpec]:
    """Load column specs from a JSON file shaped like {"columns": [...]}."""
    data = json.loads(path.read_text())
    return [ColumnSpec.model_validate(column) for column in data["columns"]]


def build_model(columns: list[ColumnSpec]) -> type[BaseModel]:
    """Build a pydantic model that validates one CSV row against columns."""
    fields: dict[str, Any] = {}
    for column in columns:
        try:
            python_type = _TYPES[column.type]
        except KeyError as exc:
            raise ValueError(f"unknown column type: {column.type!r}") from exc

        default = ... if column.required else None
        fields[column.name] = (python_type, default)

    return create_model("Row", **fields)
