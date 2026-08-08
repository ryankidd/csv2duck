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

Passing `--transform` renames columns and/or coerces their values before
validation:

```bash
uv run csv2duck path/to/data.csv --transform path/to/transform.json --schema path/to/schema.json
```

A transform file lists source columns and, optionally, a new name and/or
type to coerce the value to:

```json
{
  "columns": [
    { "source": "full_name", "target": "name" },
    { "source": "yrs", "target": "age", "type": "integer" }
  ]
}
```

Columns not mentioned in the transform pass through unchanged. `--transform`
can be used on its own, without `--schema`, to just rename/coerce and
report rows that fail coercion.

## Status

Early and under active development. Currently reports row counts for a
given CSV file, applies column renames and type coercion via `--transform`,
and validates rows against a pydantic-backed schema. A DuckDB load step is
in progress.

## Development

```bash
uv sync
uv run pytest
```
