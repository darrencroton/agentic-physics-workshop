"""Tests for the explorer tool: loading, sampling, data.json and the HTML page."""
import json
import subprocess
import sys

import pytest

from explorer.__main__ import main
from explorer.data import ExplorerError, load, sample
from explorer.page import build_page

CSV = "name,a,b,c\nx,1,2.5,\ny,2,,foo\nz,3,4.5,bar\n"
SIDECAR = {"columns": {
    "name": {"numeric": False, "description": "Label"},
    "a": {"numeric": True, "unit": "kpc", "description": "Alpha", "log": True},
    "b": {"numeric": True, "unit": "", "description": "Beta", "log": False},
    "c": {"numeric": False, "description": "Text"},
}}


@pytest.fixture
def csv_path(tmp_path):
    path = tmp_path / "t.csv"
    path.write_text(CSV)
    return path


@pytest.fixture
def big_csv(tmp_path):
    path = tmp_path / "big.csv"
    path.write_text("id,v\n" + "".join(f"r{i},{i}\n" for i in range(200)))
    return path


def run_tool(*args):
    return subprocess.run([sys.executable, "-m", "explorer", *map(str, args)],
                          capture_output=True, text=True)


def test_numeric_detection_without_sidecar(csv_path):
    table = load(csv_path)
    assert [c["name"] for c in table.columns] == ["a", "b"]
    assert set(table.labels) == {"name", "c"}
    assert table.columns[0]["unit"] == "" and table.columns[0]["log"] is False


def test_numeric_detection_with_sidecar(csv_path):
    csv_path.with_suffix(".columns.json").write_text(json.dumps(SIDECAR))
    table = load(csv_path)
    assert [c["name"] for c in table.columns] == ["a", "b"]
    assert table.columns[0] == {"name": "a", "unit": "kpc", "description": "Alpha", "log": True}


def test_sidecar_overrides_detection(csv_path):
    sidecar = {"columns": {"a": {"numeric": False}}}
    csv_path.with_suffix(".columns.json").write_text(json.dumps(sidecar))
    assert "a" in load(csv_path).labels


def test_missing_counts_and_values(csv_path):
    table = load(csv_path)
    assert table.missing == {"a": 0, "b": 1, "c": 1, "name": 0}
    assert table.rows["b"] == [2.5, None, 4.5]
    assert table.n_read == 3


def test_non_finite_values_become_missing(tmp_path):
    path = tmp_path / "n.csv"
    path.write_text("a\n1\nnan\ninf\n")
    assert load(path).rows["a"] == [1.0, None, None]


def test_no_numeric_columns_is_an_error(tmp_path):
    path = tmp_path / "t.csv"
    path.write_text("a,b\nx,y\n")
    with pytest.raises(ExplorerError):
        load(path)


def test_sampling_size_and_determinism(big_csv):
    table = load(big_csv)
    first, second = sample(table, 50, 7), sample(table, 50, 7)
    assert first.n_rows == 50
    assert first.rows == second.rows and first.labels == second.labels
    assert len(set(first.labels["id"])) == 50
    assert sample(table, 50, 8).rows != first.rows
    assert sample(table, 500, 0).n_rows == 200


def test_data_json_is_strict_and_structured(big_csv, tmp_path):
    out = tmp_path / "out"
    result = run_tool(big_csv, "--out", out, "--max-points", 20)
    assert result.returncode == 0
    assert "n_read=200" in result.stdout and "n_written=20" in result.stdout

    def reject(token):
        raise ValueError(token)

    data = json.loads((out / "data.json").read_text(), parse_constant=reject)
    assert data["n_read"] == 200 and data["n_written"] == 20
    assert data["columns"][0]["name"] == "v"
    assert len(data["rows"]["v"]) == len(data["labels"]["id"]) == 20


def test_missing_values_written_as_null(csv_path, tmp_path):
    out = tmp_path / "out"
    assert run_tool(csv_path, "--out", out).returncode == 0
    data = json.loads((out / "data.json").read_text())
    assert data["rows"]["b"] == [2.5, None, 4.5]


def test_html_has_controls_options_and_inline_plotly(csv_path, tmp_path):
    out = tmp_path / "out"
    assert run_tool(csv_path, "--out", out).returncode == 0
    page = (out / "explorer.html").read_text()
    for control in ("x", "y", "z", "colour", "palette", "logx", "logy", "logz", "logc"):
        assert f'id="{control}"' in page
    for column in ("a", "b"):
        assert f'<option value="{column}">' in page
    assert page.count('<option value="none">') == 2
    assert "plotly.js v" in page and len(page) > 1_000_000
    assert '<script src="http' not in page
    assert "scattergl" in page and "scatter3d" in page and "Plotly.react" in page


def test_page_escapes_script_end_in_data():
    payload = {"source": "s", "n_read": 1, "n_written": 1,
               "columns": [{"name": "a", "unit": "", "description": "", "log": False}],
               "rows": {"a": [1.0]}, "labels": {"n": ["</script>"]}}
    assert build_page(payload, json.dumps(payload)).count("</script>") == 3


def test_list_prints_each_column(csv_path):
    result = run_tool(csv_path, "--list")
    assert result.returncode == 0
    assert "b\t\t\t1 missing" in result.stdout


def test_missing_file_exits_cleanly(tmp_path):
    result = run_tool(tmp_path / "nope.csv")
    assert result.returncode != 0
    assert "Traceback" not in result.stderr and result.stderr.strip()


def test_main_in_process_covers_errors_and_options(csv_path, big_csv, tmp_path, capsys):
    assert main([str(csv_path), "--list"]) == 0
    assert "a\tkpc" not in capsys.readouterr().out
    assert main([str(big_csv), "--out", str(tmp_path / "o"), "--max-points", "0"]) == 2
    assert "at least 1" in capsys.readouterr().err
    empty = tmp_path / "empty.csv"
    empty.write_text("")
    assert main([str(empty)]) == 2
    bad = tmp_path / "bad.csv"
    bad.write_text("a\n1\n")
    bad.with_suffix(".columns.json").write_text("{not json")
    assert main([str(bad)]) == 2
    assert "sidecar" in capsys.readouterr().err
    assert main([str(big_csv), "--out", str(tmp_path / "o"), "--seed", "3"]) == 0
    assert "n_written=200" in capsys.readouterr().out


def test_duplicate_column_names_are_an_error(tmp_path, capsys):
    path = tmp_path / "dup.csv"
    path.write_text("a,a\n1,2\n")
    assert main([str(path)]) == 2
    assert "duplicate column names: a" in capsys.readouterr().err
