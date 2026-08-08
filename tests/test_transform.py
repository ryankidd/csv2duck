import pytest

from csv2duck.transform import ColumnTransform, TransformSpec, apply_transform


def test_apply_transform_renames_column():
    spec = TransformSpec(columns=[ColumnTransform(source="full_name", target="name")])

    result = apply_transform({"full_name": "alice", "age": "30"}, spec)

    assert result == {"name": "alice", "age": "30"}


def test_apply_transform_coerces_type():
    spec = TransformSpec(columns=[ColumnTransform(source="age", type="integer")])

    result = apply_transform({"name": "alice", "age": "30"}, spec)

    assert result == {"name": "alice", "age": 30}
    assert isinstance(result["age"], int)


def test_apply_transform_renames_and_coerces_together():
    spec = TransformSpec(
        columns=[ColumnTransform(source="yrs", target="age", type="integer")]
    )

    result = apply_transform({"yrs": "30"}, spec)

    assert result == {"age": 30}


def test_apply_transform_passes_through_unmentioned_columns():
    spec = TransformSpec(columns=[ColumnTransform(source="age", type="integer")])

    result = apply_transform({"name": "alice", "age": "30", "city": "nyc"}, spec)

    assert result == {"name": "alice", "age": 30, "city": "nyc"}


def test_apply_transform_ignores_missing_source_column():
    spec = TransformSpec(columns=[ColumnTransform(source="missing", type="integer")])

    result = apply_transform({"name": "alice"}, spec)

    assert result == {"name": "alice"}


def test_apply_transform_rejects_unknown_type():
    spec = TransformSpec(columns=[ColumnTransform(source="age", type="not-a-type")])

    with pytest.raises(ValueError, match="unknown transform type"):
        apply_transform({"age": "30"}, spec)


@pytest.mark.parametrize(
    "raw,expected",
    [("true", True), ("Yes", True), ("1", True), ("false", False), ("0", False)],
)
def test_apply_transform_coerces_boolean(raw, expected):
    spec = TransformSpec(columns=[ColumnTransform(source="active", type="boolean")])

    result = apply_transform({"active": raw}, spec)

    assert result == {"active": expected}
