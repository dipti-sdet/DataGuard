# DataGuard

SQL-based validation framework for an incremental ETL (source -> work tables -> versioned delta -> published target),
inspired by a production-style trading-data pipeline. Python + SQLite + pytest, no installs beyond pytest.

- **One correct ETL** (`sql/etl/`, 5 steps) and **10 planted bugs** (`dataguard/bugs.py`), one per common ETL defect type
- **38 checks** (`dataguard/checks.py`): row counts, reconciliation, filters, boundaries, duplicates, NULLs, referential integrity,
  transformations, business rules, versioning, delta, publish/scope, source-to-target match, idempotency
- **A report** showing every check on the good run and on every bug: `reports/dataguard_report.html`

## Run
    python -m venv .venv
    .venv\Scripts\activate            (macOS/Linux: source .venv/bin/activate)
    pip install -r requirements.txt
    python run_etl.py                 # correct ETL, prints row counts
    python run_etl.py B3              # with a planted bug
    python run_dataguard.py           # runs everything, writes the HTML report
    pytest                            # good run must pass all checks; every bug must be detected
    Full setup guide: docs/setup.md
    
## Add your own
- **New check:** copy any function in `dataguard/checks.py`, give it a new id, SQL and expected value.
- **New bug:** add an entry in `dataguard/bugs.py` (file, old text, new text, detector check ids).
  `pytest` then proves your checks catch it.

## Learn by practising
`practice/workbook.md` has 12 exercises. You write checks in `practice/my_checks.py`; run `python practice/check_my_work.py`
and the grader tells you whether each check passes on the good ETL and catches its bug.

Docs: `docs/process_map.md` (flow), `docs/validation_checklist.md` (22 check types), `docs/design.md` (seed data, bugs).

See `docs/design.md` for the data flow, seed data and catalogues.
