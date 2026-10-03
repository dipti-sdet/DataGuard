"""The validation checks. Each check: runs after ETL step `stage`, returns (passed, detail).
To add a check: copy one of the functions below, change the id/title/SQL/expected value."""
from dataclasses import dataclass
from typing import Callable

from .pipeline import build, run_steps

D14, D15 = "2024-01-14", "2024-01-15"


@dataclass
class Check:
    id: str
    category: str
    title: str
    stage: int          # ETL step after which the check runs (4 = before publish, 5 = after)
    fn: Callable


CHECKS = []


def check(cid, category, title, stage):
    def deco(fn):
        CHECKS.append(Check(cid, category, title, stage, fn))
        return fn
    return deco


class Ctx:
    """What a check receives: a DB connection plus small query helpers."""
    def __init__(self, con, bugs=()):
        self.con, self.bugs = con, bugs

    def rows(self, sql):
        return self.con.execute(sql).fetchall()

    def one(self, sql):
        return self.con.execute(sql).fetchone()[0]

    def keys(self, sql):
        return set(self.rows(sql))

    def fresh(self, upto):
        return build(upto=upto, bugs=self.bugs)


def eq(actual, expected):
    return actual == expected, f"expected {expected}, got {actual}"


def none(rows, what="offending rows"):
    return rows == [], f"{what}: {rows}"


RC, FL, DU, DD, NL, RI, TR, BR, VR, DF, PB, ST, ID = (
    "Row counts & reconciliation", "Filters & boundaries", "Duplicates", "Dedup / latest record",
    "NULLs & defaults", "Referential integrity", "Transformations", "Business rules",
    "Versioning", "Delta (diff)", "Publish & scope", "Source-to-target match", "Idempotency")

# ---------------------------------------------------------------- STEP 1 (stage)
@check("RC01", RC, "Work orders row count = 5", 1)
def _(c): return eq(c.one("SELECT COUNT(*) FROM wrk_orders"), 5)

@check("RC02", RC, "Work executions row count = 6", 1)
def _(c): return eq(c.one("SELECT COUNT(*) FROM wrk_executions"), 6)

@check("RC03", RC, "Work allocations row count = 7", 1)
def _(c): return eq(c.one("SELECT COUNT(*) FROM wrk_allocations"), 7)

@check("RC04", RC, "Executions: in-window source rows = loaded + rejected", 1)
def _(c):
    src = c.one("SELECT COUNT(*) FROM src_executions WHERE trade_date BETWEEN '2024-01-14' AND '2024-01-15'")
    loaded = c.one("SELECT COUNT(*) FROM wrk_executions")
    rej = c.one("SELECT COUNT(*) FROM etl_reject_log WHERE source_table = 'executions'")
    return src == loaded + rej, f"source {src} vs loaded {loaded} + rejected {rej}"

@check("RC05", RC, "Allocations: in-window source rows = loaded + rejected", 1)
def _(c):
    src = c.one("SELECT COUNT(*) FROM src_allocations WHERE trade_date BETWEEN '2024-01-14' AND '2024-01-15'")
    loaded = c.one("SELECT COUNT(*) FROM wrk_allocations")
    rej = c.one("SELECT COUNT(*) FROM etl_reject_log WHERE source_table = 'allocations'")
    return src == loaded + rej, f"source {src} vs loaded {loaded} + rejected {rej}"

@check("FL01", FL, "Qualified orders: exact set of (order, date) after filters", 1)
def _(c):
    expected = {(1001, D15), (1002, D15), (1003, D15), (1004, D15), (1002, D14)}
    return eq(c.keys("SELECT order_id, trade_date FROM wrk_orders"), expected)

@check("FL02", FL, "Out-of-scope orders (venue/instrument/event/source/date) are absent", 1)
def _(c):
    present = {r[0] for r in c.rows("SELECT order_id FROM wrk_orders")} & {1006, 1007, 1008, 1009, 1010, 1011}
    return present == set(), f"out-of-scope orders present: {sorted(present)}"

@check("BD01", FL, "Boundary dates: both window days present, days outside absent", 1)
def _(c):
    return eq({r[0] for r in c.rows("SELECT trade_date FROM wrk_orders")}, {D14, D15})

