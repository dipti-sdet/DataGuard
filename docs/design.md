# DataGuard design

## Flow (the whole thing is 3 ideas)

1. **Stage:** filter + join SOURCE tables into work tables; log orphans (step 1).
2. **Version + delta:** compare against what is already published, assign a version, build delta = latest EXCEPT published (steps 2, 3, 4: the same loop for orders, executions, allocations).
3. **Publish:** collect changed keys into a scope, inner-join the work tables to it, write to target (step 5, the only step that writes to target).

Run scope is hardcoded: trade dates 2024-01-14..2024-01-15, current batch B5. Delta views recompute on read, so checks on deltas run before publish (stage 4), checks on the target run after (stage 5).

## Layers

| Layer | Tables |
|---|---|
| Source (read-only) | src_orders, src_executions, src_allocations, src_accounts |
| Work (rebuilt each run) | wrk_orders, wrk_executions, wrk_allocations, wrk_*_ver, wrk_change_scope, etl_reject_log |
| Delta views | vw_orders_delta, vw_exec_delta, vw_alloc_delta (plus *_last_ver / *_latest_ver) |
| Target (published history) | tgt_orders, tgt_executions, tgt_allocations |

## Versioning logic (steps 2-4)

Each key on each trade date in the run falls into exactly one branch.

```
Does this key have any published history?
├── No  → Branch 1: version = 1
└── Yes → Does it already exist on this trade date?
          ├── No  → Branch 2: version = latest + 1   (latest across all dates)
          └── Yes → Did the source batch change?
                    ├── Yes → Branch 3: version = last + 1   (last on this date)
                    └── No  → Branch 4: keep version (not in delta, not republished)
```

| Branch | Situation | Version |
|---|---|---|
| 1 | No history anywhere | 1 |
| 2 | Exists on other dates only | latest + 1 |
| 3 | Exists on this date, source batch changed | last + 1 |
| 4 | Exists on this date, batch unchanged | keep |

**Note:** Branch number = which rule fired. Version number = that key's own history. They are not linked; the same branch can produce v2 for one order and v3 for another.

Versioning checks: VR01, DF01 (bug B5). Practice: P12-P16 in the workbook.

## Seed data

| Seed row | Tests | Expected result |
|---|---|---|
| Order 1001 (events 9001, 9010) | Dedup, branch 1 | Latest event 9010 kept (status OPEN); v1 |
| Order 1002, 01-14 | Branch 4 | Keeps existing v2; not in delta |
| Order 1002, 01-15 | Branch 2 | v3 (latest v2 + 1) |
| Order 1003 (batch B4 → B5, account ACC3) | Branch 3, NULL handling | v2; account missing → client UNKNOWN |
| Order 1004 | Branch 4, mapping | Stays v3, not in delta; venue VEN_C, source SYS2 |
| Orders 1006-1011 | Filters | Excluded: venue, instrument, event type, before window, after window, source system |
| Execution 102 (OFFX) | Mapping | Venue becomes OTC |
| Execution 107, allocation 208 | Orphans | Rejected and logged in etl_reject_log |
| Prices 1500.25 | Precision | Value preserved exactly (no rounding) |

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

SQLite instead of a big-data engine; hardcoded date window and batch; execution/allocation versions keyed by their own id; no receive/release union, cross-trade remap or extra dimensions. The shape (work table, version, EXCEPT delta, scope, inner-join write) is the same.