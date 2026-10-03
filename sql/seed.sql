-- SEED DATA. Run scope: trade dates 2024-01-14..2024-01-15, current batch B5.
-- Every row has a purpose (see docs/design.md).
INSERT INTO src_accounts VALUES ('ACC1','Alpha Capital'), ('ACC2','Beta Funds');
-- ACC3 is deliberately missing from the dimension (orphan account)

INSERT INTO src_orders VALUES
(9001,1001,'2024-01-15','NEW',   'VEN_A','FUT',   'SYS1','ACC1','1',100,'NEW', 'B5'), -- superseded by 9010
(9010,1001,'2024-01-15','AMEND', 'VEN_A','FUT',   'SYS1','ACC1','1',100,'OPEN','B5'), -- latest event wins
(9002,1002,'2024-01-15','NEW',   'VEN_A','FUT',   'SYS1','ACC2','2',200,'OPEN','B5'),
(9003,1003,'2024-01-15','AMEND', 'VEN_B','OPT',   'SYS1','ACC3','1',300,'OPEN','B5'), -- ACC3 not in dim
(9004,1004,'2024-01-15','NEW',   'VEN_C','FUT',   'SYS2','ACC1','2',400,'OPEN','B5'),
(9005,1002,'2024-01-14','NEW',   'VEN_A','FUT',   'SYS1','ACC2','2',200,'OPEN','B4'),
(9006,1006,'2024-01-15','NEW',   'VEN_X','FUT',   'SYS1','ACC1','1', 50,'NEW', 'B5'), -- out: venue
(9007,1007,'2024-01-15','NEW',   'VEN_A','EQ',    'SYS1','ACC1','1', 60,'NEW', 'B5'), -- out: instrument
(9008,1008,'2024-01-15','BUSTED','VEN_A','FUT',   'SYS1','ACC1','1', 70,'NEW', 'B5'), -- out: event type
(9011,1009,'2024-01-10','NEW',   'VEN_A','FUT',   'SYS1','ACC1','1', 80,'NEW', 'B2'), -- out: before window
(9012,1010,'2024-01-16','NEW',   'VEN_A','FUT',   'SYS1','ACC1','1', 90,'NEW', 'B5'), -- out: after window
(9013,1011,'2024-01-15','NEW',   'VEN_A','FUT',   'SYS9','ACC1','1', 20,'NEW', 'B5'); -- out: source system

INSERT INTO src_executions VALUES
(101,1001,'2024-01-15', 60,1500.25,'EXCH','B5'),
(102,1001,'2024-01-15', 40,1500.25,'OFFX','B5'), -- OFFX must become OTC
(103,1002,'2024-01-15',200,3500.0, 'EXCH','B5'),
(104,1003,'2024-01-15',300,1600.0, 'EXCH','B5'),
(105,1004,'2024-01-15',400,1700.0, 'EXCH','B5'),
(106,1002,'2024-01-14',200,3500.0, 'EXCH','B4'),
(107,1006,'2024-01-15', 10, 100.0, 'EXCH','B5'); -- parent order is out of scope: orphan

INSERT INTO src_allocations VALUES
(201,101,1001,'2024-01-15','ACC1', 30,1500.25,'B5'),
(202,101,1001,'2024-01-15','ACC2', 30,1500.25,'B5'),
(203,102,1001,'2024-01-15','ACC1', 40,1500.25,'B5'),
(204,103,1002,'2024-01-15','ACC1',200,3500.0, 'B5'),
(205,104,1003,'2024-01-15','ACC3',300,1600.0, 'B5'),
(206,105,1004,'2024-01-15','ACC2',400,1700.0, 'B5'),
(207,106,1002,'2024-01-14','ACC2',200,3500.0, 'B4'),
(208,999,1002,'2024-01-15','ACC9',  5, 100.0, 'B5'); -- parent execution not in scope: orphan

-- TARGET: history published by earlier runs
-- orders: 1001 none -> v1 | 1002 other dates only -> v3 | 1003 batch B4->B5 -> v2 | 1004 unchanged v3
INSERT INTO tgt_orders VALUES
(1002,'2024-01-13',1,'B3',200,'OPEN','Beta Funds',   'SELL'),
(1002,'2024-01-14',2,'B4',200,'OPEN','Beta Funds',   'SELL'),
(1003,'2024-01-15',1,'B4',300,'OPEN','UNKNOWN',      'BUY'),
(1004,'2024-01-15',3,'B5',400,'OPEN','Alpha Capital','SELL');
INSERT INTO tgt_executions VALUES
(106,1002,'2024-01-14',1,'B4',200,3500.0,'EXCH'),
(103,1002,'2024-01-14',1,'B4',200,3500.0,'EXCH'),
(104,1003,'2024-01-15',1,'B4',300,1600.0,'EXCH'),
(105,1004,'2024-01-15',2,'B5',400,1700.0,'EXCH');
INSERT INTO tgt_allocations VALUES
(207,1002,'2024-01-14',1,'B4',106,'ACC2',200,3500.0),
(204,1002,'2024-01-14',1,'B4',103,'ACC1',200,3500.0),
(205,1003,'2024-01-15',1,'B4',104,'ACC3',300,1600.0),
(206,1004,'2024-01-15',2,'B5',105,'ACC2',400,1700.0);
