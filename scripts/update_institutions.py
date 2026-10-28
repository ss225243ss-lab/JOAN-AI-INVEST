"""TWSE BFI82U institutional net buy/sell amount in TWD; official data only."""
import datetime as dt
import json
import pathlib
import re
import urllib.request

OUT=pathlib.Path("data/institutions.json")
URL="https://www.twse.com.tw/rwd/zh/fund/BFI82U?response=json&type=day&dayDate="
def val(s):return int(str(s).replace(",","").strip())
def main():
    tz=dt.timezone(dt.timedelta(hours=8))
    today=dt.datetime.now(tz).date()
    old={}
    if OUT.exists():
        old={r["date"]:r for r in json.loads(OUT.read_text(encoding="utf-8")).get("rows",[])}
    for back in range(8,-1,-1):
        date=today-dt.timedelta(days=back)
        if date.weekday()>4:continue
        url=URL+date.strftime("%Y%m%d")
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0","Referer":"https://www.twse.com.tw/","Accept":"application/json"})
            with urllib.request.urlopen(req,timeout=20) as response:j=json.load(response)
            data=j.get("data",[])
            found={}
            for r in data:
                if len(r)<4:continue
                name=str(r[0]).replace(" ","")
                amount=val(r[3])
                if "外資及陸資" in name:found["foreign"]=amount
                elif "投信"==name:found["trust"]=amount
                elif "自營商(自行買賣)" in name:found["dealer_self"]=amount
                elif "自營商(避險)" in name:found["dealer_hedge"]=amount
            if set(found)=={"foreign","trust","dealer_self","dealer_hedge"}:
                found["dealer"]=found["dealer_self"]+found["dealer_hedge"]
                found["total"]=found["foreign"]+found["trust"]+found["dealer"]
                old[date.isoformat()]={"date":date.isoformat(),**found}
                print("OK",date)
            else:print("SKIP incomplete",date,list(found))
        except Exception as e:print("SKIP",date,str(e))
    if not old:raise SystemExit("No verified BFI82U records; no fake data")
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({"source":"TWSE BFI82U","source_url":"https://www.twse.com.tw/zh/trading/foreign/bfi82u.html","unit":"TWD","generated_at":dt.datetime.now(dt.timezone.utc).isoformat(),"rows":[old[k] for k in sorted(old)][-400:]},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":main()
