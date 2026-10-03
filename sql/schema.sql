-- DataGuard schema (SQLite). Three layers, like a production incremental load:
--   src_*  : read-only source tables (what upstream delivers)
--   wrk_*  : work tables, rebuilt on every run
--   tgt_*  : published target tables, written ONLY by the last step (5_publish)
-- No constraints on purpose, so bad data CAN land. The checks are the safety net.
DROP VIEW IF EXISTS vw_orders_last_ver;  DROP VIEW IF EXISTS vw_orders_latest_ver; DROP VIEW IF EXISTS vw_orders_delta;
DROP VIEW IF EXISTS vw_exec_last_ver;    DROP VIEW IF EXISTS vw_exec_latest_ver;   DROP VIEW IF EXISTS vw_exec_delta;
DROP VIEW IF EXISTS vw_alloc_last_ver;   DROP VIEW IF EXISTS vw_alloc_latest_ver;  DROP VIEW IF EXISTS vw_alloc_delta;
DROP TABLE IF EXISTS wrk_change_scope;
DROP TABLE IF EXISTS src_orders;     DROP TABLE IF EXISTS src_executions; DROP TABLE IF EXISTS src_allocations;
DROP TABLE IF EXISTS src_accounts;
DROP TABLE IF EXISTS wrk_orders;     DROP TABLE IF EXISTS wrk_executions; DROP TABLE IF EXISTS wrk_allocations;
DROP TABLE IF EXISTS wrk_orders_ver; DROP TABLE IF EXISTS wrk_executions_ver; DROP TABLE IF EXISTS wrk_allocations_ver;
DROP TABLE IF EXISTS tgt_orders;     DROP TABLE IF EXISTS tgt_executions; DROP TABLE IF EXISTS tgt_allocations;
DROP TABLE IF EXISTS etl_reject_log;

-- SOURCE
CREATE TABLE src_orders (
    event_id INTEGER, order_id INTEGER, trade_date TEXT, event_type TEXT, venue TEXT,
    instrument_type TEXT, source_system TEXT, account_id TEXT, side_code TEXT,
    qty INTEGER, status TEXT, source_batch_id TEXT);
CREATE TABLE src_executions (
    exec_id INTEGER, order_id INTEGER, trade_date TEXT, qty INTEGER, price REAL,
    market_code TEXT, source_batch_id TEXT);
CREATE TABLE src_allocations (
    alloc_id INTEGER, exec_id INTEGER, order_id INTEGER, trade_date TEXT,
    account_id TEXT, qty INTEGER, price REAL, source_batch_id TEXT);
CREATE TABLE src_accounts (account_id TEXT, client_name TEXT);

-- WORK: step 1 (stage)
CREATE TABLE wrk_orders (
    order_id INTEGER, event_id INTEGER, trade_date TEXT, qty INTEGER, status TEXT,
    side_code TEXT, client_name TEXT, source_batch_id TEXT);
CREATE TABLE wrk_executions (
    exec_id INTEGER, order_id INTEGER, trade_date TEXT, qty INTEGER, price REAL,
    market_code TEXT, source_batch_id TEXT);
CREATE TABLE wrk_allocations (
    alloc_id INTEGER, exec_id INTEGER, order_id INTEGER, trade_date TEXT,
    account_id TEXT, qty INTEGER, price REAL, source_batch_id TEXT);
CREATE TABLE etl_reject_log (source_table TEXT, record_id INTEGER, reason TEXT);

-- WORK: steps 2-4 (version assigned)
CREATE TABLE wrk_orders_ver (
    order_id INTEGER, trade_date TEXT, order_version INTEGER, source_batch_id TEXT,
    qty INTEGER, status TEXT, client_name TEXT, side_text TEXT);
CREATE TABLE wrk_executions_ver (
    exec_id INTEGER, order_id INTEGER, trade_date TEXT, exec_version INTEGER,
    source_batch_id TEXT, qty INTEGER, price REAL, market_code TEXT);
CREATE TABLE wrk_allocations_ver (
    alloc_id INTEGER, order_id INTEGER, trade_date TEXT, alloc_version INTEGER,
    source_batch_id TEXT, exec_id INTEGER, account_id TEXT, qty INTEGER, price REAL);

-- TARGET (published history)
CREATE TABLE tgt_orders (
    order_id INTEGER, trade_date TEXT, order_version INTEGER, source_batch_id TEXT,
    qty INTEGER, status TEXT, client_name TEXT, side_text TEXT);
CREATE TABLE tgt_executions (
    exec_id INTEGER, order_id INTEGER, trade_date TEXT, exec_version INTEGER,
    source_batch_id TEXT, qty INTEGER, price REAL, market_code TEXT);
CREATE TABLE tgt_allocations (
    alloc_id INTEGER, order_id INTEGER, trade_date TEXT, alloc_version INTEGER,
    source_batch_id TEXT, exec_id INTEGER, account_id TEXT, qty INTEGER, price REAL);
