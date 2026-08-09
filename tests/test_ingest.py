import json

from csv2duck.ingest import read_rows


def test_read_rows_reads_csv(tmp_path):
    path = tmp_path / "sample.csv"
    path.write_text("name,age\nalice,30\nbob,25\n")

    rows = list(read_rows(path))

    assert rows == [
        (2, {"name": "alice", "age": "30"}),
        (3, {"name": "bob", "age": "25"}),
    ]


def test_read_rows_reads_json_array(tmp_path):
    path = tmp_path / "sample.json"
    path.write_text(
        json.dumps([{"name": "alice", "age": 30}, {"name": "bob", "age": 25}])
    )

    rows = list(read_rows(path))

    assert rows == [
        (1, {"name": "alice", "age": 30}),
        (2, {"name": "bob", "age": 25}),
    ]


def test_read_rows_reads_ndjson(tmp_path):
    path = tmp_path / "sample.json"
    path.write_text('{"name": "alice", "age": 30}\n{"name": "bob", "age": 25}\n')

    rows = list(read_rows(path))

    assert rows == [
        (1, {"name": "alice", "age": 30}),
        (2, {"name": "bob", "age": 25}),
    ]


def test_read_rows_reads_ndjson_with_jsonl_suffix(tmp_path):
    path = tmp_path / "sample.jsonl"
    path.write_text('{"name": "alice"}\n{"name": "bob"}\n')

    rows = list(read_rows(path))

    assert rows == [(1, {"name": "alice"}), (2, {"name": "bob"})]


def test_read_rows_skips_blank_lines_in_ndjson(tmp_path):
    path = tmp_path / "sample.json"
    path.write_text('{"name": "alice"}\n\n{"name": "bob"}\n')

    rows = list(read_rows(path))

    assert rows == [(1, {"name": "alice"}), (3, {"name": "bob"})]
