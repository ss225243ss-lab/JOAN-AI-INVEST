import json,datetime,urllib.request,time,pathlib
today=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).date()
rows={}
for offset in range(16,-1,-1):
 y=today.year+(today.month-1-offset)//12
 m=(today.month-1-offset)%12+1
 url=f"https://www.twse.com.tw/rwd/zh/afterTrading/FMTQIK?date={y}{m:02d}01&response=json"
 try:
  req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0","Accept":"application/json"})
  with urllib.request.urlopen(req,timeout=25) as f: data=json.load(f)
  for item in data.get("data",[]):
   try:
    yy,mm,dd=map(int,item[0].split("/"))
    day=f"{yy+1911:04d}-{mm:02d}-{dd:02d}"
    close=float(item[4].replace(",",""))
    volume=int(item[1].replace(",",""))
    rows[day]={"date":day,"close":close,"volume":volume}
   except (ValueError,IndexError,TypeError): pass
 except Exception as e: print("Month failed",y,m,str(e))
 time.sleep(0.25)
if len(rows)<240: raise SystemExit(f"Only {len(rows)} days; refusing to publish incomplete history")
out={"source":"TWSE FMTQIK","generated_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"rows":[rows[k] for k in sorted(rows)]}
pathlib.Path("data").mkdir(exist_ok=True)
pathlib.Path("data/taiex.json").write_text(json.dumps(out,ensure_ascii=False),encoding="utf-8")
print("Saved",len(rows),"days",max(rows))
