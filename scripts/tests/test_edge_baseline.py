import math

from edge_baseline import ARMS, build_summary, summarize


def test_summarize_math():
    s = summarize([0.1, -0.1, 0.3])
    assert s["n"] == 3
    assert math.isclose(s["meanExcess"], 0.1)
    assert s["medianExcess"] == 0.1
    assert math.isclose(s["tStat"], s["meanExcess"] / (s["sdExcess"] / math.sqrt(3)))
    assert math.isclose(s["beatRate"], 2 / 3)


def test_random_arm_deterministic_per_date():
    daily = {"market": "US", "date": "2026-01-02"}
    uni = [f"S{i}" for i in range(100)]
    a = ARMS["random"](daily, uni, 10, 0)
    assert len(a) == 10
    assert a == ARMS["random"](daily, list(reversed(uni)), 10, 0)
    assert a != ARMS["random"]({**daily, "date": "2026-01-03"}, uni, 10, 0)
    assert a != ARMS["random"](daily, uni, 10, 1)


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
