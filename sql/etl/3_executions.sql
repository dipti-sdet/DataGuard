-- STEP 3 (executions): same version + delta loop as step 2, plus the market-code mapping.
DROP VIEW IF EXISTS vw_exec_last_ver;
DROP VIEW IF EXISTS vw_exec_latest_ver;
DROP VIEW IF EXISTS vw_exec_delta;

CREATE VIEW vw_exec_last_ver AS
SELECT exec_id, trade_date, MAX(exec_version) AS exec_version, source_batch_id
FROM tgt_executions GROUP BY exec_id, trade_date;

CREATE VIEW vw_exec_latest_ver AS
SELECT exec_id, MAX(exec_version) AS exec_version
FROM tgt_executions GROUP BY exec_id;

DELETE FROM wrk_executions_ver;
INSERT INTO wrk_executions_ver
SELECT w.exec_id, w.order_id, w.trade_date,
       CASE
         WHEN lastv.exec_version IS NULL AND latestv.exec_version IS NULL THEN 1
         WHEN lastv.exec_version IS NULL THEN latestv.exec_version + 1
         WHEN lastv.source_batch_id <> w.source_batch_id THEN lastv.exec_version + 1
         ELSE lastv.exec_version
       END AS exec_version,
       w.source_batch_id, w.qty, w.price,
       CASE WHEN w.market_code = 'OFFX' THEN 'OTC' ELSE w.market_code END AS market_code
FROM wrk_executions w
LEFT JOIN vw_exec_last_ver   lastv   ON lastv.exec_id = w.exec_id AND lastv.trade_date = w.trade_date
LEFT JOIN vw_exec_latest_ver latestv ON latestv.exec_id = w.exec_id;

CREATE VIEW vw_exec_delta AS
SELECT exec_id, order_id, trade_date, exec_version, qty, price, market_code FROM wrk_executions_ver
EXCEPT
SELECT exec_id, order_id, trade_date, exec_version, qty, price, market_code FROM tgt_executions;
