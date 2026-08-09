"""Reading rows from CSV or JSON input files."""

from __future__ import annotations

import csv
import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

_JSON_SUFFIXES = {".json", ".jsonl"}


def read_csv_rows(path: Path) -> Iterator[tuple[int, dict[str, Any]]]:
    """Yield (line_number, row) pairs from a CSV file, with the header as
    line 1."""
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        yield from enumerate(reader, start=2)


def read_json_rows(path: Path) -> Iterator[tuple[int, dict[str, Any]]]:
    """Yield (record_number, row) pairs from a JSON file.

    Accepts either a JSON array of objects, or newline-delimited JSON
    objects (one per line), picked based on whether the file starts with
    an array.
    """
    text = path.read_text()
    stripped = text.lstrip()
    if stripped.startswith("["):
        yield from enumerate(json.loads(stripped), start=1)
        return

    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        yield number, json.loads(line)


def read_rows(path: Path) -> Iterator[tuple[int, dict[str, Any]]]:
    """Yield (record_number, row) pairs from a CSV or JSON file, picking the
    format based on the file's suffix."""
    if path.suffix in _JSON_SUFFIXES:
        return read_json_rows(path)
    return read_csv_rows(path)
