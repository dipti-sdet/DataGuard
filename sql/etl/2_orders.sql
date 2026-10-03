-- STEP 2 (orders): assign a version against published history, then build the delta view.
DROP VIEW IF EXISTS vw_orders_last_ver;
DROP VIEW IF EXISTS vw_orders_latest_ver;
DROP VIEW IF EXISTS vw_orders_delta;

-- last version   = what the target holds for this order on THIS trade_date
CREATE VIEW vw_orders_last_ver AS
SELECT order_id, trade_date, MAX(order_version) AS order_version, source_batch_id
FROM tgt_orders GROUP BY order_id, trade_date;

-- latest version = highest version of this order across ALL dates
CREATE VIEW vw_orders_latest_ver AS
SELECT order_id, MAX(order_version) AS order_version
FROM tgt_orders GROUP BY order_id;

DELETE FROM wrk_orders_ver;
INSERT INTO wrk_orders_ver
SELECT w.order_id, w.trade_date,
       CASE
         WHEN lastv.order_version IS NULL AND latestv.order_version IS NULL THEN 1
         WHEN lastv.order_version IS NULL THEN latestv.order_version + 1
         WHEN lastv.source_batch_id <> w.source_batch_id THEN lastv.order_version + 1
         ELSE lastv.order_version
       END AS order_version,
       w.source_batch_id, w.qty, w.status, w.client_name,
       CASE w.side_code WHEN '1' THEN 'BUY' WHEN '2' THEN 'SELL' WHEN '3' THEN 'BUY'
                        WHEN '4' THEN 'SELL' WHEN '5' THEN 'SELL SHORT'
                        WHEN '6' THEN 'SELL SHORT EXEMPT' END AS side_text
FROM wrk_orders w
LEFT JOIN vw_orders_last_ver   lastv   ON lastv.order_id = w.order_id AND lastv.trade_date = w.trade_date
LEFT JOIN vw_orders_latest_ver latestv ON latestv.order_id = w.order_id;

-- delta = new/changed rows only (latest EXCEPT published); a view, so it recomputes on read
CREATE VIEW vw_orders_delta AS
SELECT order_id, trade_date, order_version, qty, status, client_name, side_text FROM wrk_orders_ver
EXCEPT
SELECT order_id, trade_date, order_version, qty, status, client_name, side_text FROM tgt_orders;
