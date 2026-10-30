import sqlite3
from pathlib import Path

import pytest

from deliverydb.__main__ import main
from deliverydb.build import build

QUERIES = Path(__file__).resolve().parent.parent / "queries"


@pytest.fixture(scope="module")
def con():
    c = build(":memory:")
    yield c
    c.close()


def run(con, name):
    sql = (QUERIES / name).read_text(encoding="utf-8")
    return con.execute(sql).fetchall()


def test_build_is_reproducible():
    a = build(":memory:").execute("SELECT SUM(distance_km), COUNT(*) FROM routes").fetchone()
    b = build(":memory:").execute("SELECT SUM(distance_km), COUNT(*) FROM routes").fetchone()
    assert a == b


def test_every_package_is_on_exactly_one_route(con):
    assert con.execute("""
        SELECT COUNT(*) FROM packages p
        WHERE (SELECT COUNT(*) FROM deliveries d WHERE d.package_id = p.package_id) <> 1
    """).fetchone()[0] == 0


def test_trigger_keeps_package_status_in_sync(con):
    mismatches = con.execute("""
        SELECT COUNT(*) FROM deliveries d JOIN packages p ON p.package_id = d.package_id
        WHERE d.outcome <> p.status
    """).fetchone()[0]
    assert mismatches == 0


def test_no_routes_on_sunday(con):
    assert con.execute("SELECT COUNT(*) FROM routes WHERE strftime('%w', route_date) = '0'").fetchone()[0] == 0


def test_foreign_keys_are_enforced(con):
    with pytest.raises(sqlite3.IntegrityError):
        con.execute("INSERT INTO deliveries(route_id, package_id, stop_order) VALUES (999999, 1, 1)")


def test_check_constraint(con):
    with pytest.raises(sqlite3.IntegrityError):
        con.execute("INSERT INTO packages(customer_id, weight_kg) VALUES (1, -3)")


@pytest.mark.parametrize("name", sorted(p.name for p in QUERIES.glob("*.sql") if not p.name.startswith("12_")))
def test_every_query_runs(con, name):
    assert len(run(con, name)) > 0


def test_left_join_includes_courier_without_routes(con):
    rows = run(con, "04_left_join.sql")
    assert any(r[2] == 0 for r in rows)


def test_having_filters_groups(con):
    assert all(r[3] > 6 for r in run(con, "03_group_by_having.sql"))


def test_running_total_matches_sum(con):
    rows = run(con, "08_window_running.sql")
    assert rows[-1][3] == sum(r[1] for r in rows)
    assert rows[-1][3] == con.execute("SELECT COUNT(*) FROM deliveries WHERE outcome = 'delivered'").fetchone()[0]


def test_weekly_rank_one_winner_per_week(con):
    rows = run(con, "07_window_rank.sql")
    weeks = [r[0] for r in rows]
    assert len(weeks) >= len(set(weeks)) > 5


def test_recursive_calendar_has_31_days(con):
    rows = run(con, "09_recursive_cte.sql")
    assert len(rows) == 31
    assert all(r[2] == 0 for r in rows if r[1] == "Sunday")


def test_view_classes_cover_all_routes(con):
    total = sum(r[3] for r in run(con, "10_view_and_case.sql"))
    assert total == con.execute("SELECT COUNT(*) FROM routes").fetchone()[0]


def test_query_uses_index(con):
    plan = run(con, "11_index_explain.sql")[0][-1]
    assert "USING INDEX" in plan


def test_cli_commands(capsys, tmp_path, monkeypatch):
    import deliverydb.__main__ as cli
    monkeypatch.setattr(cli, "DB", tmp_path / "test.db")
    assert main(["build"]) == 0
    assert main(["benchmark"]) == 0
    assert main(["demo-transaction"]) == 0
    out = capsys.readouterr().out
    assert "SCAN packages" in out and "USING INDEX" in out
    assert "rolled back" in out
