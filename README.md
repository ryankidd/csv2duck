# csv2duck

A CLI to validate, transform, and load CSV/JSON data into DuckDB.

```bash
uv run csv2duck path/to/data.csv
```

Passing `--schema` validates each row against a column schema instead of
just counting rows:

```bash
uv run csv2duck path/to/data.csv --schema path/to/schema.json
```

A schema file lists the expected columns:

```json
{
  "columns": [
    { "name": "name", "type": "string" },
    { "name": "age", "type": "integer" },
    { "name": "nickname", "type": "string", "required": false }
  ]
}
```

Supported types are `string`, `integer`, `float`, and `boolean`. Columns
are required unless `"required": false` is set. Rows that fail validation
are reported with their line number, and the command exits non-zero if any
row is invalid.

## Status

Early and under active development. Currently reports row counts for a
given CSV file and validates rows against a pydantic-backed schema.
Transforms and a DuckDB load step are in progress.

## Development

```bash
uv sync
uv run pytest
```
