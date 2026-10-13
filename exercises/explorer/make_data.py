#!/usr/bin/env python3
"""Build the two frozen Explorer datasets (facilitator tool, needs network).

Downloads the ATNF Pulsar Catalogue (psrcat web query, "long csv with errors"
style for full precision) and the CMS Run2010B dimuon CSV (CERN Open Data
record 700), cleans them, and writes pulsars.csv, dimuons.csv and a
<name>.columns.json sidecar for each. Standard library only; the output is
deterministic for a given catalogue version.
"""

import argparse
import csv
import io
import json
import math
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

PSRCAT_URL = "https://www.atnf.csiro.au/research/pulsar/psrcat/"
PSRCAT_QUERY_URL = PSRCAT_URL + "proc_form.php"
CMS_RECORD_URL = "https://opendata.cern.ch/record/700"
CMS_FILE_URL = CMS_RECORD_URL + "/files/MuRun2010B.csv"
# Raw CMS files larger than this are cut to CMS_KEEP_ROWS rows.
CMS_MAX_RAW_BYTES = 12 * 1000 * 1000
CMS_KEEP_ROWS = 60000

# (psrcat query name, psrcat header name, output name, unit, description, log)
PULSAR_COLUMNS = [
    ("JName", "PSRJ", "JNAME", None, "Pulsar name (J2000)", None),
    ("GL", "GL", "GL", "deg", "Galactic longitude", False),
    ("GB", "GB", "GB", "deg", "Galactic latitude", False),
    ("Dist", "DIST", "DIST", "kpc", "Best distance estimate", True),
    ("Dist_DM", "DIST_DM", "DIST_DM", "kpc", "Distance from DM (YMW16)", True),
    ("XX", "XX", "XX", "kpc", "Galactocentric X (Sun at 0, 8.5, 0)", False),
    ("YY", "YY", "YY", "kpc", "Galactocentric Y (Sun at 0, 8.5, 0)", False),
    ("ZZ", "ZZ", "ZZ", "kpc", "Galactocentric Z, towards north pole", False),
    ("P0", "P0", "P0", "s", "Spin period", True),
    ("P1", "P1", "P1", "", "Period derivative (s/s)", True),
    ("DM", "DM", "DM", "cm^-3 pc", "Dispersion measure", True),
    ("Age", "AGE", "AGE", "yr", "Characteristic age P/(2 Pdot)", True),
    ("BSurf", "BSURF", "BSURF", "G", "Surface magnetic field", True),
    ("Edot", "EDOT", "EDOT", "erg/s", "Spin-down luminosity", True),
]

# (CMS header name, unit, description, log)
DIMUON_COLUMNS = [
    ("E1", "GeV", "Muon 1 energy", True),
    ("px1", "GeV", "Muon 1 momentum x", False),
    ("py1", "GeV", "Muon 1 momentum y", False),
    ("pz1", "GeV", "Muon 1 momentum z", False),
    ("pt1", "GeV", "Muon 1 transverse momentum", True),
    ("eta1", "", "Muon 1 pseudorapidity", False),
    ("phi1", "rad", "Muon 1 azimuthal angle", False),
    ("Q1", "e", "Muon 1 charge", False),
    ("E2", "GeV", "Muon 2 energy", True),
    ("px2", "GeV", "Muon 2 momentum x", False),
    ("py2", "GeV", "Muon 2 momentum y", False),
    ("pz2", "GeV", "Muon 2 momentum z", False),
    ("pt2", "GeV", "Muon 2 transverse momentum", True),
    ("eta2", "", "Muon 2 pseudorapidity", False),
    ("phi2", "rad", "Muon 2 azimuthal angle", False),
    ("Q2", "e", "Muon 2 charge", False),
    ("M", "GeV", "Dimuon invariant mass", True),
]
CMS_EXPECTED_HEADER = (
    "Run,Event,type1,E1,px1,py1,pz1,pt1,eta1,phi1,Q1,"
    "type2,E2,px2,py2,pz2,pt2,eta2,phi2,Q2,M"
).split(",")


class DataError(Exception):
    """Raised when a download does not look like the expected data."""


def fetch(url, params=None, retries=3, timeout=300):
    """Return the body of url as bytes, retrying on transient errors."""
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"User-Agent": "explorer-make-data/1.0"})
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read()
        except (urllib.error.URLError, OSError) as exc:
            print("  attempt %d/%d failed: %s" % (attempt, retries, exc), file=sys.stderr)
            if attempt == retries:
                raise DataError("could not download %s" % url) from exc
            time.sleep(5 * attempt)


