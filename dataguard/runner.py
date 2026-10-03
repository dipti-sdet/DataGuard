"""Runs every check against the good ETL and against each bug."""
from .bugs import BUGS
from .checks import CHECKS, Ctx
from .pipeline import build


def run_checks(bugs=()):
    """Returns {check_id: (passed, detail)}. A check that crashes counts as a failure."""
    cache, results = {}, {}
    for chk in CHECKS:
        try:
            if chk.stage not in cache:
                cache[chk.stage] = build(upto=chk.stage, bugs=bugs)
            ok, detail = chk.fn(Ctx(cache[chk.stage], bugs))
        except Exception as e:  # SQL error, missing table... all count as "detected"
            ok, detail = False, f"ERROR {type(e).__name__}: {e}"
        results[chk.id] = (bool(ok), detail)
    return results


def run_suite():
    """GOOD run + one run per bug. Returns [(name, bugs_tuple, results)]."""
    runs = [("GOOD", (), run_checks(()))]
    runs += [(bug_id, (bug_id,), run_checks((bug_id,))) for bug_id in BUGS]
    return runs
