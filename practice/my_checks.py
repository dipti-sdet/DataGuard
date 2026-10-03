"""YOUR CHECKS. Replace each `raise NotImplementedError` with your own check, then run:
       python practice/check_my_work.py
A check receives `c` (connection + helpers) and returns (passed, detail).
Helpers:  c.rows(sql) -> list of rows   c.one(sql) -> single value   c.keys(sql) -> set of rows
          eq(actual, expected)          none(rows)  -> passes when rows is empty
Read practice/workbook.md for the hints on each exercise."""
from dataguard.checks import eq, none          # noqa: F401
from dataguard.pipeline import run_steps       # noqa: F401  (needed for P12)


def p01(c):
    """P01 Row count vs source: wrk_orders row count must equal the number of distinct
    (order_id, trade_date) in src_orders that pass the ETL filters. Compute expected from src."""
    raise NotImplementedError


def p02(c):
    """P02 Duplicates: no duplicate (key, trade_date, version) in tgt_orders / tgt_executions / tgt_allocations."""
    raise NotImplementedError


def p03(c):
    """P03 NULLs: client_name in wrk_orders is never NULL."""
    raise NotImplementedError


def p04(c):
    """P04 Mapping: no market_code OFFX left in wrk_executions_ver (it must become OTC)."""
    raise NotImplementedError


def p05(c):
    """P05 Source-to-target: price and qty in tgt_executions and tgt_allocations equal the source row (same id + trade_date)."""
    raise NotImplementedError


def p06(c):
    """P06 Missing records: list source (order_id, trade_date) that pass the filters but are NOT in wrk_orders. Must be empty."""
    raise NotImplementedError


def p07(c):
    """P07 Schema: tgt_executions.price is REAL, qty is INTEGER (use PRAGMA table_info)."""
    raise NotImplementedError


def p08(c):
    """P08 Domain: wrk_orders.status only contains NEW, OPEN, FILLED, CANCELLED or REJECTED."""
    raise NotImplementedError


def p09(c):
    """P09 Range: qty > 0 and price > 0 in wrk_allocations_ver."""
    raise NotImplementedError


def p10(c):
    """P10 Aggregate: SUM(qty) of wrk_executions_ver equals SUM(qty) of the src_executions rows whose parent order is in wrk_orders."""
    raise NotImplementedError


def p11(c):
    """P11 Ghost records: tgt_orders rows of the current batch (B5) that have no matching row in src_orders. Must be empty."""
    raise NotImplementedError


def p12(c):
    """P12 Incremental scenario: change order 1004, execution 105 and allocation 206 in the SOURCE to batch B6
    (order qty to 450), re-run the ETL (run_steps(c.con, 5, c.bugs)), then verify: order 1004 latest version = 4
    with qty 450, and exactly 1 new row was published in each target table."""
    raise NotImplementedError
