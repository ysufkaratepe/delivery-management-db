-- 10 · Using a VIEW and CASE
-- Question: Classify every route by its success rate, and count routes per class
--           for electric vs. diesel vans.
-- Concepts: route_summary is a VIEW defined in schema.sql (a saved query you can use
--           like a table); CASE turns numbers into categories.

SELECT CASE
           WHEN rs.success_rate >= 95 THEN 'excellent (>=95%)'
           WHEN rs.success_rate >= 90 THEN 'good (90-95%)'
           ELSE 'needs attention (<90%)'
       END                                              AS route_quality,
       SUM(v.is_electric = 1)                           AS electric_vans,
       SUM(v.is_electric = 0)                           AS diesel_vans,
       COUNT(*)                                         AS routes
FROM route_summary rs
JOIN vehicles v ON v.plate = rs.vehicle
GROUP BY route_quality
ORDER BY MIN(rs.success_rate) DESC;
