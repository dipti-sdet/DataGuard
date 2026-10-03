"""Reference solutions. Try each exercise yourself for 15 minutes before looking here."""
from dataguard.checks import eq, none
from dataguard.pipeline import run_steps

_ORDER_FILTERS = """venue IN ('VEN_A','VEN_B','VEN_C') AND instrument_type IN ('FUT','OPT','SPREAD')
    AND source_system IN ('SYS1','SYS2') AND event_type IN ('NEW','AMEND','CANCEL')
    AND trade_date BETWEEN '2024-01-14' AND '2024-01-15'"""


def p01(c):
    expected = c.one(f"SELECT COUNT(*) FROM (SELECT DISTINCT order_id, trade_date FROM src_orders WHERE {_ORDER_FILTERS})")
    return eq(c.one("SELECT COUNT(*) FROM wrk_orders"), expected)


def p02(c):
    d = (c.rows("SELECT order_id, trade_date, order_version FROM tgt_orders GROUP BY 1, 2, 3 HAVING COUNT(*) > 1")
         + c.rows("SELECT exec_id, trade_date, exec_version FROM tgt_executions GROUP BY 1, 2, 3 HAVING COUNT(*) > 1")
         + c.rows("SELECT alloc_id, trade_date, alloc_version FROM tgt_allocations GROUP BY 1, 2, 3 HAVING COUNT(*) > 1"))
    return none(d, "duplicate target rows")


def p03(c):
    return eq(c.one("SELECT COUNT(*) FROM wrk_orders WHERE client_name IS NULL"), 0)


def p04(c):
    return none(c.rows("SELECT exec_id FROM wrk_executions_ver WHERE market_code = 'OFFX'"), "unmapped executions")


def p05(c):
    bad = (c.rows("""SELECT 'exec', t.exec_id FROM tgt_executions t JOIN src_executions s
                     ON s.exec_id = t.exec_id AND s.trade_date = t.trade_date
                     WHERE t.qty <> s.qty OR t.price <> s.price""")
           + c.rows("""SELECT 'alloc', t.alloc_id FROM tgt_allocations t JOIN src_allocations s
                       ON s.alloc_id = t.alloc_id AND s.trade_date = t.trade_date
                       WHERE t.qty <> s.qty OR t.price <> s.price"""))
    return none(bad, "target differs from source")


def p06(c):
    missing = c.rows(f"""SELECT DISTINCT order_id, trade_date FROM src_orders WHERE {_ORDER_FILTERS}
                         EXCEPT SELECT order_id, trade_date FROM wrk_orders""")
    return none(missing, "source orders missing from work table")


def p07(c):
    types = {r[1]: r[2] for r in c.rows("PRAGMA table_info(tgt_executions)")}
    return eq((types.get("price"), types.get("qty")), ("REAL", "INTEGER"))


def p08(c):
    bad = c.rows("SELECT DISTINCT status FROM wrk_orders WHERE status NOT IN ('NEW','OPEN','FILLED','CANCELLED','REJECTED')")
    return none(bad, "status values outside the allowed set")


def p09(c):
    return none(c.rows("SELECT alloc_id, qty, price FROM wrk_allocations_ver WHERE qty <= 0 OR price <= 0"), "out-of-range rows")


def p10(c):
    expected = c.one("""SELECT SUM(e.qty) FROM src_executions e WHERE EXISTS
                        (SELECT 1 FROM wrk_orders o WHERE o.order_id = e.order_id AND o.trade_date = e.trade_date)""")
    return eq(c.one("SELECT SUM(qty) FROM wrk_executions_ver"), expected)


def p11(c):
    ghosts = c.rows("""SELECT t.order_id, t.trade_date FROM tgt_orders t LEFT JOIN src_orders s
                       ON s.order_id = t.order_id AND s.trade_date = t.trade_date
                       WHERE t.source_batch_id = 'B5' AND s.order_id IS NULL""")
    return none(ghosts, "target rows with no source")


def p12(c):
    con = c.con
    con.execute("UPDATE src_orders SET source_batch_id = 'B6', qty = 450 WHERE order_id = 1004 AND trade_date = '2024-01-15'")
    con.execute("UPDATE src_executions SET source_batch_id = 'B6' WHERE exec_id = 105")
    con.execute("UPDATE src_allocations SET source_batch_id = 'B6' WHERE alloc_id = 206")
    con.commit()
    tables = ("tgt_orders", "tgt_executions", "tgt_allocations")
    before = {t: c.one(f"SELECT COUNT(*) FROM {t}") for t in tables}
    run_steps(con, 5, c.bugs)
    new_rows = {t: c.one(f"SELECT COUNT(*) FROM {t}") - before[t] for t in tables}
    latest = c.rows("SELECT order_version, qty FROM tgt_orders WHERE order_id = 1004 ORDER BY order_version DESC LIMIT 1")
    ok = latest == [(4, 450)] and all(n == 1 for n in new_rows.values())
    return ok, f"latest (version, qty) {latest}, new rows per table {new_rows}"
