import requests,json,os;from datetime import datetime
S=[("603019.SS","中科曙光",93.50,1),("002185.SZ","华天科技",21.93,4),("000063.SZ","中兴通讯",35.79,2),("601899.SS","紫金矿业",27.62,5),("002415.SZ","海康威视",33.86,3),("600276.SS","恒瑞医药",55.36,1),("600036.SS","招商银行",37.55,2),("600941.SS","中国移动",88.42,1)]
def m():
    syms=",".join([s[0] for s in S])
    r=requests.get(f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={syms}",timeout=15)
    p={}
    for i in r.json()["quoteResponse"]["result"]: p[i["symbol"]]=(i.get("regularMarketPrice",0),i.get("regularMarketChangePercent",0))
    t=0; l=[f"收盘监控 ({datetime.now().strftime('%m-%d %H:%M')})",""]
    for sym,name,cost,qty in S:
        if sym not in p: continue
        pr,ch=p[sym]; pl=(pr-cost)*qty*100; t+=pl
        l.append(f"{'🟢' if ch>=0 else '🔴'} {name}: {pr:.2f} ({ch:+.2f}%) 盈亏{pl:+>.0f}")
    l.append(f"
总盈亏: {t:+>.0f} ({(t/100000*100):+.2f}%)")
    msg="
".join(l); print(msg)
    wh=os.environ.get("WEBHOOK","")
    if wh: requests.post(wh,json={"msgtype":"markdown","markdown":{"title":"收盘监控","text":msg}},timeout=10)
if __name__=="__main__": m()
