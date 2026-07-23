#!/usr/bin/env python3
"""每日行情数据获取脚本 - GitHub Actions 运行"""
import requests, json, os, sys
from datetime import datetime

VIRTUAL_STOCKS = [
    ("603019","中科曙光",93.50,100), ("002185","华天科技",21.93,400),
    ("000063","中兴通讯",35.79,200), ("601899","紫金矿业",27.62,500),
    ("002415","海康威视",33.86,300), ("600276","恒瑞医药",55.36,100),
    ("600036","招商银行",37.55,200), ("600941","中国移动",88.42,100),
]
VIRTUAL_CASH = 34351; VIRTUAL_INITIAL = 100000

INDICES = {"sh000001":"上证指数","sh000300":"沪深300","sh000688":"科创50",
           "sh000016":"上证50","sh000905":"中证500","sz399001":"深证成指","sz399006":"创业板指"}

def fetch_quotes(codes):
    url = "http://qt.gtimg.cn/q=" + ",".join(codes)
    r = requests.get(url, timeout=10); r.encoding = "gbk"
    result = {}
    for line in r.text.strip().strip(";").split(";"):
        parts = line.strip().strip('"').split("~")
        if len(parts) > 37:
            result[parts[2]] = {
                "price": float(parts[3]), "chg_pct": float(parts[32]),
                "name": parts[1], "amount": float(parts[37]) if parts[37] else 0,
            }
    return result

def main():
    base = os.path.dirname(os.path.abspath(__file__))
    index_data = fetch_quotes(list(INDICES.keys()))
    stk_codes = ["sh"+s[0] if s[0][0]=="6" else "sz"+s[0] for s in VIRTUAL_STOCKS]
    stock_data = fetch_quotes(stk_codes)
    total_val = 0; positions = []
    for code, name, cost, shares in VIRTUAL_STOCKS:
        q = stock_data.get(code, {}); price = q.get("price",0)
        val = price*shares; pnl = val - cost*shares; total_val += val
        positions.append({"code":code,"name":name,"price":price,
            "chg_pct":q.get("chg_pct",0),"cost":cost,"shares":shares,
            "value":round(val,2),"pnl":round(pnl,2)})
    total = total_val + VIRTUAL_CASH; pnl_total = total - VIRTUAL_INITIAL
    indices = {}
    for code, name in INDICES.items():
        raw = code[2:]
        if raw in index_data:
            d = index_data[raw]; indices[code] = {"name":d["name"],"price":d["price"],"chg_pct":d["chg_pct"],"amount":d["amount"]}
    result = {"update_time":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"indices":indices,
              "virtual_portfolio":{"positions":positions,"cash":VIRTUAL_CASH,"stock_value":round(total_val,2),
              "total_value":round(total,2),"total_pnl":round(pnl_total,2),"total_pnl_pct":round(pnl_total/VIRTUAL_INITIAL*100,2)}}
    with open(os.path.join(base,"_market_data.json"),"w",encoding="utf-8") as f:
        json.dump(result,f,ensure_ascii=False,indent=2)
    print(f"[{result['update_time']}] 行情更新完成")
    for d in indices.values(): print(f"  {d['name']}: {d['price']:.2f} ({d['chg_pct']:+.2f}%)")
    p = result["virtual_portfolio"]
    print(f"  虚拟盘: {p['total_value']:.2f} 盈亏{p['total_pnl']:+.2f}({p['total_pnl_pct']:+.2f}%)")
if __name__ == "__main__": main()
