#!/usr/bin/env python3
"""JOAN AI INVEST / Huang strategy preliminary audit.
Uses actual TX 202611 DAY OHLC; NOT an executable trading backtest.
No intraday bars, no real fill prices, no cost/slippage modeled.
Run: python scripts/backtest_huang_preliminary.py
"""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"/"taifex_tx.json"

def run():
    j=json.loads(DATA.read_text(encoding="utf-8"))
    rows=sorted((r for r in j.get("rows",[])
        if r.get("contract")=="TX" and r.get("month")=="202611"
        and r.get("session")=="day"
        and all(isinstance(r.get(k),(int,float)) for k in ("open","high","low","last","volume"))
        ), key=lambda r:r["date"])
    if len(rows)<2: raise ValueError("Need at least two verified daily TX bars")
    dates=[r["date"] for r in rows]
    if len(set(dates))!=len(dates): raise ValueError("Duplicate dates")
    signals=[]
    reversal=[]
    for i in range(1,len(rows)):
        p,t=rows[i-1],rows[i]
        gap=t["open"]/p["last"]-1
        if abs(gap)>=0.00618:
            sign=1 if gap>0 else -1
            signals.append(dict(date=t["date"],gap_pct=round(gap*100,3),
                direction="long" if sign>0 else "short",
                theoretical_open_to_close_points=sign*(t["last"]-t["open"])))
        if p["last"]<p["open"] and t["last"]>p["open"]:
            nxt=rows[i+1] if i+1<len(rows) else None
            reversal.append(dict(date=t["date"],type="bullish_out-day candidate",
                next_day_open_to_close_points=(nxt["last"]-nxt["open"]) if nxt else None))
    return dict(
        source=j.get("source"), generated_at=j.get("generated_at"),
        sample_dates=[dates[0],dates[-1]], sample_bars=len(rows),
        framework="opening +/-0.618% versus prior day close; direction at open, exit day close",
        methodology="DESCRIPTIVE ORACLE OPEN-FILL ONLY; NOT tradable or backtest of Huang's full strategy",
        trades=signals, signal_count=len(signals), positive_count=sum(s["theoretical_open_to_close_points"]>0 for s in signals),
        positive_ratio=(sum(s["theoretical_open_to_close_points"]>0 for s in signals)/len(signals) if signals else None),
        point_sum=sum(s["theoretical_open_to_close_points"] for s in signals),
        reversal_candidates=reversal, limitations=[
            "No 5m/15m bars; no棒棒雞/羊肉串 entry or intraday stop simulation",
            "MA13 unavailable with fewer than 13+ warm-up daily bars",
            "Opening gap observed at opening; assumed fill at that open is optimistic and non-executable",
            "No commissions, transaction tax, slippage, margin/funding costs",
            "Very small non-independent sample, no statistical significance or out-of-sample test",
            "TX daily prices cannot be used as TMF fill prices",
            "Not a futures trading recommendation or automatically executable signal"
        ])
if __name__=="__main__":
    print(json.dumps(run(),ensure_ascii=False,indent=2))
