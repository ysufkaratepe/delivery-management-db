-- 06 · Common Table Expressions (WITH)
-- Question: For each courier, what are their totals and their average success rate per route?
-- Concepts: splitting a complex query into named steps that read top to bottom.

WITH per_route AS (
    SELECT r.courier_id,
           r.route_id,
           COUNT(*)                                       AS stops,
           1.0 * SUM(d.outcome = 'delivered') / COUNT(*)  AS success
    FROM routes r
    JOIN deliveries d ON d.route_id = r.route_id
    GROUP BY r.route_id
),
per_courier AS (
    SELECT courier_id,
           COUNT(*)                    AS routes,
           SUM(stops)                  AS total_stops,
           ROUND(100 * AVG(success), 2) AS avg_success_pct
    FROM per_route
    GROUP BY courier_id
)
SELECT c.full_name, pc.routes, pc.total_stops, pc.avg_success_pct
FROM per_courier pc
JOIN couriers c ON c.courier_id = pc.courier_id
ORDER BY pc.avg_success_pct DESC;
