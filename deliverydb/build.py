"""Builds the SQLite database: creates the schema and fills it with sample data.

The data is random but reproducible (fixed seed), so every run produces
exactly the same database and the tests always see the same numbers.
"""

import random
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "schema.sql"

DISTRICTS = [
    "Innenstadt", "Herrnsheim", "Pfeddersheim", "Horchheim", "Hochheim", "Neuhausen",
    "Pfiffligheim", "Leiselheim", "Rheindürkheim", "Abenheim", "Weinsheim",
    "Wiesoppenheim", "Heppenheim", "Ibersheim",
]
FIRST_NAMES = ["Anna", "Ben", "Clara", "David", "Elif", "Felix", "Greta", "Hasan", "Ida", "Jonas",
               "Lea", "Mehmet", "Nina", "Omar", "Paula", "Yusuf", "Sara", "Tim", "Zeynep", "Lukas"]
LAST_NAMES = ["Schmidt", "Müller", "Yılmaz", "Weber", "Fischer", "Kaya", "Wagner", "Becker",
              "Demir", "Hoffmann", "Schulz", "Koch", "Richter", "Klein", "Wolf"]
VAN_MODELS = [("Mercedes eSprinter", 1, 180), ("Mercedes Sprinter", 0, 200), ("Ford E-Transit", 1, 170)]

START_DATE = date(2026, 7, 1)
DAYS = 60
N_COURIERS = 12
N_VEHICLES = 14
N_CUSTOMERS = 400


def _name(rng: random.Random) -> str:
    return f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"


def build(db_path: str | Path = ":memory:", seed: int = 42) -> sqlite3.Connection:
    """Creates the database at `db_path` and returns an open connection."""
    if db_path != ":memory:":
        Path(db_path).unlink(missing_ok=True)

    rng = random.Random(seed)
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(SCHEMA.read_text(encoding="utf-8"))

    con.executemany("INSERT INTO districts(district_id, name) VALUES (?, ?)",
                    list(enumerate(DISTRICTS, start=1)))

    couriers = [(i, _name(rng), (START_DATE - timedelta(days=rng.randint(0, 700))).isoformat(),
                 0 if i == N_COURIERS else 1)  # one courier has left the company
                for i in range(1, N_COURIERS + 1)]
    con.executemany("INSERT INTO couriers VALUES (?, ?, ?, ?)", couriers)

    vehicles = []
    for i in range(1, N_VEHICLES + 1):
        model, electric, capacity = rng.choice(VAN_MODELS)
        vehicles.append((i, f"WO-AZ {1000 + i}", model, electric, capacity))
    con.executemany("INSERT INTO vehicles VALUES (?, ?, ?, ?, ?)", vehicles)

    # Some districts are busier than others
    district_weights = [rng.uniform(0.5, 3.0) for _ in DISTRICTS]
    customers = [(i, _name(rng), rng.choices(range(1, len(DISTRICTS) + 1), district_weights)[0])
                 for i in range(1, N_CUSTOMERS + 1)]
    con.executemany("INSERT INTO customers VALUES (?, ?, ?)", customers)

    # Each courier has a personal skill level that affects success rate and speed
    skill = {c[0]: rng.uniform(0.86, 0.98) for c in couriers}
    active = [c[0] for c in couriers if c[3] == 1]

    package_id = 0
    route_id = 0
    for day in range(DAYS):
        d = START_DATE + timedelta(days=day)
        if d.weekday() == 6:  # no deliveries on Sunday
            continue
        working = rng.sample(active, k=rng.randint(7, len(active)))
        vans = rng.sample(range(1, N_VEHICLES + 1), k=len(working))
        for courier_id, vehicle_id in zip(working, vans):
            route_id += 1
            n_stops = rng.randint(60, 120)
            distance = round(n_stops * rng.uniform(0.35, 0.55), 1)
            con.execute("INSERT INTO routes VALUES (?, ?, ?, ?, ?)",
                        (route_id, d.isoformat(), courier_id, vehicle_id, distance))

            t = datetime(d.year, d.month, d.day, 9, 0)
            for stop in range(1, n_stops + 1):
                package_id += 1
                con.execute("INSERT INTO packages(package_id, customer_id, weight_kg) VALUES (?, ?, ?)",
                            (package_id, rng.randint(1, N_CUSTOMERS), round(rng.uniform(0.2, 15.0), 1)))
                con.execute("INSERT INTO deliveries(route_id, package_id, stop_order) VALUES (?, ?, ?)",
                            (route_id, package_id, stop))

                # Record the attempt (fires the trigger that updates the package status)
                t += timedelta(minutes=rng.uniform(2.0, 6.5) / skill[courier_id])
                outcome = "delivered" if rng.random() < skill[courier_id] else "failed"
                con.execute("UPDATE deliveries SET outcome = ?, attempted_at = ? "
                            "WHERE route_id = ? AND stop_order = ?",
                            (outcome, t.isoformat(sep=" ", timespec="minutes"), route_id, stop))

    con.commit()
    return con


if __name__ == "__main__":
    out = ROOT / "delivery.db"
    build(out).close()
    print(f"Database created: {out}")
