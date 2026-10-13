"""Command line: python -m explorer DATA.csv [--out DIR] [--max-points N] [--seed S] [--list]."""
import argparse
import json
import sys
from pathlib import Path

from .data import ExplorerError, load, sample
from .page import build_page


def parse_args(argv):
    parser = argparse.ArgumentParser(
        prog="explorer", description="Write an interactive HTML explorer for a CSV file.")
    parser.add_argument("data", metavar="DATA.csv", help="CSV file with a header row")
    parser.add_argument("--out", default="out", help="output directory (default: out)")
    parser.add_argument("--max-points", type=int, default=20000,
                        help="most rows to write (default: 20000)")
    parser.add_argument("--seed", type=int, default=0, help="sampling seed (default: 0)")
    parser.add_argument("--list", action="store_true", help="list the columns and exit")
    return parser.parse_args(argv)


def list_columns(table):
    """Print name, unit, description and missing count for every column."""
    units = {col["name"]: col["unit"] for col in table.columns}
    for name in list(table.rows) + list(table.labels):
        print(f"{name}\t{units.get(name, '')}\t{table.descriptions.get(name, '')}"
              f"\t{table.missing[name]} missing")


def write_outputs(table, source, out_dir):
    """Write data.json (strict JSON) and explorer.html; return the number of rows written."""
    payload = {
        "source": source,
        "n_read": table.n_read,
        "n_written": table.n_rows,
        "columns": table.columns,
        "rows": table.rows,
        "labels": table.labels,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    blob = json.dumps(payload, allow_nan=False)
    (out_dir / "data.json").write_text(blob, encoding="utf-8")
    (out_dir / "explorer.html").write_text(build_page(payload, blob), encoding="utf-8")
    return table.n_rows


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        table = load(args.data)
        if args.list:
            list_columns(table)
            return 0
        n_read = table.n_read
        table = sample(table, args.max_points, args.seed)
        n_written = write_outputs(table, args.data, Path(args.out))
    except (ExplorerError, OSError, ValueError) as err:
        print(f"explorer: error: {err}", file=sys.stderr)
        return 2
    print(f"n_read={n_read} n_written={n_written}")
    print(f"wrote {Path(args.out) / 'explorer.html'} and {Path(args.out) / 'data.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
