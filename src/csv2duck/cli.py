import csv
from pathlib import Path
from typing import Optional

import typer
from pydantic import ValidationError

from csv2duck.schema import build_model, load_schema

app = typer.Typer(help="Validate, transform, and load CSV/JSON data into DuckDB.")


@app.command()
def ingest(
    path: Path,
    schema: Optional[Path] = typer.Option(
        None,
        "--schema",
        help="Path to a JSON schema file describing the expected columns. "
        "When given, rows are validated instead of just counted.",
    ),
) -> None:
    """Read a CSV file, optionally validating rows against a schema."""
    if schema is None:
        with path.open(newline="") as f:
            row_count = sum(1 for _ in f) - 1  # exclude header
        typer.echo(f"{path}: {row_count} rows")
        return

    model = build_model(load_schema(schema))

    valid = 0
    errors: list[str] = []
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        for line_number, row in enumerate(reader, start=2):  # header is line 1
            try:
                model.model_validate(row)
            except ValidationError as exc:
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
