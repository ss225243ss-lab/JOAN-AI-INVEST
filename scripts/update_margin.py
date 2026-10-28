"""TWSE margin summary updater; stores only successfully validated official rows."""
import datetime as dt
import json
import pathlib
import time
import urllib.request

OUT=pathlib.Path("data/margin.json")
TZ=dt.timezone(dt.timedelta(hours=8))

def num(value):
    return int(str(value).replace(",","").replace(" ","").strip())

def load(date):
    url="https://www.twse.com.tw/rwd/zh/marginTrading/MI_MARGN?date="+date.strftime("%Y%m%d")+"&selectType=ALL&response=json"
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0","Accept":"application/json","Referer":"https://www.twse.com.tw/","Accept-Language":"zh-TW,zh;q=0.9"})
    with urllib.request.urlopen(req,timeout=30) as response:
        payload=json.load(response)
    # First table: 融資(交易單位), 融券(交易單位), 融資金額(仟元)
    tables=payload.get("tables",[])
    raw=tables[0].get("data",[]) if tables else payload.get("data",[])
    if not isinstance(raw,list):
        raise ValueError("no summary data")
    found={}
    for row in raw:
        if not isinstance(row,list) or len(row)<5:
            continue
        name=str(row[0]).replace(" ","").replace("<br>","")
        if "融資金額" in name:
            key="margin_amount_thousand_twd"
        elif "融資" in name and "融券" not in name:
            key="margin_units"
        elif "融券" in name:
            key="short_units"
        else:
            continue
        found[key]={"previous":num(row[3]),"current":num(row[4])}
    if len(found)!=3 or any(v["current"]<0 for v in found.values()):
        raise ValueError("incomplete official summary: "+repr(list(found)))
    return {"date":date.isoformat(),**found}

def main():
    old={}
    if OUT.exists():
        data=json.loads(OUT.read_text(encoding="utf-8"))
        old={r["date"]:r for r in data.get("rows",[]) if isinstance(r,dict) and "date" in r}
    today=dt.datetime.now(TZ).date()
    errors=[]
    for back in range(9,-1,-1):
        date=today-dt.timedelta(days=back)
        if date.weekday()>4:
            continue
        try:
            old[date.isoformat()]=load(date)
            print("OK",date)
        except Exception as e:
            errors.append(f"{date}: {e}")
            print("SKIP",date,e)
        time.sleep(0.4)
    if not old:
        raise SystemExit("No verified TWSE margin data. "+ "; ".join(errors))
    OUT.parent.mkdir(exist_ok=True)
    out={"source":"TWSE MI_MARGN official credit trading statistics","source_url":"https://www.twse.com.tw/zh/trading/margin/mi-margn.html",
        "generated_at":dt.datetime.now(dt.timezone.utc).isoformat(),
        "note":"今日餘額可能修正；次交易日的前日餘額為官方建議優先參考欄位。融資金額單位為新臺幣仟元。",
        "rows":[old[k] for k in sorted(old)][-400:]}
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Wrote",len(out["rows"]),"days; latest",max(old))
if __name__=="__main__":
    main()
