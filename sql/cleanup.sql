-- CLEANUP: empty every table (structure stays)
DELETE FROM src_orders; DELETE FROM src_executions; DELETE FROM src_allocations; DELETE FROM src_accounts;
DELETE FROM wrk_orders; DELETE FROM wrk_executions; DELETE FROM wrk_allocations; DELETE FROM etl_reject_log;
DELETE FROM wrk_orders_ver; DELETE FROM wrk_executions_ver; DELETE FROM wrk_allocations_ver;
DELETE FROM tgt_orders; DELETE FROM tgt_executions; DELETE FROM tgt_allocations;
DROP TABLE IF EXISTS wrk_change_scope;
