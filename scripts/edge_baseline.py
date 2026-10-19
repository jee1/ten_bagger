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
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import cache
from pathlib import Path
from typing import Any

import pandas as pd
from config import DAILY_DIR, MIN_MARKET_CAP_KR, MIN_MARKET_CAP_US, PIT_MANIFEST_PATH
from performance.load_dailies import load_eligible_dailies
from performance.pit_prices import prefer_adjusted
from performance.prices_live import default_benchmark_provider, default_price_provider
from performance.returns import BENCHMARK_IDS, measure_pick_horizon
from regenerate_ledger import _validate_as_of_date
from screening.core import load_universe, passes_market_cap_filter
from walk_forward.fundamentals_pit import load_fundamentals_snapshot, pit_data_dir

SCHEMA_VERSION = "0.2.0"
HORIZON = "H20"
MARKETS = ("KR", "US")
EDGE_DIR = Path(__file__).resolve().parent.parent / "content" / "edge-baseline"
MIN_MARKET_CAP = {"KR": MIN_MARKET_CAP_KR, "US": MIN_MARKET_CAP_US}
SIZE_BAND = 2  # size_matched accepts caps within [pick/2, pick*2]
PREFILTER_BAND = 4  # candidate pool narrowed on latest-snapshot cap before fetching bars
MAX_ATTEMPTS_PER_K = 5
LIMITATIONS = [
    "random and size_matched filter on the cap at pick date: the PIT snapshot cap when one exists, "
    "otherwise the newest snapshot cap holding the symbol rescaled by close(pick)/close(snapshot), "
    "which assumes a constant share count",
    "info_rescaled (symbols in no snapshot) uses today's marketCap from a live yfinance quote, "
    "so its share count is today's, not the pick date's",
    "survivorship: names delisted before the first PIT snapshot (2026-10-09) are absent; "
    "rows with survivorshipBias=current_universe sample today's listing",
    "per-arm tStat treats same-date rows as independent; read pickMinus (paired by date) instead",
    "overlapping windows: consecutive H20 windows overlap, so even paired tStat is overstated",
    "small n: tens of observations per arm; tStat near zero is not proof of equality",
    "top2_5, random and size_matched arms were never published; only the measurement semantics "
    "match",
]


@dataclass(frozen=True)
class CapEstimator:
    """Market cap at a pick date for one market, from PIT snapshots."""

    market: str
    latest_date: str
    latest_caps: dict[str, float]
    snapshot_caps: Callable[[str], dict[str, float] | None]  # date -> caps, None if no snapshot
    pit_dates: frozenset[str]  # dates with a fundamentals + universe snapshot
    info_cap: Callable[[str], float | None] | None = None  # live yfinance marketCap, last resort

    def cap_at(
        self, symbol: str, pick_date: str, bars: pd.DataFrame | None
    ) -> tuple[float, str] | None:
        snap = self.snapshot_caps(pick_date) if pick_date in self.pit_dates else None
        if snap and symbol in snap:
            return snap[symbol], "pit_snapshot"
        if bars is None or bars.empty:
            return None
        at_pick = _close_on_or_before(bars, pick_date)
        if not at_pick:
            return None
        # Snapshots omit symbols dropped before scoring (duplicate ban, cap floor), so walk back
        # to the newest snapshot that holds the symbol.
        for date in sorted(self.pit_dates, reverse=True):
            cap = (self.snapshot_caps(date) or {}).get(symbol)
            at_snap = _close_on_or_before(bars, date) if cap else None
            if cap and at_snap:
                return cap * at_pick / at_snap, "price_rescaled"
        live = self.info_cap(symbol) if self.info_cap else None
        at_last = _close_on_or_before(bars, "9999-12-31")
        if live and at_last:
            return live * at_pick / at_last, "info_rescaled"
        return None


def _close_on_or_before(bars: pd.DataFrame, session: str) -> float | None:
    adj, _ = prefer_adjusted(bars)
    if "Close" not in adj.columns:
        return None
    dates = pd.DatetimeIndex(pd.to_datetime(adj["date"] if "date" in adj.columns else adj.index))
    close = pd.Series(adj["Close"].to_numpy(), index=dates.strftime("%Y-%m-%d")).dropna()
    close = close[close.index <= session].sort_index()
    return float(close.iloc[-1]) if len(close) else None


