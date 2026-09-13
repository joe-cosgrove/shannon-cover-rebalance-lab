#!/usr/bin/env python3
"""Constant-rebalanced portfolio simulator (Shannon / Cover)."""
from __future__ import annotations
import argparse, math
from typing import Iterable
import numpy as np
import pandas as pd

def load_prices(path, assets):
    df = pd.read_csv(path, parse_dates=[0], index_col=0)
    df.columns = [c.strip() for c in df.columns]
    missing = [a for a in assets if a not in df.columns]
    if missing:
        raise SystemExit(f"Missing columns {missing}. Have: {list(df.columns)}")
    return df[assets].sort_index().dropna()

def metrics(wealth, dates):
    dates = list(dates)
    w = np.asarray(wealth, float)
    r = w[1:] / w[:-1] - 1
    years = max((dates[-1] - dates[0]).days / 365.25, 1e-9)
    cagr = (w[-1] / w[0]) ** (1 / years) - 1
    vol = float(r.std() * math.sqrt(252)) if len(r) else float("nan")
    peak = np.maximum.accumulate(w)
    maxdd = float((w / peak - 1).min())
    sharpe = float((r.mean() * 252) / (r.std() * math.sqrt(252))) if r.std() > 0 else float("nan")
    return {"end": w[-1], "multiple": w[-1] / w[0], "cagr": cagr, "vol": vol, "maxdd": maxdd, "sharpe": sharpe}

def simulate_crp(prices, weights, capital=100000.0, freq="M", cost_bps=0.0, band=None):
    rets = prices.pct_change().fillna(0.0).to_numpy()
    dates = list(prices.index)
    holdings = weights * capital
    wealth = [capital]
    costs = 0.0
    n_reb = 0
    last_w = dates[0].isocalendar()[:2]
    last_m = (dates[0].year, dates[0].month)
    last_q = (dates[0].year, (dates[0].month - 1) // 3)
    last_y = dates[0].year
    def rebalance():
        nonlocal holdings, costs, n_reb
        total = float(holdings.sum())
        if total <= 0:
            return
        target = weights * total
        traded = float(np.abs(target - holdings).sum()) / 2.0
        fee = traded * (cost_bps / 1e4)
        if fee:
            total -= fee
            target = weights * total
            costs += fee
        holdings = target
        n_reb += 1
    for i in range(1, len(dates)):
        holdings = holdings * (1.0 + rets[i])
        d = dates[i]
        do = False
        if freq == "D": do = True
        elif freq == "W":
            key = d.isocalendar()[:2]; do, last_w = key != last_w, key
        elif freq == "M":
            key = (d.year, d.month); do, last_m = key != last_m, key
        elif freq == "Q":
            key = (d.year, (d.month - 1) // 3); do, last_q = key != last_q, key
        elif freq == "Y":
            do = d.year != last_y; last_y = d.year
        if band is not None:
            total = float(holdings.sum())
            if total > 0 and np.any(np.abs(holdings / total - weights) > band):
                do = True
        if do: rebalance()
        wealth.append(float(holdings.sum()))
    stats = metrics(np.array(wealth), dates)
    stats.update({"rebalances": n_reb, "costs": costs, "label": f"CRP {freq} {cost_bps}bps"})
    return stats, pd.Series(wealth, index=prices.index, name=stats["label"])

def simulate_bah(prices, capital):
    n = prices.shape[1]
    shares = (capital / n) / prices.iloc[0]
    path = prices.mul(shares, axis=1).sum(axis=1)
    stats = metrics(path.to_numpy(), list(prices.index))
    stats.update({"rebalances": 0, "costs": 0.0, "label": "Buy & hold pair"})
    return stats, path.rename(stats["label"])

def simulate_single(series, capital, name):
    path = capital * (series / series.iloc[0])
    stats = metrics(path.to_numpy(), list(series.index))
    stats.update({"rebalances": 0, "costs": 0.0, "label": f"{name} 100%"})
    return stats, path.rename(stats["label"])

def fmt(s):
    return (f"{s['label']:<22}  ${s['end']:>12,.0f}  {s['multiple']:>6.2f}x  "
            f"CAGR {s['cagr']*100:>6.2f}%  vol {s['vol']*100:>5.1f}%  "
            f"DD {s['maxdd']*100:>6.1f}%  Sharpe {s['sharpe']:>5.2f}  "
            f"rebal {s['rebalances']:<5}  costs ${s['costs']:,.0f}")

def main():
    p = argparse.ArgumentParser(description="Cover / Shannon CRP simulator")
    p.add_argument("--csv", required=True)
    p.add_argument("--assets", required=True)
    p.add_argument("--weights", default="")
    p.add_argument("--capital", type=float, default=100000)
    p.add_argument("--freq", default="M", choices=list("DWMQY"))
    p.add_argument("--cost-bps", type=float, default=5.0)
    p.add_argument("--band", type=float, default=None)
    p.add_argument("--out", default="")
    args = p.parse_args()
    assets = [a.strip().upper() for a in args.assets.split(",") if a.strip()]
    weights = np.array([float(x) for x in args.weights.split(",")], float) if args.weights else np.repeat(1.0 / len(assets), len(assets))
    if len(weights) != len(assets) or abs(weights.sum() - 1) > 1e-6 or np.any(weights < 0):
        raise SystemExit("Weights must be non-negative, same length as assets, and sum to 1")
    px = load_prices(args.csv, assets)
    rows, curves = [], []
    for col in assets:
        s, c = simulate_single(px[col], args.capital, col); rows.append(s); curves.append(c)
    s, c = simulate_bah(px, args.capital); rows.append(s); curves.append(c)
    s, c = simulate_crp(px, weights, args.capital, args.freq, args.cost_bps, args.band); rows.append(s); curves.append(c)
    print(f"{px.index[0].date()} -> {px.index[-1].date()}  n={len(px)}  capital=${args.capital:,.0f}")
    print(f"assets={assets}  weights={weights.tolist()}  freq={args.freq}  cost={args.cost_bps}bps\n")
    for s in rows: print(fmt(s))
    print(f"\nRebalancing bonus vs buy-and-hold pair: ${rows[-1]['end'] - rows[-2]['end']:,.0f}")
    if args.out:
        pd.concat(curves, axis=1).to_csv(args.out)
        print(f"Wrote {args.out}")

if __name__ == "__main__":
    main()
