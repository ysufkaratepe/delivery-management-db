"""Command-line interface.

    python -m deliverydb build                     # create delivery.db
    python -m deliverydb run queries/07_window_rank.sql
    python -m deliverydb run-all                   # run every query file
    python -m deliverydb benchmark                 # index vs. no index
    python -m deliverydb demo-transaction          # constraint + rollback demo
"""

import argparse
import sqlite3
import sys
import time
from pathlib import Path

from .build import ROOT, build

DB = ROOT / "delivery.db"
QUERIES = ROOT / "queries"


def connect() -> sqlite3.Connection:
    if not DB.exists():
        print("delivery.db not found, building it first...")
        build(DB).close()
    con = sqlite3.connect(DB, cached_statements=0)  # always re-plan (needed for the benchmark)
    con.execute("PRAGMA foreign_keys = ON")
    return con


def print_table(cursor: sqlite3.Cursor, max_rows: int = 40) -> None:
    headers = [c[0] for c in cursor.description]
    rows = cursor.fetchall()
    shown = rows[:max_rows]
    cells = [[("" if v is None else str(v)) for v in r] for r in shown]
    widths = [max(len(h), *(len(r[i]) for r in cells)) if cells else len(h) for i, h in enumerate(headers)]
    print("  ".join(h.ljust(w) for h, w in zip(headers, widths)))
    print("  ".join("-" * w for w in widths))
    for r in cells:
        print("  ".join(v.ljust(w) for v, w in zip(r, widths)))
    if len(rows) > max_rows:
        print(f"... ({len(rows) - max_rows} more rows)")
    print(f"({len(rows)} rows)")


def run_file(con: sqlite3.Connection, path: Path) -> None:
    sql = path.read_text(encoding="utf-8")
    print(f"\n=== {path.name} ===")
    print_table(con.execute(sql))


def benchmark(con: sqlite3.Connection, repeats: int = 200) -> None:
    """Measures one query with and without the idx_packages_customer index."""
    query = "SELECT COUNT(*), SUM(weight_kg) FROM packages WHERE customer_id = ?"

    def measure() -> tuple[float, str]:
        plan = con.execute("EXPLAIN QUERY PLAN " + query, (1,)).fetchone()[-1]
        start = time.perf_counter()
        for i in range(repeats):
            con.execute(query, (i % 400 + 1,)).fetchone()
        return (time.perf_counter() - start) / repeats * 1000, plan

    with_ms, with_plan = measure()
    con.execute("DROP INDEX idx_packages_customer")
    without_ms, without_plan = measure()
    con.execute("CREATE INDEX idx_packages_customer ON packages(customer_id)")

    print(f"Query: {query}\n")
    print(f"Without index: {without_ms:7.3f} ms   plan: {without_plan}")
    print(f"With index   : {with_ms:7.3f} ms   plan: {with_plan}")
    print(f"\nThe index makes this query about {without_ms / with_ms:.0f}x faster.")


def demo_transaction(con: sqlite3.Connection) -> None:
    con.isolation_level = None  # manage BEGIN/ROLLBACK ourselves
    before = con.execute("SELECT COUNT(*) FROM deliveries").fetchone()[0]
    con.execute("BEGIN")
    try:
        con.execute("INSERT INTO packages(package_id, customer_id, weight_kg) VALUES (999999, 1, 2.5)")
        con.execute("INSERT INTO deliveries(route_id, package_id, stop_order) VALUES (1, 999999, 1000)")
        print("1st insert OK")
        con.execute("INSERT INTO deliveries(route_id, package_id, stop_order) VALUES (1, 999999, 1001)")
        con.execute("COMMIT")
    except sqlite3.IntegrityError as e:
        print(f"2nd insert rejected: {e}")
        con.execute("ROLLBACK")
        print("Transaction rolled back.")
    after = con.execute("SELECT COUNT(*) FROM deliveries").fetchone()[0]
    print(f"Deliveries before: {before}, after: {after} (unchanged)")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m deliverydb")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("build")
    run = sub.add_parser("run")
    run.add_argument("file")
    sub.add_parser("run-all")
    sub.add_parser("benchmark")
    sub.add_parser("demo-transaction")
    args = p.parse_args(argv)

    if args.command == "build":
        build(DB).close()
        print(f"Database created: {DB}")
        return 0

    con = connect()
    if args.command == "run":
        run_file(con, Path(args.file))
    elif args.command == "run-all":
        for f in sorted(QUERIES.glob("*.sql")):
            if f.name.startswith("12_"):
                continue  # multi-statement transaction demo, see demo-transaction
            run_file(con, f)
    elif args.command == "benchmark":
        benchmark(con)
    elif args.command == "demo-transaction":
        demo_transaction(con)
    return 0


if __name__ == "__main__":
    sys.exit(main())
