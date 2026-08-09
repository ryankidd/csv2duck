# csv2duck

A CLI to validate, transform, and load CSV/JSON data into DuckDB.

```bash
uv run csv2duck path/to/data.csv
```

With no other options, `csv2duck` just reports how many rows the file has.
Passing `--schema`, `--transform`, and/or `--load-db` turns on the rest of
the pipeline.

## Schema validation

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

## Transforming rows

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

## Loading into DuckDB

Passing `--load-db` writes each valid row into a DuckDB database, after any
`--transform` and `--schema` steps have run:

```bash
uv run csv2duck path/to/data.csv --schema path/to/schema.json --load-db path/to/warehouse.duckdb
```

The table is named after the input file's stem by default (`data` for
`data.csv`), or you can give it an explicit name with `--table`:

```bash
uv run csv2duck path/to/data.csv --load-db path/to/warehouse.duckdb --table people
```

Column types in the table are inferred from the loaded values, so pairing
`--load-db` with `--schema` or `--transform` produces typed columns instead
of text. Running the same load again replaces the table rather than
appending to it, so repeated runs stay idempotent. Rows that fail
`--schema` validation are skipped, not loaded.

## JSON input

A `.json` or `.jsonl` file can be used anywhere a CSV file can, and goes
through the same `--transform`, `--schema`, and `--load-db` steps:

```bash
uv run csv2duck path/to/data.json --schema path/to/schema.json
```

Either a JSON array of objects or newline-delimited JSON (one object per
line) is accepted, detected automatically from the file's contents. Since
JSON input has no header row, validation errors are reported by record
number instead of line number.

## Example

The [`examples/`](examples/) directory has a small CSV file, a small JSON
file, and a schema and transform spec that exercise the full pipeline
end to end.

`examples/people.csv` uses source column names that need renaming and type
coercion, so it's run through both `--transform` and `--schema` on its way
into DuckDB:

```bash
uv run csv2duck examples/people.csv \
  --transform examples/transform.json \
  --schema examples/schema.json \
  --load-db /tmp/example.duckdb \
  --table people
```

```
examples/people.csv: 3 valid rows, 0 invalid
loaded 3 rows into /tmp/example.duckdb:people
```

`examples/people.json` already uses the target column names, so it only
needs `--schema`:

```bash
uv run csv2duck examples/people.json \
  --schema examples/schema.json \
  --load-db /tmp/example.duckdb \
  --table more_people
```

```
examples/people.json: 2 valid rows, 0 invalid
loaded 2 rows into /tmp/example.duckdb:more_people
```

Both tables now live side by side in the same database, with `age` stored
as an integer column rather than text:

```bash
uv run python -c "
import duckdb
con = duckdb.connect('/tmp/example.duckdb')
print(con.sql('SELECT * FROM people').fetchall())
print(con.sql('SELECT * FROM more_people').fetchall())
"
```

```
[('Alice Chen', 34), ('Bob Diaz', 29), ('Carol Nguyen', 41)]
[('Dave Okafor', 52), ('Erin Walsh', 26)]
```

## Status

Early and under active development. Currently reports row counts for a
given CSV or JSON file, applies column renames and type coercion via
`--transform`, validates rows against a pydantic-backed schema, and loads
the result into DuckDB via `--load-db`.

## Development

```bash
uv sync
uv run pytest
```
