# Practice workbook: learn to write ETL checks

You write the checks in `practice/my_checks.py`. The grader tells you if each one is any good.

    python practice/check_my_work.py              # grade everything
    python practice/check_my_work.py --only P03   # one exercise

A check must **PASS on the good ETL** and **FAIL on the bug(s)** listed. Status meanings:
`TODO` not written | `FAILS ON GOOD RUN` your check is too strict or wrong | `MISSED BUG` your check is blind to that bug | `PASS` done.

**To look at data while you work** (change the stage number, table and bug):

    python -c "from dataguard.pipeline import build; con=build(upto=1); print(con.execute('SELECT * FROM wrk_orders').fetchall())"
    python -c "from dataguard.pipeline import build; con=build(upto=1, bugs=('B2',)); print(con.execute('SELECT * FROM wrk_orders').fetchall())"

Stuck 15 minutes? Look at the pattern below, then `solutions.py`. Always re-write it yourself after reading.

Helpers in a check: `c.rows(sql)`, `c.one(sql)`, `c.keys(sql)`, `eq(actual, expected)`, `none(rows)`.

---
## Level 1: basics (these catch the 10 report bugs)

**P01 Row count vs source** | after step 1 | must catch B1, B2, B10
Count rows in `wrk_orders` and compare with a count computed from `src_orders` using the same filters as `1_stage.sql`.
```
expected = c.one("SELECT COUNT(*) FROM (SELECT DISTINCT order_id, trade_date FROM src_orders WHERE <filters from 1_stage.sql>)")
return eq(c.one("SELECT COUNT(*) FROM wrk_orders"), expected)
```
Why: a hardcoded 5 passes today and lies tomorrow. Counting from the source keeps the check honest.

**P02 Duplicates** | after step 5 | must catch B3
`GROUP BY order_id, trade_date, order_version HAVING COUNT(*) > 1` on each target table; combine the results and return `none(rows)`.

**P03 NULL check** | after step 1 | must catch B8
Count rows where `client_name IS NULL`; expect 0. Run it on B8 and look at which orders are NULL.

**P04 Mapping** | after step 3 | must catch B6
Select executions that still have market_code `OFFX`. An unmapped value left behind is the easiest way to test a mapping.

**P05 Source-to-target match** | after step 5 | must catch B7, B9
Join `tgt_executions` to `src_executions` on exec_id AND trade_date; select rows where qty or price differ. Same for allocations.
```
SELECT t.exec_id FROM tgt_executions t JOIN src_executions s ON s.exec_id = t.exec_id AND s.trade_date = t.trade_date
WHERE t.qty <> s.qty OR t.price <> s.price
```
Why join on trade_date too: history rows exist for other dates. Hint for later: `<>` ignores NULLs, so for nullable columns compare with `IS NOT`.

**P06 Missing records** | after step 1 | must catch B1, B2, B10
`source keys passing the filters EXCEPT work keys` must be empty. Unlike a count, this tells you WHICH order is missing, and it cannot be fooled by one missing row plus one extra row.

---
## Level 2: new check types (each has its own bug, X1-X5)

**P07 Schema check** | after step 5 | must catch X1
`c.rows("PRAGMA table_info(tgt_executions)")` returns `(cid, name, type, notnull, default, pk)`. Build a dict `{name: type}` and compare the types you care about with what the design says.

**P08 Domain check** | after step 1 | must catch X2
`SELECT DISTINCT status FROM wrk_orders WHERE status NOT IN (<allowed list>)`. Allowed: NEW, OPEN, FILLED, CANCELLED, REJECTED. Notice: it is case sensitive, which is the point.

**P09 Range check** | after step 4 | must catch X3
`wrk_allocations_ver` rows where `qty <= 0 OR price <= 0`. Return the offenders.

**P10 Aggregate check** | after step 3 | must catch X4
Expected: `SUM(qty)` of the source executions whose parent order is in `wrk_orders` (use `EXISTS`). Actual: `SUM(qty)` of `wrk_executions_ver`. Why SUM and not COUNT: this bug changes values, not row counts, so P01-style checks never notice.

**P11 Ghost records** | after step 5 | must catch X5
Target orders with no source row: `tgt_orders LEFT JOIN src_orders ... WHERE s.order_id IS NULL`. Careful: older history rows legitimately exist only in the target. Limit the check to the current batch (`source_batch_id = 'B5'`).

---
## Level 3: scenario test

**P12 Incremental scenario** | after step 5 | must catch B5, X6
This is a stateful test: change the source, re-run, check the result.
1. Update `src_orders` order 1004 (trade_date 2024-01-15): `source_batch_id = 'B6'`, `qty = 450`. Update `src_executions` exec 105 and `src_allocations` alloc 206 to batch `B6`. Commit.
2. Count rows in the three target tables.
3. Re-run: `run_steps(c.con, 5, c.bugs)`.
4. Check: the newest `tgt_orders` row for 1004 has version 4 and qty 450, and each target table gained exactly 1 row.

Why this matters: the real pipeline is incremental, and the bugs that hurt are the ones that only show when data changes between runs.

---
## When you finish
- `python practice/check_my_work.py` shows 12/12.
- Add 3 checks of your own to `dataguard/checks.py` and 1 bug of your own to `dataguard/bugs.py` (see README), then run `python run_dataguard.py` and look at your bug in the report.
