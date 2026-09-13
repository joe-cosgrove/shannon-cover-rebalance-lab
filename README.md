# Cover / Shannon Rebalance Lab

Interactive simulator for **Shannon's Demon** and Thomas Cover's **constant-rebalanced portfolio (CRP)**.

Repo: https://github.com/joe-cosgrove/shannon-cover-rebalance-lab

## What this strategy is

Keep fixed weights (for example 50/50) by selling whatever just went up and buying whatever just went down. You do not predict prices. The return comes from volatility + imperfect correlation, sometimes called a rebalancing bonus.

Cover's 1991 paper tested this on NYSE pairs. Iroquois Brands + Kin Ark over 22 years:
- buy-and-hold: 8.9x and 4.1x
- best *hindsight* daily 55/45 CRP: 73.6x ($100k → $7.4M)
- live universal portfolio (no peeking): 38.7x ($100k → $3.9M)

The viral $7M number is the omniscient mix, not a live set-and-forget system, and it assumed zero trading costs.

## Tools in this repo

1. **`index.html`** — open in a browser. No install.
   - Shannon toy: stock doubles/halves vs cash, or two stocks that oscillate
   - Historical presets: TSLA, GLD, NVDA, TLT, SPY, QQQ, IWM year-end prices 2016–2026
   - Paste your own two-column CSV of dates + prices
   - Compare CRP vs buy-and-hold vs each asset, with costs and rebalance frequency
2. **`crp_sim.py`** — daily engine. Point it at a price CSV for finer backtests.

```bash
python crp_sim.py --csv prices.csv --assets TSLA,GLD --weights 0.5,0.5 --freq M --cost-bps 5 --capital 100000
```

## Is it a viable way to make money?

**The math is real. The tweet oversells it.**

Backtests on split-adjusted daily prices, 2016-01-04 to 2026-09-11, $100,000 start:

| Pair | Buy & hold pair | Monthly 50/50 CRP (5 bps) | Winner 100% |
| --- | ---: | ---: | ---: |
| TSLA + GLD | $1.42M | **$1.66M** | TSLA $2.45M |
| NVDA + GLD | $13.7M | $4.51M | NVDA $27.0M |
| SPY + GLD | $384k | **$407k** | SPY $380k |
| SPY + TLT | $223k | $169k | SPY $380k |
| TSLA + cash | n/a | $838k | TSLA $2.45M |

What that means:

- Rebalancing **can** beat a drifted 50/50 and improve Sharpe / max drawdown when the two names are volatile and take turns winning (TSLA+GLD, SPY+GLD).
- Rebalancing **loses a lot of dollars** against a persistent winner (NVDA). You keep selling the thing that never stops working.
- Daily vs monthly is almost a wash after costs. A 5% drift band is usually enough.
- Cover's $7M pair was two small, jumpy, low-correlation names with no commissions modeled.

### When it can help
- Tax-advantaged account (IRA / 401k)
- Two (or more) liquid sleeves that are volatile and not glued together: stock + gold, stock + long Treasuries, two different sectors
- Monthly, quarterly, or 5–10% band rebalancing — not daily
- You care about a smoother path, not about capturing 100% of one rocket ship

### When it is not viable
- Taxable account + daily trades → short-term gains tax and spreads eat the bonus
- Pairing a mega-winner with a flat asset and expecting Cover's 73x
- Expecting it to replace stock selection or an index fund as a get-rich system

Practical version: 50/50 **TSLA + GLD** (or **QQQ + GLD**) in an IRA, rebalance when a weight drifts 5–10% off target. That is the honest retail version of this lecture.
