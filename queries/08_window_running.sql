-- 08 · Window functions: running total and moving average
-- Question: How many packages were delivered each day, the cumulative total,
--           and the 7-day moving average?
-- Concepts: SUM() OVER (ORDER BY ...) for running totals, a ROWS frame for moving averages,
--           LAG() to compare with the previous day.

WITH daily AS (
    SELECT r.route_date                 AS day,
           SUM(d.outcome = 'delivered') AS delivered
    FROM routes r
    JOIN deliveries d ON d.route_id = r.route_id
    GROUP BY r.route_date
)
SELECT day,
       delivered,
       delivered - LAG(delivered) OVER (ORDER BY day)              AS change_vs_prev,
       SUM(delivered) OVER (ORDER BY day)                          AS running_total,
       ROUND(AVG(delivered) OVER (ORDER BY day
                                  ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 1) AS moving_avg_7
FROM daily
ORDER BY day;
