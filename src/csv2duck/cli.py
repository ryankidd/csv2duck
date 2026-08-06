from pathlib import Path

import typer

app = typer.Typer(help="Validate, transform, and load CSV/JSON data into DuckDB.")


@app.command()
def ingest(path: Path) -> None:
    """Read a CSV file and report the number of data rows found."""
    with path.open(newline="") as f:
        row_count = sum(1 for _ in f) - 1  # exclude header
    typer.echo(f"{path}: {row_count} rows")


def main() -> None:
    app()
