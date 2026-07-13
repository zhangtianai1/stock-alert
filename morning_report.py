import requests,json,os;from datetime import datetime
IDX=[("%5EGSPC","S&P 500"),("%5EIXIC","Nasdaq"),("000001.SS","上证指数"),("000300.SS","沪深300"),("000688.SS","科创50"),("%5EHSI","恒生指数")]
def m():
    syms=",".join([s[0] for s in IDX])
    r=requests.get(f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={syms}",timeout=15)
    p={}
    for i in r.json()["quoteResponse"]["result"]: p[i["symbol"]]=(i.get("regularMarketPrice",0),i.get("regularMarketChangePercent",0))
    msg=[f"## 早盘分析 ({datetime.now().strftime('%m-%d %H:%M')})","","**【隔夜外盘】**"]
    for sym,name in IDX[:2]:
        if sym in p: msg.append(f"{name}: {p[sym][0]:.0f} ({p[sym][1]:+.2f}%)")
    msg.append(""); msg.append("**【A股技术面（昨日收盘）】**")
    for sym,name in IDX[2:5]:
        if sym in p: msg.append(f"{name}: {p[sym][0]:.0f} ({p[sym][1]:+.2f}%)")
    msg.append(""); msg.append("**【今日预测】**")
    try:
        r2=requests.get("https://query1.finance.yahoo.com/v8/finance/chart/000688.SS?interval=1d&range=2mo",timeout=10)
        d=r2.json()["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        ma5=sum(d[-5:])/5; ma10=sum(d[-10:])/10
        g=l=0
        for i in range(-14,0):
            c=d[i]-d[i-1]
            if c>0: g+=c
            else: l+=abs(c)
        rsi=100-100/(1+(g/14)/(l/14)) if l>0 else 50
        sc=(1 if rsi>45 else -1)+(1 if d[-1]>ma5 else -1)
        out="偏多震荡" if sc>=1 else "偏弱调整" if sc<=-1 else "震荡整理"
        msg.append(f"科创50: RSI={rsi:.0f} MA5={ma5:.0f} MA10={ma10:.0f}"); msg.append(f"研判: {out}")
    except: msg.append("技术分析暂不可用")
    wh=os.environ.get("WEBHOOK","")
    content="
".join(msg)
    if wh: requests.post(wh,json={"msgtype":"markdown","markdown":{"title":"早盘分析","text":content}},timeout=10)
    else: print(content)
if __name__=="__main__": m()
