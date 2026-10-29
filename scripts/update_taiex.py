"""Official TWSE TAIEX OHLC + traded share volume history; never fabricate bars."""
import datetime as dt
import json
import pathlib
import time
import urllib.request

TZ=dt.timezone(dt.timedelta(hours=8))
OUT=pathlib.Path("data/taiex.json")
BASE="https://www.twse.com.tw/rwd/zh/"
def number(v):
    if isinstance(v,(int,float)):return float(v)
    return float(str(v).replace(",","").strip())
def date_key(s):
    p=str(s).strip().split("/")
    if len(p)!=3:raise ValueError("Invalid ROC date")
    y,m,d=map(int,p)
    if y<200:y+=1911
    return dt.date(y,m,d).isoformat()
def get(endpoint,year,month):
    date=f"{year}{month:02d}01"
    url=f"{BASE}{endpoint}?date={date}&response=json"
    err=None
    for attempt in range(3):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (compatible; JOAN-AI-INVEST/1.0)","Accept":"application/json","Referer":"https://www.twse.com.tw/"})
            with urllib.request.urlopen(req,timeout=35) as response:
                data=json.load(response)
            if not isinstance(data,dict) or not isinstance(data.get("data"),list):
                raise ValueError("Unexpected TWSE response")
            return data["data"]
        except Exception as e:
            err=e
            time.sleep(1.5*(attempt+1))
    print("MONTH FAILED",endpoint,date,str(err),flush=True)
    return []
def main():
    now=dt.datetime.now(TZ)
    previous={}
    if OUT.exists():
        try:
            previous={r["date"]:r for r in json.loads(OUT.read_text(encoding="utf-8")).get("rows",[]) if isinstance(r,dict) and "date" in r}
        except Exception as e:print("Ignoring corrupt previous data:",e)
    rows=previous.copy()
    # Backfill 66 months only on a fresh install; otherwise refresh the latest 2 months.
    # This prevents daily runs from timing out while preserving full MA240 history.
    months=66 if len(previous)<240 else 2
    for offset in range(months-1,-1,-1):
        y=now.year+(now.month-1-offset)//12
        m=(now.month-1-offset)%12+1
        bars=get("TAIEX/MI_5MINS_HIST",y,m)
        volume=get("afterTrading/FMTQIK",y,m)
        month_bars={}
        for item in bars:
            try:
                day=date_key(item[0])
                o,h,l,c=(number(item[i]) for i in range(1,5))
                if not (0<l<=min(o,c)<=max(o,c)<=h):continue
                month_bars[day]={"date":day,"open":o,"high":h,"low":l,"close":c}
            except (ValueError,IndexError,TypeError):continue
        vols={}
        for item in volume:
            try:
                day=date_key(item[0])
                shares=int(number(item[1]))
                reported_close=number(item[4])
                if shares>=0 and reported_close>0:vols[day]=(shares,reported_close)
            except (ValueError,IndexError,TypeError):continue
        for day,bar in month_bars.items():
            v=vols.get(day)
            if not v:continue
            if abs(v[1]-bar["close"])>max(1,bar["close"]*0.002):
                print("CLOSE MISMATCH",day,bar["close"],v[1])
                continue
            rows[day]={**bar,"volume":v[0]}
        print(f"{y}-{m:02d}: OHLC={len(month_bars)} volume={len(vols)} matched={len(set(month_bars)&set(vols))}",flush=True)
        time.sleep(.15)
    verified=[r for r in rows.values() if all(k in r for k in ("date","open","high","low","close","volume"))]
    verified.sort(key=lambda r:r["date"])
    if len(verified)<1:raise SystemExit("No validated OHLCV available; retain last good data")
    latest=dt.date.fromisoformat(verified[-1]["date"])
    if (now.date()-latest).days>8:print(f"WARNING: latest record {latest} is stale; publishing with explicit date",flush=True)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    result={"source":"TWSE TAIEX/MI_5MINS_HIST + afterTrading/FMTQIK",
            "source_urls":["https://www.twse.com.tw/rwd/zh/TAIEX/MI_5MINS_HIST","https://www.twse.com.tw/rwd/zh/afterTrading/FMTQIK"],
            "generated_at":dt.datetime.now(dt.timezone.utc).isoformat(),
            "volume_unit":"shares","rows":verified}
    OUT.write_text(json.dumps(result,ensure_ascii=False,separators=(",",":"))+"\n",encoding="utf-8")
    print("SAVED",len(verified),"latest",verified[-1]["date"],flush=True)
if __name__=="__main__":main()
