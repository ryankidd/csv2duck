import duckdb

from csv2duck.load import load_rows


def test_load_rows_creates_table_with_rows(tmp_path):
    db_path = tmp_path / "out.duckdb"

    loaded = load_rows(
        db_path,
        "people",
        [{"name": "alice", "age": 30}, {"name": "bob", "age": 25}],
    )

    assert loaded == 2
    con = duckdb.connect(str(db_path))
    try:
        rows = con.execute("SELECT name, age FROM people ORDER BY name").fetchall()
    finally:
        con.close()
    assert rows == [("alice", 30), ("bob", 25)]


def test_load_rows_infers_duckdb_column_types(tmp_path):
    db_path = tmp_path / "out.duckdb"

    load_rows(db_path, "people", [{"name": "alice", "age": 30, "active": True}])

    con = duckdb.connect(str(db_path))
    try:
        columns = con.execute("DESCRIBE people").fetchall()
    finally:
        con.close()
    types = {name: column_type for name, column_type, *_ in columns}
    assert types == {"name": "VARCHAR", "age": "BIGINT", "active": "BOOLEAN"}


def test_load_rows_replaces_existing_table(tmp_path):
    db_path = tmp_path / "out.duckdb"

    load_rows(db_path, "people", [{"name": "alice", "age": 30}])
    load_rows(db_path, "people", [{"name": "carol", "age": 40}])

    con = duckdb.connect(str(db_path))
    try:
        rows = con.execute("SELECT name, age FROM people").fetchall()
    finally:
        con.close()
    assert rows == [("carol", 40)]


def test_load_rows_with_no_rows_returns_zero(tmp_path):
    db_path = tmp_path / "out.duckdb"

    loaded = load_rows(db_path, "people", [])

    assert loaded == 0
