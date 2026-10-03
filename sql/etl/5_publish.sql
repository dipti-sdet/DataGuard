-- STEP 5 (publish): the ONLY step that writes to the target tables.
-- Change scope = every (order, date) that changed in orders OR executions OR allocations.
-- Snapshot it into a table FIRST: the delta views recompute, so they would change
-- as soon as the first target insert lands.
DROP TABLE IF EXISTS wrk_change_scope;
CREATE TABLE wrk_change_scope AS
SELECT order_id, trade_date FROM vw_orders_delta
UNION
SELECT order_id, trade_date FROM vw_exec_delta
UNION
SELECT order_id, trade_date FROM vw_alloc_delta;

-- Inner join each work table to the scope; only matching rows are published.
INSERT INTO tgt_orders
SELECT o.order_id, o.trade_date, o.order_version, o.source_batch_id,
       o.qty, o.status, o.client_name, o.side_text
FROM wrk_orders_ver o
JOIN wrk_change_scope s ON s.order_id = o.order_id AND s.trade_date = o.trade_date;

INSERT INTO tgt_executions
SELECT e.exec_id, e.order_id, e.trade_date, e.exec_version, e.source_batch_id,
       e.qty, e.price, e.market_code
FROM wrk_executions_ver e
JOIN wrk_change_scope s ON s.order_id = e.order_id AND s.trade_date = e.trade_date;

INSERT INTO tgt_allocations
SELECT a.alloc_id, a.order_id, a.trade_date, a.alloc_version, a.source_batch_id,
       a.exec_id, a.account_id, a.qty, a.price
FROM wrk_allocations_ver a
JOIN wrk_change_scope s ON s.order_id = a.order_id AND s.trade_date = a.trade_date;