@check("DU01", DU, "No duplicate (order, date) in work orders", 1)
def _(c): return none(c.rows("SELECT order_id, trade_date, COUNT(*) FROM wrk_orders GROUP BY 1, 2 HAVING COUNT(*) > 1"))

@check("DU02", DU, "No duplicate exec_id / alloc_id in work tables", 1)
def _(c):
    d = c.rows("SELECT 'exec', exec_id FROM wrk_executions GROUP BY exec_id HAVING COUNT(*) > 1 "
               "UNION ALL SELECT 'alloc', alloc_id FROM wrk_allocations GROUP BY alloc_id HAVING COUNT(*) > 1")
    return none(d)

@check("DD01", DD, "Latest event kept per order+date (order 1001 = event 9010, OPEN)", 1)
def _(c): return eq(c.rows("SELECT status, event_id FROM wrk_orders WHERE order_id = 1001"), [("OPEN", 9010)])

@check("NL01", NL, "No NULLs in mandatory work columns", 1)
def _(c):
    n = c.one("""SELECT (SELECT COUNT(*) FROM wrk_orders WHERE order_id IS NULL OR trade_date IS NULL OR qty IS NULL OR side_code IS NULL)
                      + (SELECT COUNT(*) FROM wrk_executions WHERE exec_id IS NULL OR order_id IS NULL OR qty IS NULL OR price IS NULL)
                      + (SELECT COUNT(*) FROM wrk_allocations WHERE alloc_id IS NULL OR exec_id IS NULL OR qty IS NULL OR price IS NULL)""")
    return eq(n, 0)

@check("NL02", NL, "client_name is never NULL", 1)
def _(c): return eq(c.one("SELECT COUNT(*) FROM wrk_orders WHERE client_name IS NULL"), 0)

@check("NL03", NL, "Unknown account defaults to 'UNKNOWN' (order 1003)", 1)
def _(c): return eq(c.rows("SELECT client_name FROM wrk_orders WHERE order_id = 1003"), [("UNKNOWN",)])

@check("RI01", RI, "Every work execution has a parent order", 1)
def _(c):
    return none(c.rows("""SELECT e.exec_id FROM wrk_executions e LEFT JOIN wrk_orders o
                          ON o.order_id = e.order_id AND o.trade_date = e.trade_date WHERE o.order_id IS NULL"""))

@check("RI02", RI, "Every work allocation has a parent execution", 1)
def _(c):
    return none(c.rows("""SELECT a.alloc_id FROM wrk_allocations a LEFT JOIN wrk_executions e
                          ON e.exec_id = a.exec_id WHERE e.exec_id IS NULL"""))

@check("RI03", RI, "Orphans are rejected AND logged (exec 107, alloc 208 only)", 1)
def _(c):
    return eq(c.keys("SELECT source_table, record_id FROM etl_reject_log"),
              {("executions", 107), ("allocations", 208)})

# ---------------------------------------------------------------- STEP 2-4
@check("TR01", TR, "Side codes mapped to text (1=BUY, 2=SELL)", 2)
def _(c):
    return eq(c.keys("SELECT order_id, side_text FROM wrk_orders_ver WHERE trade_date = '2024-01-15'"),
              {(1001, "BUY"), (1002, "SELL"), (1003, "BUY"), (1004, "SELL")})

@check("VR01", VR, "Order versions follow the 4-branch rule", 2)
def _(c):
    got = {(r[0], r[1]): r[2] for r in c.rows("SELECT order_id, trade_date, order_version FROM wrk_orders_ver")}
    return eq(got, {(1001, D15): 1, (1002, D15): 3, (1003, D15): 2, (1004, D15): 3, (1002, D14): 2})

@check("DF01", DF, "Orders delta = exactly the new/changed orders", 2)
def _(c): return eq(c.keys("SELECT order_id, trade_date FROM vw_orders_delta"), {(1001, D15), (1002, D15), (1003, D15)})

