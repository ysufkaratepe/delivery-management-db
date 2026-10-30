-- 03 · GROUP BY and HAVING
-- Question: Which districts have a failed-delivery rate above 6%?
-- Concepts: aggregate functions (COUNT, SUM), grouping, filtering groups with HAVING
--           (WHERE filters rows before grouping, HAVING filters groups after).

SELECT ds.name                                        AS district,
       COUNT(*)                                       AS attempts,
       SUM(d.outcome = 'failed')                      AS failed,
       ROUND(100.0 * SUM(d.outcome = 'failed') / COUNT(*), 2) AS failed_pct
FROM deliveries d
JOIN packages  p  ON p.package_id   = d.package_id
JOIN customers c  ON c.customer_id  = p.customer_id
JOIN districts ds ON ds.district_id = c.district_id
GROUP BY ds.district_id
HAVING failed_pct > 6
ORDER BY failed_pct DESC;
