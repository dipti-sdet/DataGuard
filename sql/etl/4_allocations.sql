-- STEP 4 (allocations): same version + delta loop.
DROP VIEW IF EXISTS vw_alloc_last_ver;
DROP VIEW IF EXISTS vw_alloc_latest_ver;
DROP VIEW IF EXISTS vw_alloc_delta;

CREATE VIEW vw_alloc_last_ver AS
SELECT alloc_id, trade_date, MAX(alloc_version) AS alloc_version, source_batch_id
FROM tgt_allocations GROUP BY alloc_id, trade_date;

CREATE VIEW vw_alloc_latest_ver AS
SELECT alloc_id, MAX(alloc_version) AS alloc_version
FROM tgt_allocations GROUP BY alloc_id;

DELETE FROM wrk_allocations_ver;
INSERT INTO wrk_allocations_ver
SELECT w.alloc_id, w.order_id, w.trade_date,
       CASE
         WHEN lastv.alloc_version IS NULL AND latestv.alloc_version IS NULL THEN 1
         WHEN lastv.alloc_version IS NULL THEN latestv.alloc_version + 1
         WHEN lastv.source_batch_id <> w.source_batch_id THEN lastv.alloc_version + 1
         ELSE lastv.alloc_version
       END AS alloc_version,
       w.source_batch_id, w.exec_id, w.account_id, w.qty, w.price
FROM wrk_allocations w
LEFT JOIN vw_alloc_last_ver   lastv   ON lastv.alloc_id = w.alloc_id AND lastv.trade_date = w.trade_date
LEFT JOIN vw_alloc_latest_ver latestv ON latestv.alloc_id = w.alloc_id;

CREATE VIEW vw_alloc_delta AS
SELECT alloc_id, order_id, trade_date, alloc_version, exec_id, account_id, qty, price FROM wrk_allocations_ver
EXCEPT
SELECT alloc_id, order_id, trade_date, alloc_version, exec_id, account_id, qty, price FROM tgt_allocations;