@check("TR02", TR, "Market code OFFX mapped to OTC (exec 102)", 3)
def _(c):
    left = c.one("SELECT COUNT(*) FROM wrk_executions_ver WHERE market_code = 'OFFX'")
    m = c.rows("SELECT market_code FROM wrk_executions_ver WHERE exec_id = 102")
    return left == 0 and m == [("OTC",)], f"OFFX left: {left}, exec 102 market: {m}"

@check("VR02", VR, "Execution versions follow the 4-branch rule", 3)
def _(c):
    got = {(r[0], r[1]): r[2] for r in c.rows("SELECT exec_id, trade_date, exec_version FROM wrk_executions_ver")}
    return eq(got, {(101, D15): 1, (102, D15): 1, (103, D15): 2, (104, D15): 2, (105, D15): 2, (106, D14): 1})

@check("DF02", DF, "Executions delta = {101, 102, 103, 104}", 3)
def _(c): return eq({r[0] for r in c.rows("SELECT exec_id FROM vw_exec_delta")}, {101, 102, 103, 104})

@check("VR03", VR, "Allocation versions follow the 4-branch rule", 4)
def _(c):
    got = {(r[0], r[1]): r[2] for r in c.rows("SELECT alloc_id, trade_date, alloc_version FROM wrk_allocations_ver")}
    return eq(got, {(201, D15): 1, (202, D15): 1, (203, D15): 1, (204, D15): 2, (205, D15): 2, (206, D15): 2, (207, D14): 1})

@check("DF03", DF, "Allocations delta = {201 .. 205}", 4)
def _(c): return eq({r[0] for r in c.rows("SELECT alloc_id FROM vw_alloc_delta")}, {201, 202, 203, 204, 205})

@check("DF04", DF, "Unchanged rows are NOT in any delta", 4)
def _(c):
    bad = (c.rows("SELECT 'order', order_id FROM vw_orders_delta WHERE (order_id, trade_date) IN ((1004,'2024-01-15'),(1002,'2024-01-14'))")
           + c.rows("SELECT 'exec', exec_id FROM vw_exec_delta WHERE exec_id IN (105, 106)")
           + c.rows("SELECT 'alloc', alloc_id FROM vw_alloc_delta WHERE alloc_id IN (206, 207)"))
    return none(bad, "unchanged rows found in delta")

@check("BR01", BR, "Allocated qty per execution = execution qty", 4)
def _(c):
    return none(c.rows("""SELECT e.exec_id, e.qty, a.q FROM wrk_executions_ver e
                          JOIN (SELECT exec_id, SUM(qty) q FROM wrk_allocations_ver GROUP BY exec_id) a
                            ON a.exec_id = e.exec_id WHERE a.q <> e.qty"""), "executions where allocations do not add up")

# ---------------------------------------------------------------- STEP 5 (publish)
@check("PB01", PB, "Change scope = exactly 3 (order, date) pairs", 5)
def _(c): return eq(c.keys("SELECT order_id, trade_date FROM wrk_change_scope"), {(1001, D15), (1002, D15), (1003, D15)})

@check("RC06", RC, "Target row counts after publish: 7 / 8 / 9", 5)
def _(c):
    got = (c.one("SELECT COUNT(*) FROM tgt_orders"), c.one("SELECT COUNT(*) FROM tgt_executions"),
           c.one("SELECT COUNT(*) FROM tgt_allocations"))
    return eq(got, (7, 8, 9))

@check("PB02", PB, "Completeness: every work row exists in target (work EXCEPT target is empty)", 5)
def _(c):
    q = "SELECT {cols} FROM {w} EXCEPT SELECT {cols} FROM {t}"
    miss = (c.rows(q.format(w="wrk_orders_ver", t="tgt_orders", cols="order_id, trade_date, order_version, source_batch_id, qty, status, client_name, side_text"))
            + c.rows(q.format(w="wrk_executions_ver", t="tgt_executions", cols="exec_id, order_id, trade_date, exec_version, source_batch_id, qty, price, market_code"))
            + c.rows(q.format(w="wrk_allocations_ver", t="tgt_allocations", cols="alloc_id, order_id, trade_date, alloc_version, source_batch_id, exec_id, account_id, qty, price")))
    return none(miss, "work rows missing from target")

