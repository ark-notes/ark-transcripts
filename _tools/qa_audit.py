#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""发布前自检"""
import sys, os, glob, re, json
from playwright.sync_api import sync_playwright
WS='/app/workspace/build/site'; BASE='http://127.0.0.1:10340'
ISSUES=[]
def add(p,k,d,sev='warn'): ISSUES.append({'page':p,'kind':k,'detail':str(d),'sev':sev})
def main():
    pages=sorted(os.path.basename(p) for p in glob.glob(f'{WS}/*.html'))
    print(f"检查 {len(pages)} 个页面...\n")
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path="/usr/bin/chromium",args=["--no-sandbox","--disable-dev-shm-usage"])
        for w in [390,360,320]:
            pg=b.new_page(viewport={"width":w,"height":844})
            for page in pages:
                try:
                    pg.goto(f"{BASE}/{page}",timeout=18000); pg.wait_for_timeout(400)
                    r=pg.evaluate("""()=>{const out={small:[],broken:[],overflow:false,wide:[]};
                      document.querySelectorAll('p,li,td,th,figcaption,span,a,div').forEach(e=>{
                        const t=(e.innerText||'').trim(); if(t.length<3) return;
                        const s=getComputedStyle(e); if(s.display==='none'||s.visibility==='hidden') return;
                        const fs=parseFloat(s.fontSize);
                        if(fs<13){const k=fs+'|'+(e.className||e.tagName).toString().slice(0,20);
                          if(!out.small.some(x=>x.k===k)) out.small.push({k,fs,cls:(e.className||e.tagName).toString().slice(0,22),t:t.slice(0,16)});}});
                      document.querySelectorAll('img').forEach(i=>{const s=i.getAttribute('src');
                        if(!s) return; if(i.complete&&i.naturalWidth===0) out.broken.push(s);});
                      out.overflow=document.documentElement.scrollWidth>window.innerWidth+2;
                      document.querySelectorAll('h1,h2,.hero p,.site-def-text').forEach(e=>{
                        const s=getComputedStyle(e); if(s.display==='none') return;
                        const lh=parseFloat(s.lineHeight)||parseFloat(s.fontSize)*1.4;
                        const lines=Math.round(e.getBoundingClientRect().height/lh);
                        if(lines>=5) out.wide.push({tag:e.tagName+'.'+(e.className||'').toString().slice(0,16),lines,t:(e.innerText||'').slice(0,20)});});
                      return out;}""")
                    for x in r['small'][:2]: add(page,'字号过小',f"{x['fs']}px .{x['cls']} 「{x['t']}」",'error')
                    for s in r['broken'][:3]: add(page,'坏图',s,'error')
                    if r['overflow'] and w==390: add(page,'横向溢出',f'{w}px','error')
                    if r['wide'] and w==320:
                        for x in r['wide'][:2]: add(page,'文字爆行',f"{x['tag']} {x['lines']}行",'warn')
                except Exception as e: add(page,'加载失败',str(e)[:60],'error')
            pg.close()
        b.close()
    for page in pages:
        try:
            h=open(f'{WS}/{page}',encoding='utf-8').read()
            talks=len(re.findall(r'class="talk"',h)); srcs=len(re.findall(r'class="src"',h))
            if talks>=3 and srcs==0: add(page,'缺出处',f'{talks}块/0出处','warn')
            if '<title>' not in h: add(page,'缺 title','','error')
        except Exception: pass
    print("="*60)
    if not ISSUES: print("✅ 全部通过，无问题")
    else:
        seen=set(); uniq=[]
        for i in ISSUES:
            k=(i['page'],i['kind'],i['detail'][:30])
            if k in seen: continue
            seen.add(k); uniq.append(i)
        errs=[i for i in uniq if i['sev']=='error']
        print(f"❌ {len(errs)} 错误 / ⚠️ {len(uniq)-len(errs)} 警告\n")
        for i in uniq:
            print(("❌ " if i['sev']=='error' else "⚠️  ")+f"[{i['page']}] {i['kind']}: {i['detail']}")
    print("="*60)
    json.dump(ISSUES,open('/app/workspace/build/qa/last_report.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
    return 1 if any(i['sev']=='error' for i in ISSUES) else 0
if __name__=='__main__': sys.exit(main())