def cached_fetch(url, cache_dir, name, **kwargs):
    """fetch(), reading from and writing to cache_dir/name when cache_dir is set."""
    if cache_dir:
        path = Path(cache_dir) / name
        if path.exists():
            print("  using cached %s" % path)
            return path.read_bytes()
    body = fetch(url, **kwargs)
    if cache_dir:
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        (Path(cache_dir) / name).write_bytes(body)
    return body


def clean_number(token, where):
    """Return token unchanged if it is a finite number, "" if missing."""
    token = token.strip()
    if token in ("", "*"):
        return ""
    try:
        value = float(token)
    except ValueError:
        raise DataError("%s: not a number: %r" % (where, token)) from None
    if not math.isfinite(value):
        raise DataError("%s: non-finite value: %r" % (where, token))
    return token


def pulsar_query():
    """Query parameters for the psrcat table of every pulsar."""
    params = {"version": "", "startUserDefined": "true"}
    for query_name, _, _, _, _, _ in PULSAR_COLUMNS:
        params[query_name] = query_name
    params.update({
        "ephemeris": "long csv with errors",
        "style": "Long csv with errors",
        "coords_unit": "raj/decj",
        "sort_attr": "jname",
        "sort_order": "asc",
        "no_value": "*",
        "x_scale": "linear",
        "y_scale": "linear",
        "state": "query",
    })
    return params


def parse_pulsars(html):
    """Return (catalogue version, header names, rows) from a psrcat page."""
    text = html.decode("iso-8859-1")
    version = re.search(r"Catalogue Version:\s*([0-9][0-9.]*)", text)
    if not version:
        raise DataError("catalogue version not found in psrcat response")
    pre = re.search(r"<pre>(.*?)</pre>", text, re.S)
    if not pre:
        raise DataError("no <pre> table in psrcat response")
    lines = [ln.rstrip() for ln in pre.group(1).splitlines() if ln.strip()]
    if not lines or not lines[0].startswith("#;"):
        raise DataError("unexpected psrcat table header")
    header = [h.strip().upper() for h in lines[0].split(";")]
    rows = []
    for line in lines[2:]:
        fields = line.split(";")
        if not re.match(r"^\d+$", fields[0]):
            continue
        if len(fields) != len(header):
            raise DataError("psrcat row has %d fields, header %d: %s" % (len(fields), len(header), line[:80]))
        rows.append(fields)
    return version.group(1), header, rows


def blank_unplaced_position(record, row, header, name):
    """Blank XX, YY, ZZ when DIST is missing.

    psrcat reports (0, 8.5, 0), the Sun, for a pulsar with no distance. That
    is not a measurement, so it is replaced by missing values.
    """
    if record["DIST"] != "":
        return
    position = [float(record[k]) for k in ("XX", "YY", "ZZ") if record[k] != ""]
    if position and (len(position) != 3 or abs(position[0]) > 1e-3
                     or abs(position[1] - 8.5) > 1e-3 or abs(position[2]) > 1e-3):
        raise DataError("%s: no DIST but XX, YY, ZZ are not the Sun: %s" % (name, position))
    for key in ("XX", "YY", "ZZ"):
        row[header.index(key)] = ""


def build_pulsars(cache_dir):
    """Download and clean the pulsar table; return (version, header, rows)."""
    print("Pulsars: querying psrcat ...")
    params = pulsar_query()
    version_page = fetch(PSRCAT_URL)
    match = re.search(rb"Catalogue Version\s*([0-9][0-9.]*)", version_page)
    if not match:
        raise DataError("could not read the current catalogue version")
    params["version"] = match.group(1).decode()
    body = cached_fetch(PSRCAT_QUERY_URL, cache_dir, "psrcat_%s.html" % params["version"], params=params)
    version, header, raw_rows = parse_pulsars(body)
    if version != params["version"]:
        raise DataError("catalogue version mismatch: %s vs %s" % (version, params["version"]))
    out_header = [col[2] for col in PULSAR_COLUMNS]
    index = {}
    for col in PULSAR_COLUMNS:
        # Error and reference columns have empty names, so names are unique.
        if header.count(col[1]) != 1:
            raise DataError("psrcat column %s found %d times" % (col[1], header.count(col[1])))
        index[col[2]] = header.index(col[1])
    rows = []
    seen = set()
    for fields in raw_rows:
        name = fields[index["JNAME"]].strip()
        if not name or name in seen:
            raise DataError("missing or duplicate pulsar name: %r" % name)
        seen.add(name)
        row = [name]
        for col in PULSAR_COLUMNS[1:]:
            row.append(clean_number(fields[index[col[2]]], "%s %s" % (name, col[2])))
        blank_unplaced_position(dict(zip(out_header, row)), row, out_header, name)
        rows.append(row)
    if len(rows) < 3000:
        raise DataError("only %d pulsars returned; expected thousands" % len(rows))
    return version, out_header, rows


