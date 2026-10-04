# DataGuard design

## Flow (the whole thing is 3 ideas)
1. **Stage:** filter + join SOURCE tables into work tables; log orphans (step 1).
2. **Version + delta:** compare against what is already published, assign a version, build `delta = latest EXCEPT published` (steps 2, 3, 4: the same loop for orders, executions, allocations).
3. **Publish:** collect changed keys into a scope, inner-join the work tables to it, write to target (step 5, the only step that writes to target).

| Layer | Tables |
|---|---|
| Source (read-only) | src_orders, src_executions, src_allocations, src_accounts |
| Work (rebuilt each run) | wrk_orders, wrk_executions, wrk_allocations, wrk_*_ver, wrk_change_scope, etl_reject_log |
| Delta views | vw_orders_delta, vw_exec_delta, vw_alloc_delta (plus *_last_ver / *_latest_ver) |
| Target (published history) | tgt_orders, tgt_executions, tgt_allocations |

**Version rule** (steps 2-4): no history anywhere = 1 | exists on other dates only = latest + 1 | exists this date and source batch changed = last + 1 | exists this date, unchanged = keep.

Run scope is hardcoded: trade dates 2024-01-14..2024-01-15, current batch B5. Delta views recompute on read, so checks on deltas run before publish (stage 4), checks on the target run after (stage 5).


## Versioning Logic (Branches)

Every incoming order is assigned to one branch, based on whether it already
exists in the target and what changed.

> **Note:** Branch number = which rule fired. Version number = that order's own
> change history. They are not linked. A branch never "produces" a fixed version;
> it always does `new version = previous version + 1` (or no change).

### Decision tree

```
Is this order already in the target?
├── No  → Branch 1 (new, insert as v1)
└── Yes → Did anything meaningful change?
         ├── No  → Branch 4 (unchanged, keep current version)
         └── Yes → Why?
                  ├── New business date   → Branch 2
                  └── New batch / resend  → Branch 3
```

### Branch definitions

| Branch | Situation | What the pipeline does |
|---|---|---|
| 1 | Brand-new order, not in target | Insert as v1 |
| 2 | Existing order, new business date, data changed | New version = previous + 1; close old version |
| 3 | Existing order re-sent in a later batch (correction) | New version = previous + 1; close old version |
| 4 | Existing order, nothing changed | No new row; version unchanged |

> TODO: Confirm branch 2 vs 3 definitions against the version-assignment
> code (CASE WHEN / if-elif block).

### Seed data mapping

| Seed row | Prior version | Branch | Expected version |
|---|---|---|---|
| Order 1001 (events 9001, 9010) | none | 1 | v1 (latest event kept, status OPEN) |
| Order 1002 on 01-15 | v2 | 2 | v3 |
| Order 1002 on 01-14 | v3 | 4 | v3 (unchanged) |
| Order 1003 (batch B4 → B5) | v1 | 3 | v2 |
| Order 1004 | v3 | 4 | v3 (unchanged) |

### Validation checks

1. Exactly one current row per order.
2. Changed orders: new version = previous version + 1, and the old version is closed.
3. Unchanged orders: row count and version are the same before and after the run.
4. Version numbers never skip or reset.

## Seed cheat sheet
| Row | Purpose |
|---|---|
| order 1001 (events 9001, 9010) | dedup keeps latest (OPEN); version branch 1 |
| order 1002 on 01-15 / 01-14 | branch 2 (v3) / unchanged |
| order 1003 (batch B4 to B5, account ACC3) | branch 3 (v2); account missing, client UNKNOWN |
| order 1004 | branch 4 (v3), unchanged, venue VEN_C, source SYS2 |
| orders 1006-1011 | filtered out: venue, instrument, event type, before window, after window, source system |
| execution 102 (OFFX) | must become OTC |
| execution 107, allocation 208 | orphans: rejected and logged |
| prices 1500.25 | precision (rounding) bug |

## Bug catalogue
| Bug | Type | Primary detector |
|---|---|---|
| B1 | Wrong join type | FL01, NL03 |
| B2 | Missing filter value | FL01 |
| B3 | Join key mismatch / duplicates | DU03, PB03 |
| B4 | Stale data (wrong dedup order) | DD01, ST01 |
| B5 | Versioning logic | VR01, DF01 |
| B6 | Transformation / mapping | TR02 |
| B7 | Calculation error | ST03 |
| B8 | NULL handling | NL02, NL03 |
| B9 | Precision loss | ST02 |
| B10 | Boundary / off-by-one date | BD01, FL01 |

## Simplified vs a real pipeline
SQLite instead of a big-data engine; hardcoded date window and batch; execution/allocation versions keyed by their own id; no
receive/release union, cross-trade remap or extra dimensions. The shape (work table, version, EXCEPT delta, scope, inner-join write) is the same.
