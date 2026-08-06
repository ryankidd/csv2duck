from typer.testing import CliRunner

from csv2duck.cli import app

runner = CliRunner()


def test_ingest_reports_row_count(tmp_path):
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text("name,age\nalice,30\nbob,25\n")

    result = runner.invoke(app, [str(csv_path)])

    assert result.exit_code == 0
    assert "2 rows" in result.stdout
