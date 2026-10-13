# Data

Two frozen datasets for the Explorer exercise. Both are plain CSV (UTF-8, comma separated, empty field = missing value), each with a `.columns.json` sidecar. Regenerate them with `exercises/explorer/make_data.py` (needs network).

- `pulsars.csv`: every pulsar in the ATNF Pulsar Catalogue v2.9.0 (4,503 rows). `JNAME` is a text label; the other columns are numeric. Many pulsars lack a distance, a period derivative or the derived quantities, so missing values are common. Pulsars with no distance have empty `XX`, `YY`, `ZZ` (psrcat would place them at the Sun).
  - Source: https://www.atnf.csiro.au/research/pulsar/psrcat/
  - Cite: Manchester, Hobbs, Teoh & Hobbs 2005, AJ 129, 1993.
  - Licence: free to use with acknowledgement; CSIRO ATNF property (see the CSIRO Legal Notice on the catalogue site).
- `dimuons.csv`: the first 60,000 of the 100,000 dimuon events in the CMS Run2010B `Mu` dataset, one row per muon pair (energy, momentum, pt, eta, phi, charge for each muon, and the invariant mass `M`).
  - Source: https://opendata.cern.ch/record/700 (file `MuRun2010B.csv`).
  - Cite: McCauley, T. (2014), CERN Open Data Portal, DOI 10.7483/OPENDATA.CMS.CB8H.MFFA.
  - Licence: CC0.
- `<name>.columns.json`: `source`, `citation`, `licence` and `columns`, an object in CSV column order. Each column has `numeric` (true/false), `description`, and, for numeric columns, `unit` ("" if dimensionless) and `log` (a suggested log-scale default).
