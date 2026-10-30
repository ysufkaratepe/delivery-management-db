-- 01 · SELECT, WHERE, ORDER BY, LIMIT
-- Question: Which electric vans do we have, largest capacity first?
-- Concepts: filtering rows with WHERE, sorting, limiting the result.

SELECT plate, model, capacity
FROM vehicles
WHERE is_electric = 1
ORDER BY capacity DESC, plate
LIMIT 10;
