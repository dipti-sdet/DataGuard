# ETL validation checks: what to test, and how to write each

## How to write any check (4 steps)
1. **Pick the stage:** after which ETL step does the evidence exist? (deltas: before publish; target: after.)
2. **Write the query that finds the problem.** Best form: it returns the OFFENDING rows, so empty means pass.
3. **Compute the expected value from the source, not from the ETL output.** Hardcoding is fine for a first version, but a check that copies the ETL's own answer proves nothing.
4. **Test the check:** it must pass on the good run and fail on a bug. If it passes on a bug, it is blind.

Return `(passed, detail)`; put the offending rows in `detail` so a failure explains itself.

## The checks (22 types)
| # | Check type | Question it answers | SQL pattern | DataGuard checks | Practice |
|---|---|---|---|---|---|
| 1 | Row count | Same number of rows as expected? | `SELECT COUNT(*)` on both sides, compare | RC01-03, RC06 | P01 |
| 2 | Reconciliation | Does every source row end up loaded or rejected? | source = loaded + rejected | RC04-05 | |
| 3 | Missing records | What is in the source but not in the target? | `src EXCEPT tgt` or LEFT JOIN ... IS NULL | PB02, FL01 | P06 |
| 4 | Extra / ghost records | What is in the target with no source? | reverse of #3, limited to the current batch | | P11 |
| 5 | Duplicates | Does a key appear twice? | `GROUP BY key HAVING COUNT(*) > 1` | DU01-03 | P02 |
| 6 | NULL / mandatory | Are required columns filled? | `WHERE col IS NULL` | NL01, NL02, NL04 | P03 |
| 7 | Default values | Does a missing value get the agreed default? | `WHERE id = X` equals 'UNKNOWN' | NL03 | |
| 8 | Referential integrity | Does every child have a parent? | child LEFT JOIN parent WHERE parent IS NULL | RI01-04 | |
| 9 | Field-level match | Is every value identical to the source? | JOIN on key WHERE a <> b (NULL-safe) | ST01-03 | P05 |
| 10 | Transformation / mapping | Is each rule applied (code to text, OFFX to OTC)? | assert the mapped value; assert no unmapped value remains | TR01-02 | P04 |
| 11 | Calculation / business rule | Do totals add up (children = parent)? | `SUM(child)` vs parent | BR01 | |
| 12 | Aggregate / checksum | Do SUM / MIN / MAX / COUNT DISTINCT agree? | aggregate both sides | | P10 |
| 13 | Domain / value set | Only allowed values? | `WHERE status NOT IN (...)` | | P08 |
| 14 | Range / format | Positive qty, valid dates, no negatives? | `WHERE qty <= 0`, date pattern | | P09 |
| 15 | Schema / data type | Are columns and types as designed? | `PRAGMA table_info(table)` | | P07 |
| 16 | Filters & boundaries | Are in-scope rows kept and out-of-scope rows dropped, at the edges? | key set equality; first and last day | FL01-02, BD01 | P06 |
| 17 | Dedup / latest record | Did the right duplicate win? | assert the winner's id and status | DD01 | |
| 18 | Versioning | Does each branch of the version rule give the right number? | dict of key to expected version | VR01-03 | P12 |
| 19 | Delta / incremental | Only new or changed rows in the delta? Unchanged rows absent? | key set equality on the delta; absence checks | DF01-04 | |
| 20 | Publish / scope | Is every changed key published, and nothing else? | work EXCEPT target is empty; scope key set | PB01-03 | |
| 21 | Idempotency / re-run | Does a second run change nothing? | count before and after run 2 | ID01 | |
| 22 | Incremental scenario | If the source changes, does the next run publish exactly that change? | UPDATE source, re-run, assert version and row counts | | P12 |

Plus a **regression** layer: plant a bug, confirm a check fails. That is `bugs.py` and `pytest`.

## Order to learn them
1. Counts, duplicates, NULLs (#1, #5, #6): 15 minutes each, the basics everyone is asked.
2. Missing and extra records, field match (#3, #4, #9): the core of source-to-target testing.
3. Mapping, domain, range, schema (#10, #13, #14, #15).
4. Versioning, delta, scope, idempotency, scenarios (#18-22): what makes you senior.

## Anatomy of an ETL test automation project
| Part | In DataGuard | What it does |
|---|---|---|
| Test data | `sql/seed.sql` | Small, hand-made data where every row has a purpose |
| Schema and cleanup | `sql/schema.sql`, `sql/cleanup.sql` | Build and reset the environment |
| ETL under test | `sql/etl/*.sql` | The pipeline |
| Runner | `dataguard/pipeline.py` | Builds a fresh DB, runs the steps, can stop after any step |
| Checks | `dataguard/checks.py` | Each check: id, category, stage, function |
| Bug injection | `dataguard/bugs.py` | Proves the checks can catch real defects |
| Reporting | `dataguard/report.py` | Check x run matrix, bug detection, failures with detail |
| Test framework | `tests/` (pytest) | Good run passes; every bug is caught |

To build your own for a new pipeline: write the seed first (decide which rows exercise which rule), then the checks, then the bugs.
