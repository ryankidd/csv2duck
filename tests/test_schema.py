import json

import pytest
from pydantic import ValidationError

from csv2duck.schema import build_model, load_schema


def _write_schema(tmp_path, columns):
    path = tmp_path / "schema.json"
    path.write_text(json.dumps({"columns": columns}))
    return path


def test_load_schema_parses_columns(tmp_path):
    path = _write_schema(
        tmp_path,
        [{"name": "name", "type": "string"}, {"name": "age", "type": "integer"}],
    )

    columns = load_schema(path)

    assert [c.name for c in columns] == ["name", "age"]
    assert [c.type for c in columns] == ["string", "integer"]


def test_build_model_accepts_valid_row(tmp_path):
    path = _write_schema(
        tmp_path,
        [{"name": "name", "type": "string"}, {"name": "age", "type": "integer"}],
    )
    model = build_model(load_schema(path))

    row = model.model_validate({"name": "alice", "age": "30"})

    assert row.name == "alice"
    assert row.age == 30


def test_build_model_rejects_invalid_row(tmp_path):
    path = _write_schema(tmp_path, [{"name": "age", "type": "integer"}])
    model = build_model(load_schema(path))

    with pytest.raises(ValidationError):
        model.model_validate({"age": "not-a-number"})


def test_build_model_allows_missing_optional_column(tmp_path):
    path = _write_schema(
        tmp_path, [{"name": "nickname", "type": "string", "required": False}]
    )
    model = build_model(load_schema(path))

    row = model.model_validate({})

    assert row.nickname is None


def test_build_model_rejects_unknown_type(tmp_path):
    path = _write_schema(tmp_path, [{"name": "age", "type": "not-a-type"}])

    with pytest.raises(ValueError, match="unknown column type"):
        build_model(load_schema(path))
