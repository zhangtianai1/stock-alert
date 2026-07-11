import requests, json, os, math, sys
from datetime import datetime
sys.stdout.reconfigure(encoding="utf-8")

def get_kline(code):
    url=f"http://ifzq.gtimg.cn/appstock/app/fqkline/get?param={code},day,,,60,qfq"
    try:
        rd=requests.get(url,timeout=8).json()
        ck=code if code in rd.get("data",{}) else code[2:]
        return rd["data"][ck].get("qfqday",rd["data"][ck].get("day",[]))
    except: return []

def calc_tech(ks):
    if len(ks)<20: return {}
    cls=[float(k[2]) for k in ks]; highs=[float(k[3]) for k in ks]; lows=[float(k[4]) for k in ks]
    vols=[float(k[5]) for k in ks]; p=cls[-1]
    ma5=sum(cls[-5:])/5; ma10=sum(cls[-10:])/10; ma20=sum(cls[-20:])/20; ma60=sum(cls[-60:])/60
    g=l=0
    for i in range(-14,0):
        c=cls[i]-cls[i-1]
        if c>0: g+=c
        else: l-=c
    rsi=100-100/(1+(g/14)/(l/14)) if l>0 else 50
    trend="多头" if ma5>ma10>ma20 else "空头" if ma5<ma10<ma20 else "震荡"
    h60=max(highs[-60:]); l60=min(lows[-60:])
    pos=(p-l60)/(h60-l60)*100 if h60>l60 else 50
    vol5=sum(vols[-5:])/5; vol20=sum(vols[-20:])/20
    vr=vol5/vol20 if vol20>0 else 1
    return {"p":p,"ma5":ma5,"ma10":ma10,"ma20":ma20,"ma60":ma60,"rsi":rsi,"trend":trend,"pos":pos,"vr":vr,"h60":h60,"l60":l60}

def get_us(code,name):
    try:
        r=requests.get(f"http://qt.gtimg.cn/q=us{code}",timeout=8)
        p=r.text.strip().strip("\"").split("~")
        if len(p)>5:
            price=float(p[3]) if p[3] else 0; pre=float(p[4]) if p[4] else 0
            chg=(price/pre-1)*100 if pre>0 else 0
            return f'{name}: {price:.0f} ({chg:+.2f}%)'
    except: return f'{name}: N/A'

print("=== 早盘市场分析 ===")
msg=[f"## 📊 早盘分析 ({datetime.now().strftime('%m-%d %H:%M')})",""]

# 1. 隔夜外盘
msg.append("**【隔夜外盘】**")
msg.append(get_us("SPY","S&P 500"))
msg.append(get_us("QQQ","Nasdaq"))
msg.append(get_us("ES","S&P期货"))
msg.append(get_us("NQ","Nasdaq期货"))
msg.append("")

# 2. 港股
try:
    r2=requests.get("http://qt.gtimg.cn/q=hkHSI",timeout=8)
    p2=r2.text.strip().strip("\"").split("~")
    if len(p2)>8: msg.append(f'恒生指数: {float(p2[3]):.0f} ({float(p2[8]):+.2f}%)' if float(p2[8])!=0 else f'恒生指数: {float(p2[3]):.0f}')
except: pass
msg.append("")

# 3. A股技术面
msg.append("**【A股技术面（昨日收盘）】**")
for code,name in [("sh000001","上证指数"),("sh000300","沪深300"),("sh000688","科创50")]:
    d=calc_tech(get_kline(code))
    if d:
        tag="" if d["pos"]>=30 else " 低位" if d["pos"]<=30 else ""
        signal="偏多" if d["rsi"]>50 and d["trend"]=="多头" else "偏空" if d["rsi"]<50 else "中性"
        msg.append(f'{name}: {d["p"]:.0f} (MA5={d["ma5"]:.0f} MA10={d["ma10"]:.0f}) RSI={d["rsi"]:.0f} {d["trend"]} {signal}')

# 4. 预测
msg.append("")
msg.append("**【今日预测】**")
kc=calc_tech(get_kline("sh000688"))
hs=calc_tech(get_kline("sh000300"))
score=0
if kc: score+=1 if kc["rsi"]>45 else -1
if hs: score+=1 if hs["rsi"]>45 else -1
if kc: score+=1 if kc["rsi"]>45 and kc["p"]>kc["ma5"] else 0
if kc: score+=1 if kc["vr"]>1 else 0

if score>=2: outlook="偏多震荡"
elif score>=0: outlook="震荡整理"
else: outlook="偏弱调整"
msg.append(f'研判: {outlook} (综合评分{score})')
if kc: msg.append(f'科创50支撑: {kc["ma5"]:.0f}~{kc["l60"]:.0f}  阻力: {kc["h60"]:.0f}')
if hs: msg.append(f'沪深300支撑: {hs["ma5"]:.0f}~{hs["l60"]:.0f}  阻力: {hs["h60"]:.0f}')
msg.append("\n*数据仅供参考，不构成投资建议*")

# 发送钉钉
webhook=os.environ.get("WEBHOOK","")
if webhook:
    content="\n".join(msg)
    data={"msgtype":"markdown","markdown":{"title":"早盘分析","text":content}}
    try:
        requests.post(webhook,json=data,timeout=10)
        print("已发送")
    except: pass
else:
    print("\n".join(msg))
