-- 12 · Transactions and constraints
-- Question: What happens if we try to put the same package on a route twice?
-- Concepts: UNIQUE (route_id, package_id) in schema.sql rejects the second insert.
--           Inside a transaction, a failed step can be rolled back so the database
--           never ends up half-updated.
-- Note: this file is run step by step by `python -m deliverydb demo-transaction`.

BEGIN;
INSERT INTO packages(package_id, customer_id, weight_kg) VALUES (999999, 1, 2.5);
INSERT INTO deliveries(route_id, package_id, stop_order) VALUES (1, 999999, 1000);
INSERT INTO deliveries(route_id, package_id, stop_order) VALUES (1, 999999, 1001);  -- fails: duplicate
ROLLBACK;
