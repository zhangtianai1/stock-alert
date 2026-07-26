import requests, json, os, math
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))

def load_watchlist():
    path = os.path.join(BASE, "watchlist.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def fetch_klines(code, days=60):
    prefix = "sh" if code[0] == "6" else "sz"
    url = f"http://ifzq.gtimg.cn/appstock/app/fqkline/get?param={prefix}{code},day,,,{days},qfq"
    r = requests.get(url, timeout=10)
    d = r.json().get("data", {}).get(f"{prefix}{code}", {})
    klines = d.get("qfqday", d.get("day", []))
    return [{"date":k[0],"open":float(k[1]),"close":float(k[2]),"high":float(k[3]),"low":float(k[4]),"volume":float(k[5])} for k in klines if len(k)>=6]

def calc_ma(prices, n):
    return sum(prices[-n:])/n if len(prices)>=n else None

def calc_rsi(prices, n=14):
    if len(prices)<n+1: return 50
    gains=[max(prices[i]-prices[i-1],0) for i in range(-n,0)]
    losses=[max(prices[i-1]-prices[i],0) for i in range(-n,0)]
    ag=sum(gains)/n; al=sum(losses)/n
    if al==0: return 100 if ag>0 else 50
    return 100-100/(1+ag/al)

def analyze(code, name, klines):
    if len(klines)<20:
        return {"code":code,"name":name,"signal":"INSUFFICIENT_DATA","score":0}
    
    closes=[k["close"] for k in klines]
    cur=klines[-1]; prv=klines[-2]
    ma5=calc_ma(closes,5); ma20=calc_ma(closes,20)
    rsi=calc_rsi(closes)
    vols=[k["volume"] for k in klines]
    avg_vol=sum(vols[:-1])/max(len(vols)-1,1)
    vr=cur["volume"]/avg_vol if avg_vol>0 else 1
    
    h60=max(k["high"] for k in klines[-60:]) if len(klines)>=60 else max(k["high"] for k in klines)
    l60=min(k["low"] for k in klines[-60:]) if len(klines)>=60 else min(k["low"] for k in klines)
    p60=(cur["close"]-l60)/(h60-l60)*100 if h60>l60 else 50
    
    score=0.0; reasons=[]
    
    if ma5 and ma20:
        if cur["close"]>ma5>ma20: score+=2; reasons.append("多头")
        elif cur["close"]<ma5<ma20: score-=1; reasons.append("空头")
    if rsi<30: score+=1; reasons.append(f"超卖({rsi:.0f})")
    elif rsi<40: score+=0.5; reasons.append(f"偏低({rsi:.0f})")
    elif rsi>70: score-=1; reasons.append(f"超买({rsi:.0f})")
    elif rsi>60: score-=0.5
    if vr>1.2: score+=0.5; reasons.append(f"放量({vr:.1f}x)")
    elif vr<0.8: score-=0.5; reasons.append(f"缩量({vr:.1f}x)")
    if p60<30: score+=0.5; reasons.append("低位")
    elif p60>70: score-=0.5; reasons.append("高位")
    
    sig="STRONG_BUY" if score>=2.5 else "BUY" if score>=1 else "SELL" if score<=-1 else "HOLD"
    chg=(cur["close"]-prv["close"])/prv["close"]*100 if prv else 0
    
    return {"code":code,"name":name,"price":round(cur["close"],2),
        "chg_pct":round(chg,2),"ma5":round(ma5,2) if ma5 else None,
        "ma20":round(ma20,2) if ma20 else None,"rsi":round(rsi,1),
        "vol_ratio":round(vr,2),"pos_60":round(p60,1),
        "score":round(score,1),"signal":sig,"reasons":"; ".join(reasons[:3])}

def analyze_current_only(code, name, klines):
    """只用当日行情数据快速分析（不需要K线时用）"""
    return analyze(code, name, klines)

def main():
    config = load_watchlist()
    stocks = config.get("stocks", [])
    cash = config.get("cash", 0)
    initial = config.get("initial_capital", 100000)
    
    signals = {"update_time":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"signals":[],"alerts":[]}
    
    for s in stocks:
        code=s["code"]; name=s["name"]
        try:
            klines=fetch_klines(code)
            sig=analyze(code, name, klines)
        except Exception as e:
            sig={"code":code,"name":name,"signal":"FETCH_ERROR","score":0,"error":str(e)[:50]}
        
        sig["cost"]=s.get("cost",0)
        sig["shares"]=s.get("shares",0)
        sig["position_value"]=round(sig.get("price",0)*sig["shares"],2)
        sig["position_pnl"]=round((sig.get("price",0)-sig["cost"])*sig["shares"],2) if sig["cost"] else 0
        signals["signals"].append(sig)
        print(f"  {sig['name']:8s} {sig['signal']:12s} score={sig['score']:+.1f} RSI={sig.get('rsi',0):.0f}")
        
        # 生成告警
        ret=(sig["price"]-sig["cost"])/sig["cost"]*100 if sig["cost"]>0 else 0
        if ret<-14:
            signals["alerts"].append({"type":"STOP_LOSS_WARNING","code":code,"name":name,"msg":f"已亏损{ret:.1f}%，接近止损线(15%)"})
        if ret>19:
            signals["alerts"].append({"type":"TAKE_PROFIT_WARNING","code":code,"name":name,"msg":f"已盈利{ret:.1f}%，接近止盈线(20%)"})
    
    total_val=sum(s["position_value"] for s in signals["signals"])
    total=round(total_val+cash,2); pnl=round(total-initial,2); pnl_pct=round((total-initial)/initial*100,2)
    signals["portfolio"]={"stock_value":round(total_val,2),"cash":cash,"total":total,"pnl":pnl,"pnl_pct":pnl_pct}
    
    print(f"\n  总资产: {total:.0f}  盈亏: {pnl:+>.0f} ({pnl_pct:+.2f}%)")
    for a in signals["alerts"]:
        print(f"  ! {a['msg']}")
    
    with open(os.path.join(BASE,"_signals.json"),"w",encoding="utf-8") as f:
        json.dump(signals,f,ensure_ascii=False,indent=2)
    print(f"\n信号已保存 -> _signals.json ({len(signals['signals'])}只股票)")

if __name__=="__main__":
    main()
