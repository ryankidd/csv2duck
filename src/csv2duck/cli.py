from pathlib import Path
from typing import Any

import typer
from pydantic import ValidationError

from csv2duck.ingest import read_rows
from csv2duck.load import load_rows
from csv2duck.schema import build_model, load_schema
from csv2duck.transform import apply_transform, load_transform

app = typer.Typer(help="Validate, transform, and load CSV/JSON data into DuckDB.")


@app.command()
def ingest(
    path: Path,
    schema: Path | None = typer.Option(
        None,
        "--schema",
        help="Path to a JSON schema file describing the expected columns. "
        "When given, rows are validated instead of just counted.",
    ),
    transform: Path | None = typer.Option(
        None,
        "--transform",
        help="Path to a JSON transform spec describing column renames and "
        "type coercions. Applied to each row before schema validation.",
    ),
    load_db: Path | None = typer.Option(
        None,
        "--load-db",
        help="Path to a DuckDB database file. When given, valid rows are "
        "loaded into it, after any --transform and --schema validation, "
        "replacing the target table if it already exists.",
    ),
    table: str | None = typer.Option(
        None,
        "--table",
        help="Name of the table to load rows into. Defaults to the input "
        "file's stem. Only used together with --load-db.",
    ),
) -> None:
    """Read a CSV or JSON file, optionally transforming, validating, and
    loading each row into DuckDB."""
    if schema is None and transform is None and load_db is None:
        row_count = sum(1 for _ in read_rows(path))
        typer.echo(f"{path}: {row_count} rows")
        return

    transform_spec = load_transform(transform) if transform is not None else None
    model = build_model(load_schema(schema)) if schema is not None else None
    label = "record" if path.suffix in {".json", ".jsonl"} else "line"

    valid = 0
    errors: list[str] = []
    loaded_rows: list[dict[str, Any]] = []
    for number, row in read_rows(path):
        try:
            if transform_spec is not None:
                row = apply_transform(row, transform_spec)
            if model is not None:
                row = model.model_validate(row).model_dump()
        except (ValidationError, ValueError) as exc:
            errors.append(f"{label} {number}: {exc}")
        else:
            valid += 1
            if load_db is not None:
                loaded_rows.append(row)

    typer.echo(f"{path}: {valid} valid rows, {len(errors)} invalid")
    for error in errors:
        typer.echo(error)

    if load_db is not None:
        table_name = table or path.stem
        loaded = load_rows(load_db, table_name, loaded_rows)
        typer.echo(f"loaded {loaded} rows into {load_db}:{table_name}")

    if errors:
        raise typer.Exit(code=1)


def main() -> None:
    app()
