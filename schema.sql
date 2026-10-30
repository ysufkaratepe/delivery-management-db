-- Delivery Management DB: schema
-- A small model of a last-mile delivery station, like the one I worked at
-- in Worms, Germany (summer 2026).

PRAGMA foreign_keys = ON;

-- People who deliver packages
CREATE TABLE couriers (
    courier_id   INTEGER PRIMARY KEY,
    full_name    TEXT    NOT NULL,
    hired_on     DATE    NOT NULL,
    is_active    INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1))
);

-- Delivery vans
CREATE TABLE vehicles (
    vehicle_id    INTEGER PRIMARY KEY,
    plate         TEXT    NOT NULL UNIQUE,
    model         TEXT    NOT NULL,
    is_electric   INTEGER NOT NULL CHECK (is_electric IN (0, 1)),
    capacity      INTEGER NOT NULL CHECK (capacity > 0)       -- max packages per route
);

-- Neighbourhoods (districts) of the city
CREATE TABLE districts (
    district_id  INTEGER PRIMARY KEY,
    name         TEXT NOT NULL UNIQUE
);

CREATE TABLE customers (
    customer_id  INTEGER PRIMARY KEY,
    full_name    TEXT    NOT NULL,
    district_id  INTEGER NOT NULL REFERENCES districts(district_id)
);

-- One route = one courier driving one vehicle on one day
CREATE TABLE routes (
    route_id     INTEGER PRIMARY KEY,
    route_date   DATE    NOT NULL,
    courier_id   INTEGER NOT NULL REFERENCES couriers(courier_id),
    vehicle_id   INTEGER NOT NULL REFERENCES vehicles(vehicle_id),
    distance_km  REAL    NOT NULL CHECK (distance_km >= 0),
    UNIQUE (route_date, courier_id),   -- a courier drives one route per day
    UNIQUE (route_date, vehicle_id)    -- a van is used once per day
);

CREATE TABLE packages (
    package_id   INTEGER PRIMARY KEY,
    customer_id  INTEGER NOT NULL REFERENCES customers(customer_id),
    weight_kg    REAL    NOT NULL CHECK (weight_kg > 0),
    status       TEXT    NOT NULL DEFAULT 'pending'
                 CHECK (status IN ('pending', 'out_for_delivery', 'delivered', 'failed'))
);

-- A package placed on a route, in a given stop order
CREATE TABLE deliveries (
    delivery_id   INTEGER PRIMARY KEY,
    route_id      INTEGER NOT NULL REFERENCES routes(route_id),
    package_id    INTEGER NOT NULL REFERENCES packages(package_id),
    stop_order    INTEGER NOT NULL CHECK (stop_order > 0),
    outcome       TEXT    CHECK (outcome IN ('delivered', 'failed')),  -- NULL = not attempted yet
    attempted_at  DATETIME,
    UNIQUE (route_id, stop_order),
    UNIQUE (route_id, package_id)
);

-- Indexes for the columns we filter and join on most often
CREATE INDEX idx_routes_date        ON routes(route_date);
CREATE INDEX idx_routes_courier     ON routes(courier_id);
CREATE INDEX idx_deliveries_route   ON deliveries(route_id);
CREATE INDEX idx_deliveries_package ON deliveries(package_id);
CREATE INDEX idx_customers_district ON customers(district_id);
CREATE INDEX idx_packages_customer  ON packages(customer_id);

-- Trigger: keep packages.status in sync when a delivery attempt is recorded
CREATE TRIGGER trg_delivery_outcome
AFTER UPDATE OF outcome ON deliveries
WHEN NEW.outcome IS NOT NULL
BEGIN
    UPDATE packages SET status = NEW.outcome WHERE package_id = NEW.package_id;
END;

-- Trigger: a package that goes on a route is now out for delivery
CREATE TRIGGER trg_delivery_assigned
AFTER INSERT ON deliveries
WHEN NEW.outcome IS NULL
BEGIN
    UPDATE packages SET status = 'out_for_delivery' WHERE package_id = NEW.package_id;
END;

-- View: one row per route with its daily numbers
CREATE VIEW route_summary AS
SELECT
    r.route_id,
    r.route_date,
    c.full_name                                         AS courier,
    v.plate                                             AS vehicle,
    r.distance_km,
    COUNT(d.delivery_id)                                AS stops,
    SUM(d.outcome = 'delivered')                        AS delivered,
    SUM(d.outcome = 'failed')                           AS failed,
    ROUND(100.0 * SUM(d.outcome = 'delivered') / COUNT(d.delivery_id), 1) AS success_rate
FROM routes r
JOIN couriers   c ON c.courier_id = r.courier_id
JOIN vehicles   v ON v.vehicle_id = r.vehicle_id
JOIN deliveries d ON d.route_id   = r.route_id
GROUP BY r.route_id;
