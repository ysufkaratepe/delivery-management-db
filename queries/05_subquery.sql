-- 05 · Subqueries
-- Question: Which routes were longer than the average route?
-- Concepts: a scalar subquery used inside WHERE and SELECT.

SELECT route_id,
       route_date,
       distance_km,
       ROUND(distance_km - (SELECT AVG(distance_km) FROM routes), 1) AS above_avg_km
FROM routes
WHERE distance_km > (SELECT AVG(distance_km) FROM routes)
ORDER BY distance_km DESC
LIMIT 10;
