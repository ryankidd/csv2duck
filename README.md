# csv2duck

A CLI to validate, transform, and load CSV/JSON data into DuckDB.

```bash
uv run csv2duck path/to/data.csv
```

## Status

Early and under active development. Currently reports row counts for a
given CSV file. Schema validation, transforms, and a DuckDB load step are
in progress.

## Development

```bash
uv sync
uv run pytest
```
