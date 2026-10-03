"""Grades your checks in practice/my_checks.py.
   For each exercise: your check must PASS on the good ETL and FAIL on every bug listed for it.
     python practice/check_my_work.py                 # grade my_checks.py
     python practice/check_my_work.py --only P03      # one exercise
     python practice/check_my_work.py --solutions     # grade the reference solutions (peek only when stuck)"""
import argparse
import importlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from dataguard.bugs import ALL_BUGS  # noqa: E402
from dataguard.checks import Ctx  # noqa: E402
from dataguard.pipeline import build  # noqa: E402
from exercises import EXERCISES  # noqa: E402


def _norm(result):
    return (result, "") if isinstance(result, bool) else (bool(result[0]), result[1])


def grade(fn, ex):
    def run(bugs):
        return _norm(fn(Ctx(build(upto=ex.stage, bugs=bugs), bugs)))
    try:
        ok, detail = run(())
    except NotImplementedError:
        return "TODO", ""
    except Exception as e:
        return "ERROR", f"{type(e).__name__}: {e}"
    if not ok:
        return "FAILS ON GOOD RUN", str(detail)[:200]
    missed = []
    for bug in ex.catches:
        try:
            caught = not run((bug,))[0]
        except Exception:
            caught = True  # crashing on a broken run still counts as a failure signal
        if not caught:
            missed.append(bug)
    if missed:
        return "MISSED BUG", ", ".join(f"{b} ({ALL_BUGS[b]['what']})" for b in missed)
    return "PASS", ""


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    ap.add_argument("--solutions", action="store_true")
    args = ap.parse_args()
    mod = importlib.import_module("solutions" if args.solutions else "my_checks")
    done = 0
    for ex in EXERCISES:
        if args.only and ex.id != args.only.upper():
            continue
        status, msg = grade(getattr(mod, ex.id.lower()), ex)
        done += status == "PASS"
        print(f"{ex.id}  L{ex.level}  {status:18} {ex.title}")
        if msg:
            print(f"       -> {msg}")
    print(f"\n{done}/{len(EXERCISES) if not args.only else 1} exercises complete")
