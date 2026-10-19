import math

import pandas as pd
from config import MIN_MARKET_CAP_US
from edge_baseline import (
    ARMS,
    ArmContext,
    CapEstimator,
    build_rows,
    build_summary,
    load_cap_estimator,
    summarize,
)


def test_summarize_math():
    s = summarize([0.1, -0.1, 0.3])
    assert s["n"] == 3
    assert math.isclose(s["meanExcess"], 0.1)
    assert s["medianExcess"] == 0.1
    assert math.isclose(s["tStat"], s["meanExcess"] / (s["sdExcess"] / math.sqrt(3)))
    assert math.isclose(s["beatRate"], 2 / 3)


def _bars(at_pick: float, at_latest: float):
    idx = pd.to_datetime(["2026-10-01", "2026-10-09", "2026-10-12", "2026-11-20"])
    return pd.DataFrame(
        {"Open": 1.0, "Close": [at_pick, at_latest, at_latest, at_latest]}, index=idx
    )


DAILY = {"market": "US", "date": "2026-10-01", "status": "pick", "stock": {"symbol": "PICK"}}
FLOOR = MIN_MARKET_CAP_US


def _estimator(latest: dict, snapshots: dict | None = None):
    snapshots = snapshots or {}
    return CapEstimator(
        "US", "2026-10-09", latest, snapshots.get, frozenset(snapshots) | {"2026-10-09"}
    )


def _rows(latest, bars, snapshots=None):
    prices = {s: _bars(*b) for s, b in bars.items()}
    rows = build_rows(
        dailies=[DAILY],
        universes={"US": sorted(latest), "KR": []},
        as_of_date="2026-12-01",
        price_provider=lambda sym, mkt: prices[sym],
        benchmark_provider=lambda _id: _bars(100, 100),
        random_k=5,
        seed=0,
        estimators={"US": _estimator(latest, snapshots)},
    )
    return {a: [r for r in rows if r["arm"] == a] for a in ARMS}


def test_random_rejects_symbol_below_floor_at_pick_date():
    # SHRUNK clears the floor on its latest cap but its price doubled after the pick date
    latest = {"PICK": 10 * FLOOR, "SHRUNK": 1.5 * FLOOR, "BIG": 5 * FLOOR}
    by_arm = _rows(latest, {"PICK": (1, 1), "SHRUNK": (1, 2), "BIG": (1, 1)})
    assert {r["symbol"] for r in by_arm["random"]} == {"PICK", "BIG"}
    assert all(r["capBasis"] == "price_rescaled" for r in by_arm["random"])


def test_size_matched_stays_within_band_and_excludes_pick():
    pick = 10 * FLOOR
    latest = {
        "PICK": pick,
        "IN_LO": pick / 1.9,
        "IN_HI": pick * 1.9,
        "OUT_HI": pick * 2.5,
        "OUT_LO": pick / 2.5,
        "SHRUNK": pick,  # latest cap in band, cap at pick date is pick/4
    }
    bars = {s: (1, 1) for s in latest}
    bars["SHRUNK"] = (1, 4)
    by_arm = _rows(latest, bars)
    assert {r["symbol"] for r in by_arm["size_matched"]} == {"IN_LO", "IN_HI"}


def test_pit_snapshot_cap_wins_over_rescaling():
    est = _estimator({"X": 100.0}, {"2026-10-01": {"X": 7.0}})
    assert est.cap_at("X", "2026-10-01", _bars(1, 2)) == (7.0, "pit_snapshot")
    assert est.cap_at("X", "2026-10-05", _bars(1, 2)) == (50.0, "price_rescaled")
    assert est.cap_at("Y", "2026-10-05", _bars(1, 2)) is None


def test_cap_at_reads_date_column_bars():
    bars = _bars(1, 2).rename_axis("date").reset_index()
    assert _estimator({"X": 100.0}).cap_at("X", "2026-10-05", bars) == (50.0, "price_rescaled")


def test_rows_carry_cap_and_survivorship_flag():
    by_arm = _rows({"PICK": 10 * FLOOR}, {"PICK": (1, 1)}, {"2026-10-01": {"PICK": 3.0}})
    (pick,) = by_arm["pick"]
    assert (pick["capAtPick"], pick["capBasis"]) == (3.0, "pit_snapshot")
    assert pick["survivorshipBias"] == "pit_universe"


def test_missing_pit_skips_size_matched_and_random_falls_back():
    rows = build_rows(
        dailies=[DAILY],
        universes={"US": ["PICK", "A", "B"], "KR": []},
        floor_universes={"US": ["A"]},
        as_of_date="2026-12-01",
        price_provider=lambda sym, mkt: _bars(1, 1),
        benchmark_provider=lambda _id: _bars(100, 100),
        random_k=5,
        seed=0,
        estimators={"US": None},
    )
    assert not [r for r in rows if r["arm"] == "size_matched"]
    assert [r["symbol"] for r in rows if r["arm"] == "random"] == ["A"]
    assert {r["survivorshipBias"] for r in rows} == {"current_universe"}


def test_load_cap_estimator_none_when_pit_dir_missing(monkeypatch, tmp_path):
    monkeypatch.setenv("PIT_DATA_DIR", str(tmp_path / "absent"))
    assert load_cap_estimator("KR") is None


def test_random_arm_deterministic_per_date():
    uni = [f"S{i}" for i in range(100)]

    def order(universe, date="2026-01-02", seed=0):
        ctx = ArmContext({"market": "US", "date": date}, universe, universe, 10, seed, None, None)
        return ARMS["random"].candidates(ctx)

    a = order(uni)
    assert a == order(list(reversed(uni)))
    assert a != order(uni, date="2026-01-03")
    assert a != order(uni, seed=1)


def test_summary_skips_incomplete_and_diffs_arms():
    def r(arm, ex, day="2026-01-02"):
        return {"market": "US", "arm": arm, "excess": ex, "pickDate": day}

    s = build_summary(
        [
            r("pick", 0.2),
            r("random", 0.05),
            r("random", None),
            r("random", 0.15),
            r("pick", 0.0, "2026-01-05"),
            r("random", 0.1, "2026-01-05"),
            r("random", 0.3, "2026-01-06"),
        ]
    )
    assert s["US"]["random"]["n"] == 4
    paired = s["US"]["pickMinus"]["random"]
    assert paired["n"] == 2, "one diff per date that has both arms"
    assert math.isclose(paired["meanExcess"], 0.0)
    assert s["US"]["pickMinus"]["top2_5"]["n"] == 0
