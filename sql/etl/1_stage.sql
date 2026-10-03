-- STEP 1 (stage): filter + join SOURCE into work tables; log orphans.
DELETE FROM wrk_orders; DELETE FROM wrk_executions; DELETE FROM wrk_allocations; DELETE FROM etl_reject_log;

-- Orders: venue / instrument / source / event / date filters, left join to accounts,
-- keep only the LATEST event per order + date.
INSERT INTO wrk_orders
SELECT order_id, event_id, trade_date, qty, status, side_code, client_name, source_batch_id
FROM (
    SELECT h.order_id, h.event_id, h.trade_date, h.qty, h.status, h.side_code,
           COALESCE(d.client_name, 'UNKNOWN') AS client_name,
           h.source_batch_id,
           ROW_NUMBER() OVER (PARTITION BY h.order_id, h.trade_date
                              ORDER BY h.event_id DESC) AS rn
    FROM src_orders h
    LEFT JOIN src_accounts d ON d.account_id = h.account_id
    WHERE h.venue IN ('VEN_A','VEN_B','VEN_C')
      AND h.instrument_type IN ('FUT','OPT','SPREAD')
      AND h.source_system IN ('SYS1','SYS2')
      AND h.event_type IN ('NEW','AMEND','CANCEL')
      AND h.trade_date BETWEEN '2024-01-14' AND '2024-01-15'
) WHERE rn = 1;

-- Executions: keep those whose parent order survived; log the rest as rejects
INSERT INTO etl_reject_log
SELECT 'executions', e.exec_id, 'parent order not found'
FROM src_executions e
LEFT JOIN wrk_orders o ON o.order_id = e.order_id AND o.trade_date = e.trade_date
WHERE e.trade_date BETWEEN '2024-01-14' AND '2024-01-15' AND o.order_id IS NULL;

INSERT INTO wrk_executions
SELECT e.exec_id, e.order_id, e.trade_date, e.qty, e.price, e.market_code, e.source_batch_id
FROM src_executions e
JOIN wrk_orders o ON o.order_id = e.order_id AND o.trade_date = e.trade_date;

-- Allocations: keep those whose parent execution survived; log the rest as rejects
INSERT INTO etl_reject_log
SELECT 'allocations', a.alloc_id, 'parent execution not found'
FROM src_allocations a
LEFT JOIN wrk_executions x ON x.exec_id = a.exec_id
WHERE a.trade_date BETWEEN '2024-01-14' AND '2024-01-15' AND x.exec_id IS NULL;

INSERT INTO wrk_allocations
SELECT a.alloc_id, a.exec_id, a.order_id, a.trade_date, a.account_id, a.qty, a.price, a.source_batch_id
FROM src_allocations a
JOIN wrk_executions x ON x.exec_id = a.exec_id;
