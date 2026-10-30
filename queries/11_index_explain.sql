-- 11 · Indexes and EXPLAIN QUERY PLAN
-- Question: How does the database find all deliveries of one route?
-- Concepts: EXPLAIN QUERY PLAN shows whether SQLite scans the whole table or uses an index.
--           Thanks to idx_deliveries_route (see schema.sql) it says
--           "SEARCH deliveries USING INDEX idx_deliveries_route" instead of "SCAN deliveries".
--           Note: the UNIQUE (route_id, ...) constraints also create hidden indexes.
--           Run `python -m deliverydb benchmark` to see a real before/after measurement
--           on packages.customer_id (with vs. without idx_packages_customer).

EXPLAIN QUERY PLAN
SELECT * FROM deliveries WHERE route_id = 42;
