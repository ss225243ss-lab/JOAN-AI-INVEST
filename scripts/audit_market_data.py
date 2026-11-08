#!/usr/bin/env python3
"""JOAN AI INVEST data quality gate. Local JSON validation, not remote source verification."""
import json
import sys
from datetime import date
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
errors=[]
warnings=[]
summary={}
def load(name):
    p=ROOT/"data"/name
    if not p.exists():
        errors.append(f"{name}: missing")
        return []
    try:
        j=json.loads(p.read_text(encoding="utf-8"))
        rows=j["rows"]
        assert isinstance(rows,list) and rows
        return rows
    except (ValueError,KeyError,AssertionError,TypeError) as e:
        errors.append(f"{name}: invalid JSON/rows {e}")
        return []
def check_dates(name,rows):
    ds=[r.get("date") for r in rows]
    try:
        parsed=[date.fromisoformat(d) for d in ds]
        if parsed!=sorted(set(parsed)): errors.append(f"{name}: unsorted or duplicate dates")
        if parsed and parsed[-1]>date.today(): errors.append(f"{name}: future dated rows")
        if parsed:
            summary[name]={"rows":len(rows),"latest":ds[-1],"age_calendar_days":(date.today()-parsed[-1]).days}
            if (date.today()-parsed[-1]).days>4: warnings.append(f"{name}: data may be stale ({ds[-1]})")
    except (TypeError,ValueError):
        errors.append(f"{name}: malformed dates")
ohlc=load("taiex.json")
check_dates("taiex.json",ohlc)
for r in ohlc:
    try:
        o,h,l,c,v=(float(r[k]) for k in ("open","high","low","close","volume"))
        if not (0<l<=min(o,c)<=max(o,c)<=h and v>=0): raise ValueError()
    except (KeyError,TypeError,ValueError):
        errors.append(f"taiex.json: invalid OHLCV at {r.get('date')}")
        break
inst=load("institutions.json")
check_dates("institutions.json",inst)
for r in inst:
    try:
        vals=[r[k] for k in ("foreign","trust","dealer","total")]
        if not all(isinstance(x,(int,float)) and not isinstance(x,bool) for x in vals): raise ValueError()
        if abs(sum(vals[:3])-vals[3])>1: raise ValueError()
        if "dealer_self" in r and "dealer_hedge" in r and abs(r["dealer_self"]+r["dealer_hedge"]-r["dealer"])>1: raise ValueError()
    except (KeyError,ValueError,TypeError):
        errors.append(f"institutions.json: arithmetic mismatch at {r.get('date')}")
        break
fut=load("foreign_futures.json")
check_dates("foreign_futures.json",fut)
for r in fut:
    try:
        n,l,s=(r[k] for k in ("net_open_interest","long_open_interest","short_open_interest"))
        if not all(isinstance(x,int) and not isinstance(x,bool) for x in (n,l,s)) or l<0 or s<0 or n!=l-s: raise ValueError()
    except (KeyError,ValueError,TypeError):
        errors.append(f"foreign_futures.json: arithmetic mismatch at {r.get('date')}")
        break
print(json.dumps({"status":"FAIL" if errors else "PASS_LOCAL_ONLY","summary":summary,"errors":errors,"warnings":warnings,"note":"Local integrity checks do not verify original TWSE/TAIFEX values, market hours, or browser functionality."},ensure_ascii=False,indent=2))
sys.exit(1 if errors else 0)
