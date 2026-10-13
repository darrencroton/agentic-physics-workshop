"""Load a CSV (with optional columns.json sidecar), classify columns, sample rows."""
import csv
import json
import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np


class ExplorerError(Exception):
    """A problem the user can fix; reported without a traceback."""


@dataclass
class Table:
    """Parsed data: numeric columns hold floats or None, labels hold strings."""

    columns: list = field(default_factory=list)
    rows: dict = field(default_factory=dict)
    labels: dict = field(default_factory=dict)
    missing: dict = field(default_factory=dict)
    descriptions: dict = field(default_factory=dict)
    n_read: int = 0

    @property
    def n_rows(self):
        return len(next(iter(self.rows.values())))


def parse_float(text):
    """Return a finite float, None for an empty or non-finite value; ValueError if not a number."""
    text = text.strip()
    if not text:
        return None
    value = float(text)
    return value if math.isfinite(value) else None


def read_sidecar(path):
    """Return the sidecar's column metadata, or {} when there is no sidecar."""
    sidecar = Path(path).with_suffix(".columns.json")
    if not sidecar.is_file():
        return {}
    try:
        return json.loads(sidecar.read_text(encoding="utf-8"))["columns"]
    except (OSError, ValueError, KeyError, TypeError) as err:
        raise ExplorerError(f"cannot read sidecar {sidecar}: {err}")


def is_numeric(values):
    """True when there is a non-empty value and every non-empty one parses as a float."""
    seen = False
    for text in values:
        if not text.strip():
            continue
        try:
            float(text)
        except ValueError:
            return False
        seen = True
    return seen


def load(path):
    """Read a CSV file into a Table."""
    path = Path(path)
    try:
        with open(path, newline="", encoding="utf-8-sig") as handle:
            records = list(csv.reader(handle))
    except (OSError, UnicodeDecodeError, csv.Error) as err:
        raise ExplorerError(f"cannot read {path}: {err}")
    if not records or not any(name.strip() for name in records[0]):
        raise ExplorerError(f"{path} has no header row")
    header, body = [name.strip() for name in records[0]], records[1:]
    duplicates = sorted({name for name in header if header.count(name) > 1})
    if duplicates:
        raise ExplorerError(f"{path} has duplicate column names: {', '.join(duplicates)}")
    meta = read_sidecar(path)
    table = Table(n_read=len(body))
    for index, name in enumerate(header):
        raw = [row[index] if index < len(row) else "" for row in body]
        info = meta.get(name, {})
        numeric = info["numeric"] if "numeric" in info else is_numeric(raw)
        table.descriptions[name] = info.get("description", "")
        if numeric:
            values = []
            for text in raw:
                try:
                    values.append(parse_float(text))
                except ValueError:
                    values.append(None)
            table.missing[name] = values.count(None)
            table.rows[name] = values
            table.columns.append({
                "name": name,
                "unit": info.get("unit", ""),
                "description": info.get("description", ""),
                "log": bool(info.get("log", False)),
            })
        else:
            table.missing[name] = sum(1 for text in raw if not text.strip())
            table.labels[name] = [text.strip() for text in raw]
    if not table.columns:
        raise ExplorerError(f"{path} has no numeric columns")
    if table.n_read == 0:
        raise ExplorerError(f"{path} has no data rows")
    return table


def sample(table, max_points, seed):
    """Keep at most max_points rows, chosen without replacement, in original order."""
    if max_points < 1:
        raise ExplorerError("--max-points must be at least 1")
    if table.n_rows <= max_points:
        return table
    keep = np.sort(np.random.default_rng(seed).choice(
        table.n_rows, size=max_points, replace=False))

    def pick(values):
        return [values[i] for i in keep]

    return Table(
        columns=table.columns,
        rows={name: pick(values) for name, values in table.rows.items()},
        labels={name: pick(values) for name, values in table.labels.items()},
        missing=table.missing,
        descriptions=table.descriptions,
        n_read=table.n_read,
    )
