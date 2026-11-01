"""TWSE BFI82U institutional net buy/sell amount in TWD; official data only."""
import datetime as dt
import json
import pathlib
import re
import urllib.request
from html.parser import HTMLParser

OUT=pathlib.Path("data/institutions.json")
URL="https://www.twse.com.tw/rwd/zh/fund/BFI82U?response=json&type=day&dayDate="
def val(s):return int(str(s).replace(",","").strip())

class TableRows(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows=[];self.row=None;self.cell=None
    def handle_starttag(self,tag,attrs):
        if tag=="tr":self.row=[]
        elif tag in ("td","th") and self.row is not None:self.cell=[]
    def handle_data(self,data):
        if self.cell is not None:self.cell.append(data)
    def handle_endtag(self,tag):
        if tag in ("td","th") and self.cell is not None:
            self.row.append("".join(self.cell).strip());self.cell=None
        elif tag=="tr" and self.row is not None:
            if self.row:self.rows.append(self.row)
            self.row=None

def official_html_final(date):
    url="https://www.twse.com.tw/fund/BFI82U?response=html&type=day&dayDate="+date.strftime("%Y%m%d")
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0","Referer":"https://www.twse.com.tw/","Accept":"text/html"})
    with urllib.request.urlopen(req,timeout=20) as response:
        html=response.read().decode("utf-8","replace")
    expected=f"{date.year-1911}年{date.month:02d}月{date.day:02d}日"
    if expected not in html:
        raise ValueError("HTML report date mismatch; do not overwrite verified data")
    parser=TableRows();parser.feed(html)
    found={}
    for r in parser.rows:
        if len(r)<4:continue
        name=re.sub(r"\s+","",r[0])
        try:amount=val(r[3])
        except ValueError:continue
        if "外資及陸資" in name:found["foreign"]=amount
        elif name=="投信":found["trust"]=amount
        elif "自營商(自行買賣)" in name:found["dealer_self"]=amount
        elif "自營商(避險)" in name:found["dealer_hedge"]=amount
    if set(found)!={"foreign","trust","dealer_self","dealer_hedge"}:
        raise ValueError("HTML report incomplete")
    return found

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
                try:
                    final=official_html_final(date)
                    if final!=found:print("CORRECTED by official HTML",date,found,final)
                    found.update(final)
                    found["verified_html"]=True
                except Exception as e:
                    if old.get(date.isoformat(),{}).get("verified_html"):
                        print("PRESERVE previously HTML-verified row",date,str(e))
                        continue
                    print("HTML verification unavailable; JSON provisional",date,str(e))
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
