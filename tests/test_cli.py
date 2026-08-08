import json

import duckdb
from typer.testing import CliRunner

from csv2duck.cli import app

runner = CliRunner()


def test_ingest_reports_row_count(tmp_path):
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text("name,age\nalice,30\nbob,25\n")

    result = runner.invoke(app, [str(csv_path)])

    assert result.exit_code == 0
    assert "2 rows" in result.stdout


def _write_schema(tmp_path, columns):
    schema_path = tmp_path / "schema.json"
    schema_path.write_text(json.dumps({"columns": columns}))
    return schema_path


def test_ingest_with_schema_reports_valid_rows(tmp_path):
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text("name,age\nalice,30\nbob,25\n")
    schema_path = _write_schema(
        tmp_path,
        [{"name": "name", "type": "string"}, {"name": "age", "type": "integer"}],
    )

    result = runner.invoke(app, [str(csv_path), "--schema", str(schema_path)])

    assert result.exit_code == 0
    assert "2 valid rows, 0 invalid" in result.stdout


def test_ingest_with_schema_reports_invalid_rows(tmp_path):
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text("name,age\nalice,thirty\nbob,25\n")
    schema_path = _write_schema(
        tmp_path,
        [{"name": "name", "type": "string"}, {"name": "age", "type": "integer"}],
    )

    result = runner.invoke(app, [str(csv_path), "--schema", str(schema_path)])

    assert result.exit_code == 1
    assert "1 valid rows, 1 invalid" in result.stdout
    assert "line 2" in result.stdout


def _write_transform(tmp_path, columns):
    transform_path = tmp_path / "transform.json"
    transform_path.write_text(json.dumps({"columns": columns}))
    return transform_path


def test_ingest_with_transform_renames_and_coerces_before_validation(tmp_path):
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text("full_name,yrs\nalice,30\nbob,25\n")
    transform_path = _write_transform(
        tmp_path,
        [
            {"source": "full_name", "target": "name"},
            {"source": "yrs", "target": "age", "type": "integer"},
        ],
    )
    schema_path = _write_schema(
        tmp_path,
        [{"name": "name", "type": "string"}, {"name": "age", "type": "integer"}],
    )

    result = runner.invoke(
        app,
        [
            str(csv_path),
            "--transform",
            str(transform_path),
            "--schema",
            str(schema_path),
        ],
    )

    assert result.exit_code == 0
    assert "2 valid rows, 0 invalid" in result.stdout


def test_ingest_with_transform_only_reports_coercion_failures(tmp_path):
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text("age\n30\nnot-a-number\n")
    transform_path = _write_transform(
        tmp_path, [{"source": "age", "type": "integer"}]
    )

    result = runner.invoke(app, [str(csv_path), "--transform", str(transform_path)])

    assert result.exit_code == 1
    assert "1 valid rows, 1 invalid" in result.stdout
    assert "line 3" in result.stdout


def test_ingest_with_load_db_writes_rows_to_default_table(tmp_path):
    csv_path = tmp_path / "people.csv"
    csv_path.write_text("name,age\nalice,30\nbob,25\n")
    db_path = tmp_path / "out.duckdb"

    result = runner.invoke(app, [str(csv_path), "--load-db", str(db_path)])

    assert result.exit_code == 0
    assert "loaded 2 rows" in result.stdout
    con = duckdb.connect(str(db_path))
    try:
        rows = con.execute("SELECT name, age FROM people ORDER BY name").fetchall()
    finally:
        con.close()
    assert rows == [("alice", "30"), ("bob", "25")]


def test_ingest_with_load_db_and_table_uses_given_table_name(tmp_path):
    csv_path = tmp_path / "people.csv"
    csv_path.write_text("name,age\nalice,30\n")
    db_path = tmp_path / "out.duckdb"

    result = runner.invoke(
        app, [str(csv_path), "--load-db", str(db_path), "--table", "customers"]
    )

    assert result.exit_code == 0
    con = duckdb.connect(str(db_path))
    try:
        rows = con.execute("SELECT name FROM customers").fetchall()
    finally:
        con.close()
    assert rows == [("alice",)]


def test_ingest_with_load_db_composes_with_transform_and_schema(tmp_path):
    csv_path = tmp_path / "people.csv"
    csv_path.write_text("full_name,yrs\nalice,30\nbob,25\n")
    transform_path = _write_transform(
        tmp_path,
        [
            {"source": "full_name", "target": "name"},
            {"source": "yrs", "target": "age", "type": "integer"},
        ],
    )
    schema_path = _write_schema(
        tmp_path,
        [{"name": "name", "type": "string"}, {"name": "age", "type": "integer"}],
    )
    db_path = tmp_path / "out.duckdb"

    result = runner.invoke(
        app,
        [
            str(csv_path),
            "--transform",
            str(transform_path),
            "--schema",
            str(schema_path),
            "--load-db",
            str(db_path),
        ],
    )

    assert result.exit_code == 0
    con = duckdb.connect(str(db_path))
    try:
        rows = con.execute("SELECT name, age FROM people ORDER BY name").fetchall()
        types = {
            name: column_type
            for name, column_type, *_ in con.execute("DESCRIBE people").fetchall()
        }
    finally:
        con.close()
    assert rows == [("alice", 30), ("bob", 25)]
    assert types == {"name": "VARCHAR", "age": "BIGINT"}


def test_ingest_with_load_db_skips_invalid_rows(tmp_path):
    csv_path = tmp_path / "people.csv"
    csv_path.write_text("name,age\nalice,thirty\nbob,25\n")
    schema_path = _write_schema(
        tmp_path,
        [{"name": "name", "type": "string"}, {"name": "age", "type": "integer"}],
    )
    db_path = tmp_path / "out.duckdb"

    result = runner.invoke(
        app, [str(csv_path), "--schema", str(schema_path), "--load-db", str(db_path)]
    )

    assert result.exit_code == 1
    con = duckdb.connect(str(db_path))
    try:
        rows = con.execute("SELECT name, age FROM people").fetchall()
    finally:
        con.close()
    assert rows == [("bob", 25)]


def test_ingest_with_load_db_rerun_replaces_table(tmp_path):
    csv_path = tmp_path / "people.csv"
    csv_path.write_text("name,age\nalice,30\n")
    db_path = tmp_path / "out.duckdb"
    runner.invoke(app, [str(csv_path), "--load-db", str(db_path)])

    csv_path.write_text("name,age\ncarol,40\n")
    result = runner.invoke(app, [str(csv_path), "--load-db", str(db_path)])

    assert result.exit_code == 0
    con = duckdb.connect(str(db_path))
    try:
        rows = con.execute("SELECT name, age FROM people").fetchall()
    finally:
        con.close()
    assert rows == [("carol", "40")]
