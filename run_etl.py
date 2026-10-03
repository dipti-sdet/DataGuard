"""Run just the ETL and print row counts (good run, or with bugs).
   python run_etl.py          -> correct ETL
   python run_etl.py B3,B6    -> with planted bugs"""
import sys

from dataguard.pipeline import build

bugs = [b for b in (sys.argv[1] if len(sys.argv) > 1 else "").split(",") if b]
print("bugs:", bugs or "none")
con = build(upto=5, bugs=bugs)
for t in ["wrk_orders", "wrk_executions", "wrk_allocations", "etl_reject_log",
          "wrk_change_scope", "tgt_orders", "tgt_executions", "tgt_allocations"]:
    print(f"{t:18}{con.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]}")
