import requests, json, sys, os
from datetime import datetime
CFG=os.path.join(os.path.dirname(__file__),'alert_config.json')
WLT=os.path.join(os.path.dirname(__file__),'watchlist.json')
def load(p):
    with open(p,'r',encoding='utf-8') as f: return json.load(f)
def get_prices(codes):
    q=','.join(['sh'+c if c[0]=='6' else 'sz'+c for c,nm in codes])
    r=requests.get(f'http://qt.gtimg.cn/q={q}',timeout=8)
    res={}
    for line in r.text.strip().strip(';').split(';'):
        p=line.strip().strip('"').split('~')
        if len(p)>32: res[p[2]]=(p[1],float(p[3]) if p[3] else 0,float(p[32]) if p[32] else 0)
    return res
def check():
    cfg=load(CFG); stks=load(WLT).get('stocks',[])
    codes=[(s['code'],s.get('name','')) for s in stks]
    qs=get_prices(codes)
    now=datetime.now().strftime('%m-%d %H:%M')
    lines=[f'自选股监控 ({now})','']
    total=0
    for s in stks:
        d=qs.get(s['code'])
        if not d: continue
        nm,pr,ch=d
        cst=s.get('cost',0); sh=s.get('shares',100)
        pnl=(pr-cst)*sh if cst>0 else 0; total+=pnl
        tag='+' if pnl>=0 else ''
        lines.append(f"{'*' if ch>=5 or ch<=-3 else' '} {nm}: {pr:.2f} ({ch:+.2f}%) 盈亏{tag}{pnl:.0f}")
    lines.append(f'\n总盈亏: +{total:.0f}' if total>=0 else f'\n总盈亏: {total:.0f}')
    print('\n'.join(lines))
if __name__=='__main__': check()

