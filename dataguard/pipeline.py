"""Builds the database, loads seed data and runs the ETL steps (optionally with bugs injected)."""
import sqlite3
from pathlib import Path

from .bugs import ALL_BUGS

ROOT = Path(__file__).resolve().parent.parent
SQL_DIR = ROOT / "sql"
STEPS = ["1_stage.sql", "2_orders.sql", "3_executions.sql", "4_allocations.sql", "5_publish.sql"]


def _inject(text, filename, bugs):
    """Apply every requested bug that targets this file (plain text replacement)."""
    for bug_id in bugs:
        bug = ALL_BUGS[bug_id]
        if bug["file"] == filename:
            assert bug["old"] in text, f"{bug_id}: text to replace not found in {filename}"
            text = text.replace(bug["old"], bug["new"])
    return text


def run_steps(con, upto=5, bugs=()):
    """Run ETL steps 1..upto on an existing connection (call twice to test re-runs)."""
    for step in STEPS[:upto]:
        con.executescript(_inject((SQL_DIR / "etl" / step).read_text(), step, bugs))
    con.commit()


def build(upto=5, bugs=(), db=":memory:"):
    """Fresh database + seed, then run steps 1..upto. upto=4 stops before publish, so the
    delta views still show what is about to be published."""
    con = sqlite3.connect(db)
    con.executescript(_inject((SQL_DIR / "schema.sql").read_text(), "schema.sql", bugs))
    con.executescript((SQL_DIR / "seed.sql").read_text())
    run_steps(con, upto, bugs)
    return con
