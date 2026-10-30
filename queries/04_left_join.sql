-- 04 · LEFT JOIN to find missing data
-- Question: How many routes did each courier drive? Include couriers with zero routes.
-- Concepts: LEFT JOIN keeps every row from the left table even without a match;
--           COUNT(column) counts only non-NULL values.

SELECT c.full_name,
       c.is_active,
       COUNT(r.route_id) AS routes_driven
FROM couriers c
LEFT JOIN routes r ON r.courier_id = c.courier_id
GROUP BY c.courier_id
ORDER BY routes_driven DESC;