def parse_dimuons(raw):
    """Return (rows as lists of strings in DIMUON_COLUMNS order) from raw CSV bytes."""
    reader = csv.reader(io.StringIO(raw.decode("utf-8")))
    header = [h.strip().lower() for h in next(reader)]
    if header != [h.lower() for h in CMS_EXPECTED_HEADER]:
        raise DataError("unexpected CMS columns: %s" % header)
    index = [header.index(col[0].lower()) for col in DIMUON_COLUMNS]
    rows = []
    for number, fields in enumerate(reader, start=2):
        if len(fields) != len(header):
            raise DataError("CMS line %d has %d fields" % (number, len(fields)))
        rows.append([clean_number(fields[i], "CMS line %d %s" % (number, header[i])) for i in index])
    return rows


def build_dimuons(cache_dir):
    """Download and clean the dimuon table; return (rows, truncated, raw size)."""
    print("Dimuons: downloading CMS record 700 (about 15 MB) ...")
    raw = cached_fetch(CMS_FILE_URL, cache_dir, "MuRun2010B.csv")
    rows = parse_dimuons(raw)
    truncated = len(raw) > CMS_MAX_RAW_BYTES
    if truncated:
        rows = rows[:CMS_KEEP_ROWS]
    return rows, truncated, len(raw)


def write_csv(path, header, rows):
    """Write header and rows as UTF-8 CSV with LF line endings."""
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def write_sidecar(path, source, citation, licence, columns):
    """Write the <name>.columns.json sidecar; columns is an ordered dict."""
    sidecar = {"source": source, "citation": citation, "licence": licence, "columns": columns}
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(sidecar, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def pulsar_sidecar(version):
    columns = {}
    for _, _, name, unit, description, log in PULSAR_COLUMNS:
        if unit is None:
            columns[name] = {"numeric": False, "description": description}
        else:
            columns[name] = {"numeric": True, "unit": unit, "description": description, "log": log}
    return {
        "source": "ATNF Pulsar Catalogue v%s, %s" % (version, PSRCAT_URL),
        "citation": "Manchester, Hobbs, Teoh & Hobbs 2005, AJ 129, 1993",
        "licence": ("Free to use with acknowledgement (cite Manchester et al. 2005); "
                    "CSIRO ATNF property, see the CSIRO Legal Notice on the catalogue site"),
        "columns": columns,
    }


def dimuon_sidecar(truncated):
    columns = {
        name: {"numeric": True, "unit": unit, "description": description, "log": log}
        for name, unit, description, log in DIMUON_COLUMNS
    }
    source = ("CMS Run2010B dimuon events, CERN Open Data record 700, %s (MuRun2010B.csv)"
              % CMS_RECORD_URL)
    if truncated:
        source += ", first %d of 100000 rows" % CMS_KEEP_ROWS
    return {
        "source": source,
        "citation": ("McCauley, T. (2014). Dimuon event information derived from the Run2010B "
                     "public Mu dataset. CERN Open Data Portal, DOI 10.7483/OPENDATA.CMS.CB8H.MFFA"),
        "licence": "CC0 1.0",
        "columns": columns,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Download and clean the ATNF pulsar catalogue and the CMS Run2010B "
                    "dimuon events; write the CSVs and column sidecars for the Explorer exercise.")
    parser.add_argument("--out", default=str(Path(__file__).resolve().parent / "level0" / "data"),
                        help="output directory (default: level0/data next to this script)")
    parser.add_argument("--cache-dir", default=None,
                        help="optional directory to keep (and reuse) the raw downloads")
    parser.add_argument("--only", choices=("pulsars", "dimuons"), default=None,
                        help="build just one dataset")
    args = parser.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    try:
        if args.only in (None, "pulsars"):
            version, header, rows = build_pulsars(args.cache_dir)
            write_csv(out / "pulsars.csv", header, rows)
            sidecar = pulsar_sidecar(version)
            write_sidecar(out / "pulsars.columns.json", sidecar["source"], sidecar["citation"],
                          sidecar["licence"], sidecar["columns"])
            print("  wrote pulsars.csv: %d rows (catalogue v%s)" % (len(rows), version))
        if args.only in (None, "dimuons"):
            rows, truncated, raw_size = build_dimuons(args.cache_dir)
            write_csv(out / "dimuons.csv", [c[0] for c in DIMUON_COLUMNS], rows)
            sidecar = dimuon_sidecar(truncated)
            write_sidecar(out / "dimuons.columns.json", sidecar["source"], sidecar["citation"],
                          sidecar["licence"], sidecar["columns"])
            print("  wrote dimuons.csv: %d rows (raw file %d bytes%s)"
                  % (len(rows), raw_size, ", truncated" if truncated else ""))
    except DataError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
