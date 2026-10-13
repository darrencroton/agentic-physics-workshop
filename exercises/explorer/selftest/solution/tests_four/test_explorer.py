"""Four tests only: too few to pass the Level 2 gate."""
import subprocess
import sys

from explorer.data import load, sample

CSV = "name,a,b\nx,1,2.5\ny,2,\nz,3,4.5\n"


def make_csv(tmp_path):
    path = tmp_path / "t.csv"
    path.write_text(CSV)
    return path


def test_numeric_detection(tmp_path):
    assert [c["name"] for c in load(make_csv(tmp_path)).columns] == ["a", "b"]


def test_missing_counts(tmp_path):
    assert load(make_csv(tmp_path)).missing["b"] == 1


def test_sampling_size(tmp_path):
    assert sample(load(make_csv(tmp_path)), 2, 0).n_rows == 2


def test_missing_file_exits_cleanly(tmp_path):
    result = subprocess.run([sys.executable, "-m", "explorer", str(tmp_path / "x.csv")],
                            capture_output=True, text=True)
    assert result.returncode != 0 and "Traceback" not in result.stderr
