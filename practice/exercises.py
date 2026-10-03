from dataclasses import dataclass


@dataclass
class Exercise:
    id: str
    title: str
    level: int
    stage: int      # ETL step after which your check runs
    catches: list   # bug ids your check must FAIL on (it must PASS on the good run)


EXERCISES = [
    Exercise("P01", "Row count vs source (expected computed from source)", 1, 1, ["B1", "B2", "B10"]),
    Exercise("P02", "Duplicates in target (key + version)",              1, 5, ["B3"]),
    Exercise("P03", "NULL check on client_name",                          1, 1, ["B8"]),
    Exercise("P04", "Transformation: market code mapping",                1, 3, ["B6"]),
    Exercise("P05", "Source-to-target field match (execution + allocation price)", 1, 5, ["B7", "B9"]),
    Exercise("P06", "Missing records (source rows absent from work)",     1, 1, ["B1", "B2", "B10"]),
    Exercise("P07", "Schema / data type check on target",                 2, 5, ["X1"]),
    Exercise("P08", "Domain check: allowed order status values",          2, 1, ["X2"]),
    Exercise("P09", "Range check: qty > 0 and price > 0",                 2, 4, ["X3"]),
    Exercise("P10", "Aggregate check: SUM(qty) source vs work",           2, 3, ["X4"]),
    Exercise("P11", "Ghost records: target rows with no source",          2, 5, ["X5"]),
    Exercise("P12", "Incremental scenario: change source, rerun, verify", 3, 5, ["B5", "X6"]),
]
