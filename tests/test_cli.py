import json

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
