-- 09 · Recursive CTE
-- Question: Show every calendar day in July 2026 and how many routes ran that day,
--           including days with no deliveries (Sundays).
-- Concepts: a recursive CTE generates rows (here: dates) that don't exist in any table,
--           then a LEFT JOIN fills in the data.

WITH RECURSIVE calendar(day) AS (
    SELECT DATE('2026-07-01')
    UNION ALL
    SELECT DATE(day, '+1 day') FROM calendar WHERE day < '2026-07-31'
)
SELECT cal.day,
       CASE strftime('%w', cal.day) WHEN '0' THEN 'Sunday' ELSE '' END AS note,
       COUNT(r.route_id) AS routes
FROM calendar cal
LEFT JOIN routes r ON r.route_date = cal.day
GROUP BY cal.day
ORDER BY cal.day;