def load_cap_estimator(market: str) -> CapEstimator | None:
    """None when the PIT clone or its manifest entries for *market* are unavailable."""
    if not PIT_MANIFEST_PATH.exists() or not pit_data_dir().is_dir():
        return None
    manifest = json.loads(PIT_MANIFEST_PATH.read_text(encoding="utf-8"))
    dates = sorted(e["date"] for e in manifest.get("entries") or [] if e.get("market") == market)

    @cache
    def caps(date: str) -> dict[str, float] | None:
        snap = load_fundamentals_snapshot(market, date)
        if snap is None:
            return None
        return {
            sym: float(info["marketCap"])
            for sym, info in snap.infos.items()
            if isinstance(info.get("marketCap"), int | float) and info["marketCap"] > 0
        }

    latest = caps(dates[-1]) if dates else None
    if not latest:
        return None
    return CapEstimator(market, dates[-1], latest, caps, frozenset(dates), _live_info_cap)


def _live_info_cap(symbol: str) -> float | None:
    from yf_cache import get_ticker_info

    try:
        cap = get_ticker_info(symbol).get("marketCap")
    except Exception as exc:
        print(f"warn: info failed {symbol}: {exc}", file=sys.stderr)
        return None
    return float(cap) if isinstance(cap, int | float) and cap > 0 else None


@dataclass(frozen=True)
class ArmContext:
    daily: dict
    universe: list[str]  # every listed symbol
    floor_universe: list[str]  # current-cap prefiltered; random fallback without PIT
    k: int
    seed: int
    est: CapEstimator | None
    pick_cap: float | None

    @property
    def market(self) -> str:
        return self.daily["market"]

    def shuffled(self, symbols: list[str], salt: str = "") -> list[str]:
        rng = random.Random(f"{self.seed}:{self.market}:{self.daily['date']}{salt}")
        order = sorted(symbols)
        rng.shuffle(order)
        return order


@dataclass(frozen=True)
class Arm:
    candidates: Callable[[ArmContext], list[str]]  # ordered; sampled arms walk it in order
    accept: Callable[[ArmContext, float | None], bool] | None = None
    sampled: bool = False  # stop after k accepted or MAX_ATTEMPTS_PER_K * k tried
    needs_pit: bool = False


def _top2_5_symbols(ctx: ArmContext) -> list[str]:
    return [c["symbol"] for c in ctx.daily.get("topCandidates") or [] if 2 <= c["rank"] <= 5]


def _random_candidates(ctx: ArmContext) -> list[str]:
    return ctx.shuffled(ctx.universe if ctx.est else ctx.floor_universe)


def _random_accepts(ctx: ArmContext, cap: float | None) -> bool:
    return ctx.est is None or (cap is not None and cap >= MIN_MARKET_CAP[ctx.market])


def _size_matched_candidates(ctx: ArmContext) -> list[str]:
    if ctx.est is None or ctx.pick_cap is None:
        return []
    lo, hi = ctx.pick_cap / PREFILTER_BAND, ctx.pick_cap * PREFILTER_BAND
    excluded = {ctx.daily["stock"]["symbol"], *_top2_5_symbols(ctx)}
    pool = [
        s for s in ctx.universe if s not in excluded and lo <= ctx.est.latest_caps.get(s, 0) <= hi
    ]
    return ctx.shuffled(pool, ":size_matched")


def _size_matched_accepts(ctx: ArmContext, cap: float | None) -> bool:
    return (
        cap is not None
        and ctx.pick_cap is not None
        and ctx.pick_cap / SIZE_BAND <= cap <= ctx.pick_cap * SIZE_BAND
    )


