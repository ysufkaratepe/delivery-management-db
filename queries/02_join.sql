-- 02 · INNER JOIN across several tables
-- Question: Show the first 10 stops of route 1 with the customer and district.
-- Concepts: joining tables through their foreign keys.

SELECT d.stop_order,
       c.full_name  AS customer,
       ds.name      AS district,
       p.weight_kg,
       d.outcome
FROM deliveries d
JOIN packages  p  ON p.package_id  = d.package_id
JOIN customers c  ON c.customer_id = p.customer_id
JOIN districts ds ON ds.district_id = c.district_id
WHERE d.route_id = 1
ORDER BY d.stop_order
LIMIT 10;
