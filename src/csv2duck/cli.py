import csv
from pathlib import Path

import typer
from pydantic import ValidationError

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
) -> None:
    """Read a CSV file, optionally transforming and validating each row."""
    if schema is None and transform is None:
        with path.open(newline="") as f:
            row_count = sum(1 for _ in f) - 1  # exclude header
        typer.echo(f"{path}: {row_count} rows")
        return

    transform_spec = load_transform(transform) if transform is not None else None
    model = build_model(load_schema(schema)) if schema is not None else None

    valid = 0
    errors: list[str] = []
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        for line_number, row in enumerate(reader, start=2):  # header is line 1
            try:
                if transform_spec is not None:
                    row = apply_transform(row, transform_spec)
                if model is not None:
                    model.model_validate(row)
            except (ValidationError, ValueError) as exc:
                errors.append(f"line {line_number}: {exc}")
            else:
                valid += 1

    typer.echo(f"{path}: {valid} valid rows, {len(errors)} invalid")
    for error in errors:
        typer.echo(error)

    if errors:
        raise typer.Exit(code=1)


def main() -> None:
    app()