ARMS: dict[str, Arm] = {
    "pick": Arm(lambda ctx: [ctx.daily["stock"]["symbol"]]),
    "top2_5": Arm(_top2_5_symbols),
    "random": Arm(_random_candidates, _random_accepts, sampled=True),
    "size_matched": Arm(
        _size_matched_candidates, _size_matched_accepts, sampled=True, needs_pit=True
    ),
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


def _row(m: dict, arm: str, cap: tuple[float, str] | None, survivorship: str) -> dict:
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
        "capAtPick": cap[0] if cap else None,
        "capBasis": cap[1] if cap else None,
        "survivorshipBias": survivorship,
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
    estimators: dict[str, CapEstimator | None] | None = None,
    floor_universes: dict[str, list[str]] | None = None,
) -> list[dict]:
    estimators = estimators or {}
    floor_universes = floor_universes or {}
    bars_cache: dict[tuple[str, str], Any] = {}
    bench = {m: benchmark_provider(BENCHMARK_IDS[m]) for m in MARKETS}

    def bars_for(symbol: str, market: str):
        key = (symbol, market)
        if key not in bars_cache:
            try:
                bars_cache[key] = price_provider(symbol, market)
            except Exception as exc:
                print(f"warn: bars failed {symbol}: {exc}", file=sys.stderr)
                bars_cache[key] = None
        return bars_cache[key]

    rows: list[dict] = []
    for daily in dailies:
        market = daily["market"]
        if daily["status"] != "pick" or market not in MARKETS:
            continue
        est = estimators.get(market)
        pick_symbol = daily["stock"]["symbol"]
        pick_cap = (
            est.cap_at(pick_symbol, daily["date"], bars_for(pick_symbol, market)) if est else None
        )
        ctx = ArmContext(
            daily=daily,
            universe=universes[market],
            floor_universe=floor_universes.get(market, universes[market]),
            k=random_k,
            seed=seed,
            est=est,
            pick_cap=pick_cap[0] if pick_cap else None,
        )
        survivorship = (
            "pit_universe" if est and daily["date"] in est.pit_dates else "current_universe"
        )
        for arm, spec in ARMS.items():
            if spec.needs_pit and est is None:
                continue
            accepted = attempts = 0
            for symbol in spec.candidates(ctx):
                if spec.sampled and (
                    accepted >= random_k or attempts >= MAX_ATTEMPTS_PER_K * random_k
                ):
                    break
                attempts += 1
                bars = bars_for(symbol, market)
                cap = est.cap_at(symbol, daily["date"], bars) if est else None
                if spec.accept and not spec.accept(ctx, cap[0] if cap else None):
                    continue
                accepted += 1
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
                rows.append(_row(m, arm, cap, survivorship))
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
    estimators: dict[str, CapEstimator | None] | None = None,
) -> Path:
    dailies = load_eligible_dailies(daily_dir or DAILY_DIR, as_of_date)
    if estimators is None:
        estimators = {m: load_cap_estimator(m) for m in MARKETS}
    notes = []
    for m in MARKETS:
        if estimators.get(m) is None:
            note = (
                f"{m}: PIT cap data unavailable; random uses the current-universe cap floor "
                "and size_matched is skipped"
            )
            print(f"warn: {note}", file=sys.stderr)
            notes.append(note)
    floor_universes = None
    if universes is None:
        universes = {m: [u.symbol for u in load_universe(m)] for m in MARKETS}
        floor_universes = {
            m: [u.symbol for u in load_universe(m) if passes_market_cap_filter(u, m)]
            for m in MARKETS
            if estimators.get(m) is None
        }
    rows = build_rows(
        dailies=dailies,
        universes=universes,
        as_of_date=as_of_date,
        price_provider=price_provider or default_price_provider(as_of_date),
        benchmark_provider=benchmark_provider or default_benchmark_provider(as_of_date),
        random_k=random_k,
        seed=seed,
        estimators=estimators,
        floor_universes=floor_universes,
    )
    doc = {
        "schemaVersion": SCHEMA_VERSION,
        "asOfDate": as_of_date,
        "generatedAt": datetime.now(UTC).isoformat(),
        "params": {"horizon": HORIZON, "randomK": random_k, "seed": seed},
        "notes": notes,
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
