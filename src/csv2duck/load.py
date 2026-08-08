"""Loading validated/transformed rows into a DuckDB database."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import duckdb

_DUCKDB_TYPES: dict[type, str] = {
    str: "VARCHAR",
    int: "BIGINT",
    float: "DOUBLE",
    bool: "BOOLEAN",
}


def _column_type(values: list[Any]) -> str:
    """Infer a DuckDB column type from the first non-null value in values."""
    for value in values:
        if value is None:
            continue
        return _DUCKDB_TYPES.get(type(value), "VARCHAR")
    return "VARCHAR"


def load_rows(db_path: Path, table: str, rows: list[dict[str, Any]]) -> int:
    """Load rows into a table in the DuckDB database at db_path.

    The table's columns and types are inferred from the rows themselves, and
    any existing table of the same name is replaced rather than appended to,
    so re-running a load with the same table name is idempotent. Returns the
    number of rows loaded.
    """
    if not rows:
        return 0

    columns = list(rows[0].keys())
    column_types = {
        column: _column_type([row.get(column) for row in rows]) for column in columns
    }

    column_defs = ", ".join(f'"{c}" {column_types[c]}' for c in columns)
    quoted_columns = ", ".join(f'"{c}"' for c in columns)
    placeholders = ", ".join("?" for _ in columns)

    con = duckdb.connect(str(db_path))
    try:
        con.execute(f'CREATE OR REPLACE TABLE "{table}" ({column_defs})')
        con.executemany(
            f'INSERT INTO "{table}" ({quoted_columns}) VALUES ({placeholders})',
            [[row.get(c) for c in columns] for row in rows],
        )
    finally:
        con.close()

    return len(rows)
