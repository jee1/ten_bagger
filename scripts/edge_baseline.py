#!/usr/bin/env python3
"""Compare the live Score v2 pick with simple baselines on H20 excess return."""

from __future__ import annotations

import argparse
import json
import math
import random
import statistics
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from config import DAILY_DIR
from performance.load_dailies import load_eligible_dailies
from performance.prices_live import default_benchmark_provider, default_price_provider
from performance.returns import BENCHMARK_IDS, measure_pick_horizon
from regenerate_ledger import _validate_as_of_date
from screening.core import load_universe, passes_market_cap_filter

SCHEMA_VERSION = "0.1.0"
HORIZON = "H20"
MARKETS = ("KR", "US")
EDGE_DIR = Path(__file__).resolve().parent.parent / "content" / "edge-baseline"
LIMITATIONS = [
    "US listings carry no market cap, so only KR random applies the cap floor",
    "survivorship: random arm samples the current listing, delisted names are absent",
    "per-arm tStat treats same-date rows as independent; read pickMinus (paired by date) instead",
    "overlapping windows: consecutive H20 windows overlap, so even paired tStat is overstated",
    "small n: tens of observations per arm; tStat near zero is not proof of equality",
    "top2_5 and random arms were never published; only the measurement semantics match",
]


def _top2_5(daily: dict, universe: list[str], k: int, seed: int) -> list[str]:
    return [c["symbol"] for c in daily.get("topCandidates") or [] if 2 <= c["rank"] <= 5]


def _random(daily: dict, universe: list[str], k: int, seed: int) -> list[str]:
    rng = random.Random(f"{seed}:{daily['market']}:{daily['date']}")
    return rng.sample(sorted(universe), min(k, len(universe)))


# arm name -> (daily, universe, randomK, seed) -> symbols
ARMS: dict[str, Callable[[dict, list[str], int, int], list[str]]] = {
    "pick": lambda d, u, k, s: [d["stock"]["symbol"]],
    "top2_5": _top2_5,
    "random": _random,
}


def summarize(excess: list[float]) -> dict[str, Any]:
    n = len(excess)
    if n == 0:
        return {"n": 0}
    mean = statistics.fmean(excess)
    sd = statistics.stdev(excess) if n > 1 else None
    return {
        "n": n,
        "meanExcess": mean,
        "medianExcess": statistics.median(excess),
        "sdExcess": sd,
        "tStat": mean / (sd / math.sqrt(n)) if sd else None,
        "beatRate": sum(e > 0 for e in excess) / n,
    }


def build_summary(rows: list[dict]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for market in sorted({r["market"] for r in rows}):
        arms: dict[str, Any] = {
            arm: summarize(
                [
                    r["excess"]
                    for r in rows
                    if r["market"] == market and r["arm"] == arm and r["excess"] is not None
                ]
            )
            for arm in ARMS
        }
        arms["pickMinus"] = {
            arm: summarize(_paired_by_date(rows, market, arm)) for arm in ARMS if arm != "pick"
        }
        out[market] = arms
    return out


def _paired_by_date(rows: list[dict], market: str, arm: str) -> list[float]:
    # Rows sharing a pickDate share the benchmark window, so they are not independent;
    # the comparison unit is the date: pick excess minus that date's arm mean.
    by_date: dict[str, dict[str, list[float]]] = {}
    for r in rows:
        if r["market"] == market and r["excess"] is not None and r["arm"] in ("pick", arm):
            by_date.setdefault(r["pickDate"], {}).setdefault(r["arm"], []).append(r["excess"])
    return [
        g["pick"][0] - statistics.fmean(g[arm])
        for _, g in sorted(by_date.items())
        if "pick" in g and arm in g
    ]


def _row(m: dict, arm: str) -> dict:
    fr, br = m.get("forwardReturn"), m.get("benchmarkReturn")
    done = m["completionStatus"] == "complete" and m["benchmarkCompletionStatus"] == "complete"
    return {
        "pickDate": m["pickDate"],
        "market": m["market"],
        "arm": arm,
        "symbol": m["symbol"],
        "entryPrice": m.get("entryPrice"),
        "exitPrice": m.get("exitPrice"),
        "forwardReturn": fr,
        "benchmarkReturn": br,
        "excess": fr - br if done else None,
        "completionStatus": "complete" if done else "incomplete",
    }


def build_rows(
    *,
    dailies: list[dict],
    universes: dict[str, list[str]],
    as_of_date: str,
    price_provider,
    benchmark_provider,
    random_k: int,
    seed: int,
) -> list[dict]:
    bars_cache: dict[tuple[str, str], Any] = {}
    bench = {m: benchmark_provider(BENCHMARK_IDS[m]) for m in MARKETS}
    rows: list[dict] = []
    for daily in dailies:
        market = daily["market"]
        if daily["status"] != "pick" or market not in MARKETS:
            continue
        for arm, symbols_for in ARMS.items():
            for symbol in symbols_for(daily, universes[market], random_k, seed):
                key = (symbol, market)
                if key not in bars_cache:
                    try:
                        bars_cache[key] = price_provider(symbol, market)
                    except Exception as exc:
                        print(f"warn: bars failed {symbol}: {exc}", file=sys.stderr)
                        bars_cache[key] = None
                bars = bars_cache[key]
                if bars is None or bars.empty:
                    m = {
                        "pickDate": daily["date"],
                        "market": market,
                        "symbol": symbol,
                        "completionStatus": "incomplete",
                        "benchmarkCompletionStatus": "incomplete",
                    }
                else:
                    m = measure_pick_horizon(
                        bars=bars,
                        benchmark_bars=bench[market],
                        pick_date=daily["date"],
                        as_of_date=as_of_date,
                        market=market,
                        symbol=symbol,
                        horizon_id=HORIZON,
                    )
                rows.append(_row(m, arm))
    return rows


def run(
    *,
    as_of_date: str,
    random_k: int,
    seed: int,
    out_dir: Path,
    price_provider=None,
    benchmark_provider=None,
    universes: dict[str, list[str]] | None = None,
    daily_dir: Path | None = None,
) -> Path:
    dailies = load_eligible_dailies(daily_dir or DAILY_DIR, as_of_date)
    universes = universes or {
        m: [u.symbol for u in load_universe(m) if passes_market_cap_filter(u, m)] for m in MARKETS
    }
    rows = build_rows(
        dailies=dailies,
        universes=universes,
        as_of_date=as_of_date,
        price_provider=price_provider or default_price_provider(as_of_date),
        benchmark_provider=benchmark_provider or default_benchmark_provider(as_of_date),
        random_k=random_k,
        seed=seed,
    )
    doc = {
        "schemaVersion": SCHEMA_VERSION,
        "asOfDate": as_of_date,
        "generatedAt": datetime.now(UTC).isoformat(),
        "params": {"horizon": HORIZON, "randomK": random_k, "seed": seed},
        "survivorshipBias": "current_universe",
        "limitations": LIMITATIONS,
        "summary": build_summary(rows),
        "rows": rows,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{as_of_date}.json"
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="edge_baseline.py")
    ap.add_argument("--as-of-date", required=True)
    ap.add_argument("--random-k", type=int, default=10)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args(argv)
    as_of = _validate_as_of_date(args.as_of_date)
    if not as_of:
        print("error: --as-of-date YYYY-MM-DD is required", file=sys.stderr)
        return 2
    path = run(as_of_date=as_of, random_k=args.random_k, seed=args.seed, out_dir=EDGE_DIR)
    print(json.dumps(json.loads(path.read_text())["summary"], indent=2))
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
