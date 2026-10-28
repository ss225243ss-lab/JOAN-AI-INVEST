"""Save verified official TAIFEX TX daily and after-hours futures market reports.
OpenAPI exposes latest published date, not arbitrary backfill. Accumulate forward.
"""
import datetime as dt
import json
import pathlib
import re
import urllib.request

URL="https://openapi.taifex.com.tw/v1/DailyMarketReportFut"
OUT=pathlib.Path("data/taifex_tx.json")
def numeric(v):
    if v is None or str(v).strip() in ("","-","--","－","N/A"):
        return None
    try:
        x=float(str(v).replace(",","").replace("+","").replace("▲","").replace("▼","").strip())
        return x if abs(x)<1e9 else None
    except (TypeError,ValueError):return None

def get(record,*names):
    for name in names:
        if name in record:
            return record[name]
    return None

def parse_date(value):
    s=str(value or "").replace("/","").replace("-","").strip()
    if not re.fullmatch(r"20\d{6}",s):
        return None
    try:return dt.datetime.strptime(s,"%Y%m%d").date().isoformat()
    except ValueError:return None

def parse(record):
    product=str(get(record,"Contract","商品契約代號") or "").strip()
    if product!="TX":return None
    month=str(get(record,"ContractMonth(Week)","Contract Month(Week)","到期月份(週別)") or "").strip()
    if not re.fullmatch(r"20\d{4}",month):return None
    session=str(get(record,"TradingSession","交易時段") or "").strip()
    if session in ("一般","一般交易時段","regular","Regular","1"):
        session="day"
    elif session in ("盤後","盤後交易時段","afterhours","AfterHours","2"):
        session="night"
    else:return None
    date=parse_date(get(record,"Date","交易日期"))
    last=numeric(get(record,"Last","Close","最後成交價"))
    high=numeric(get(record,"High","最高價"))
    low=numeric(get(record,"Low","最低價"))
    op=numeric(get(record,"Open","開盤價"))
    if not date or last is None or last<=0 or high is None or low is None or high<low or not(low<=last<=high):
        return None
    if op is not None and not(low<=op<=high):return None
    def integer(*keys):
        v=numeric(get(record,*keys))
        return int(v) if v is not None and v>=0 else None
    return {"date":date,"contract":"TX","month":month,"session":session,
            "open":op,"high":high,"low":low,"last":last,
            "change":numeric(get(record,"Change","漲跌價")),
            "volume":integer("Volume","成交量"),
            "settlement":numeric(get(record,"SettlementPrice","結算價")),
            "open_interest":integer("OpenInterest","未沖銷契約量")}

def main():
    req=urllib.request.Request(URL,headers={"User-Agent":"Mozilla/5.0","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=80) as response:
        payload=json.load(response)
    if isinstance(payload,dict):
        payload=payload.get("data") or payload.get("Data") or payload.get("result")
    if not isinstance(payload,list):raise RuntimeError("Unexpected TAIFEX API response")
    tx=[r for r in (parse(x) for x in payload if isinstance(x,dict)) if r]
    if not tx:raise RuntimeError("No validated TX records; refusing to publish")
    prev=[]
    if OUT.exists():
        prev=json.loads(OUT.read_text(encoding="utf-8")).get("rows",[])
    records={(r["date"],r["month"],r["session"]):r for r in prev}
    for r in tx:records[(r["date"],r["month"],r["session"])]=r
    rows=sorted(records.values(),key=lambda x:(x["date"],x["session"],x["month"]))
    if len(rows)>6000:rows=rows[-6000:]
    now=dt.datetime.now(dt.timezone.utc).isoformat()
    output={"source":"TAIFEX official OpenAPI DailyMarketReportFut","source_url":URL,
            "generated_at":now,"contract_policy":"Actual YYYYMM contract; no silent back-adjustment/roll",
            "session_policy":"Day=08:45-13:45; night=15:00-next day 05:00, exchange trading-date attribution",
            "history_policy":"Accumulate only validated published daily snapshots; no artificial backfill",
            "rows":rows}
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("validated new",len(tx),"total",len(rows),"latest",max(x["date"] for x in tx))
if __name__=="__main__":main()
