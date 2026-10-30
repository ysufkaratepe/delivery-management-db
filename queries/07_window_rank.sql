-- 07 · Window functions: RANK() with PARTITION BY
-- Question: Who was the best courier each week (most successful deliveries)?
-- Concepts: window functions compute a value for each row using a "window" of related
--           rows, without collapsing them like GROUP BY does.

WITH weekly AS (
    SELECT strftime('%Y-W%W', r.route_date) AS week,
           c.full_name                      AS courier,
           SUM(d.outcome = 'delivered')     AS delivered
    FROM routes r
    JOIN couriers   c ON c.courier_id = r.courier_id
    JOIN deliveries d ON d.route_id   = r.route_id
    GROUP BY week, r.courier_id
),
ranked AS (
    SELECT week, courier, delivered,
           RANK() OVER (PARTITION BY week ORDER BY delivered DESC) AS rank_in_week
    FROM weekly
)
SELECT week, courier, delivered
FROM ranked
WHERE rank_in_week = 1
ORDER BY week;
