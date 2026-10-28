"""Fetch verified foreign investors' TX futures net open interest from TAIFEX."""
import datetime as dt
import json
import pathlib
import re
import urllib.parse
import urllib.request
from html.parser import HTMLParser

OUT = pathlib.Path("data/foreign_futures.json")
URL = "https://www.taifex.com.tw/cht/3/futContractsDate"

class Tables(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables=[]; self.table=None; self.row=None; self.cell=None
    def handle_starttag(self,tag,attrs):
        if tag=="table":self.table=[]
        elif tag=="tr" and self.table is not None:self.row=[]
        elif tag in ("td","th") and self.row is not None:self.cell=[]
    def handle_data(self,data):
        if self.cell is not None:self.cell.append(data)
    def handle_endtag(self,tag):
        if tag in ("td","th") and self.cell is not None:
            self.row.append(" ".join("".join(self.cell).split()));self.cell=None
        elif tag=="tr" and self.row is not None:
            if self.row:self.table.append(self.row)
            self.row=None
        elif tag=="table" and self.table is not None:
            self.tables.append(self.table);self.table=None

def parse_page(html, day):
    parser=Tables();parser.feed(html)
    # TAIFEX table has 14 data columns; foreign TX row has 13 columns
    # because the product name cell is rowspan from the dealer row.
    for table in parser.tables:
        in_tx=False
        for row in table:
            joined=" ".join(row)
            if any("臺股期貨" in c or "台股期貨" in c for c in row[:3]):in_tx=True
            elif row and any("期貨" in c for c in row[:2]) and "臺股" not in joined:in_tx=False
            if in_tx and any(c.strip()=="外資" for c in row[:4]):
                i=next(i for i,c in enumerate(row) if c.strip()=="外資")
                nums=[int(c.replace(",","")) for c in row[i+1:] if re.fullmatch(r"-?[\d,]+",c)]
                # 12 numbers: long/short/net trade lots & amounts,
                # long/short/net open interest lots & amounts.
                if len(nums)==12 and nums[10]==nums[6]-nums[8]:
                    return {"date":day.isoformat(),"net_open_interest":nums[10],"long_open_interest":nums[6],"short_open_interest":nums[8]}
    raise ValueError("No verified TX foreign open-interest row")

def main():
    today=dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).date()
    old={}
    if OUT.exists():
        old={r["date"]:r for r in json.loads(OUT.read_text()).get("rows",[])}
    for back in range(14,-1,-1):
        day=today-dt.timedelta(days=back)
        if day.weekday()>4:continue
        payload=urllib.parse.urlencode({"queryType":"1","doQuery":"1","dateaddcnt":"","queryDate":day.strftime("%Y/%m/%d")})
        req=urllib.request.Request(URL+"?"+payload,headers={"User-Agent":"Mozilla/5.0","Referer":"https://www.taifex.com.tw/cht/3/futContractsDate","Accept-Language":"zh-TW"})
        try:
            with urllib.request.urlopen(req,timeout=25) as resp:html=resp.read().decode("utf-8","replace")
            item=parse_page(html,day);old[item["date"]]=item;print("OK",item)
        except Exception as exc:print("SKIP",day,exc)
    if not old:raise SystemExit("No verified TX foreign futures records; not publishing fake values")
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({"source":"TAIFEX futContractsDate / TX foreign open interest","source_url":URL,"generated_at":dt.datetime.now(dt.timezone.utc).isoformat(),"rows":[old[k] for k in sorted(old)][-750:]},ensure_ascii=False,indent=2)+"\n")

if __name__=="__main__":main()