@check("DU03", DU, "No duplicate keys+version in target tables", 5)
def _(c):
    d = (c.rows("SELECT 'orders', order_id, trade_date, order_version FROM tgt_orders GROUP BY 2, 3, 4 HAVING COUNT(*) > 1")
         + c.rows("SELECT 'exec', exec_id, trade_date, exec_version FROM tgt_executions GROUP BY 2, 3, 4 HAVING COUNT(*) > 1")
         + c.rows("SELECT 'alloc', alloc_id, trade_date, alloc_version FROM tgt_allocations GROUP BY 2, 3, 4 HAVING COUNT(*) > 1"))
    return none(d, "duplicate target rows")

@check("PB03", PB, "Unchanged data is not rewritten (1 row each: order 1004, 1002@14, exec 105/106, alloc 206/207)", 5)
def _(c):
    got = (c.one("SELECT COUNT(*) FROM tgt_orders WHERE order_id = 1004"),
           c.one("SELECT COUNT(*) FROM tgt_orders WHERE order_id = 1002 AND trade_date = '2024-01-14'"),
           c.one("SELECT COUNT(*) FROM tgt_executions WHERE exec_id IN (105, 106)"),
           c.one("SELECT COUNT(*) FROM tgt_allocations WHERE alloc_id IN (206, 207)"))
    return eq(got, (1, 1, 2, 2))

@check("NL04", NL, "No NULLs in target key / version columns", 5)
def _(c):
    n = c.one("""SELECT (SELECT COUNT(*) FROM tgt_orders WHERE order_id IS NULL OR trade_date IS NULL OR order_version IS NULL)
                      + (SELECT COUNT(*) FROM tgt_executions WHERE exec_id IS NULL OR trade_date IS NULL OR exec_version IS NULL)
                      + (SELECT COUNT(*) FROM tgt_allocations WHERE alloc_id IS NULL OR trade_date IS NULL OR alloc_version IS NULL)""")
    return eq(n, 0)

@check("RI04", RI, "Every target execution has a parent order in target", 5)
def _(c):
    return none(c.rows("""SELECT e.exec_id FROM tgt_executions e LEFT JOIN tgt_orders o
                          ON o.order_id = e.order_id AND o.trade_date = e.trade_date WHERE o.order_id IS NULL"""))

@check("ST01", ST, "Target order qty/status = latest source event", 5)
def _(c):
    return none(c.rows("""SELECT t.order_id, t.trade_date, t.status, l.status
        FROM tgt_orders t JOIN (SELECT order_id, trade_date, qty, status FROM src_orders s
                                WHERE event_id = (SELECT MAX(event_id) FROM src_orders x
                                                  WHERE x.order_id = s.order_id AND x.trade_date = s.trade_date)) l
          ON l.order_id = t.order_id AND l.trade_date = t.trade_date
        WHERE t.qty <> l.qty OR t.status <> l.status"""), "target vs source mismatches")

@check("ST02", ST, "Target execution qty/price = source (no rounding or truncation)", 5)
def _(c):
    return none(c.rows("""SELECT t.exec_id, t.price, s.price FROM tgt_executions t
        JOIN src_executions s ON s.exec_id = t.exec_id AND s.trade_date = t.trade_date
        WHERE t.qty <> s.qty OR t.price <> s.price"""), "target vs source mismatches")

@check("ST03", ST, "Target allocation qty/price = source", 5)
def _(c):
    return none(c.rows("""SELECT t.alloc_id, t.price, s.price FROM tgt_allocations t
        JOIN src_allocations s ON s.alloc_id = t.alloc_id AND s.trade_date = t.trade_date
        WHERE t.qty <> s.qty OR t.price <> s.price"""), "target vs source mismatches")

@check("ID01", ID, "Idempotency: a second run publishes nothing new", 5)
def _(c):
    con = c.fresh(5)
    total = lambda: sum(con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                        for t in ("tgt_orders", "tgt_executions", "tgt_allocations"))
    before = total()
    run_steps(con, 5, c.bugs)
    return eq(total(), before)
