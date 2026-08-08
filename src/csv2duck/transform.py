"""Row-level transforms: column renames and type coercion, applied before
validation or loading."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from pydantic import BaseModel


def _to_bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


_COERCERS: dict[str, Callable[[str], Any]] = {
    "string": str,
    "integer": int,
    "float": float,
    "boolean": _to_bool,
}


class ColumnTransform(BaseModel):
    source: str
    target: str | None = None
    type: str | None = None


class TransformSpec(BaseModel):
    columns: list[ColumnTransform]


def load_transform(path: Path) -> TransformSpec:
    """Load a transform spec from a JSON file shaped like {"columns": [...]}."""
    data = json.loads(path.read_text())
    return TransformSpec.model_validate(data)


def apply_transform(row: dict[str, Any], spec: TransformSpec) -> dict[str, Any]:
    """Rename and/or coerce the columns named in spec; every other column
    passes through unchanged."""
    mentioned = {column.source for column in spec.columns}
    result: dict[str, Any] = {k: v for k, v in row.items() if k not in mentioned}

    for column in spec.columns:
        if column.source not in row:
            continue

        value = row[column.source]
        if column.type is not None:
            try:
                coerce = _COERCERS[column.type]
            except KeyError as exc:
                raise ValueError(f"unknown transform type: {column.type!r}") from exc
            value = coerce(value)

        result[column.target or column.source] = value

    return result
