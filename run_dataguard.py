"""Run DataGuard: good ETL + every bug, all checks, then write the HTML report.
   python run_dataguard.py                      -> reports/dataguard_report.html
   python run_dataguard.py --report my.html"""
import argparse
from pathlib import Path

from dataguard.report import print_summary, render
from dataguard.runner import run_suite

ap = argparse.ArgumentParser()
ap.add_argument("--report", default="reports/dataguard_report.html")
args = ap.parse_args()

runs = run_suite()
print_summary(runs)
Path(args.report).parent.mkdir(parents=True, exist_ok=True)
render(runs, args.report)
print(f"\nReport written: {args.report}")
