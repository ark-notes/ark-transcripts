#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查私有上传仓库（ark-uploads）有没有新文件"""
import json, urllib.request, urllib.parse, os, sys

WS='/app/workspace/build'
REPO='ark-notes/ark-uploads'

def tok():
    for f in ['.upload_token','.token']:
        p=os.path.join(WS,f)
        if os.path.exists(p): return open(p).read().strip()
    return None

def api(path,t):
    url=f"https://api.github.com/repos/{REPO}/contents/"+urllib.parse.quote(path)
    r=urllib.request.Request(url,headers={'Authorization':f'token {t}','Accept':'application/vnd.github+json'})
    return json.loads(urllib.request.urlopen(r,timeout=30).read())

def walk(path,t,d=0):
    out=[]
    try: items=api(path,t)
    except Exception: return out
    if not isinstance(items,list): return out
    for it in items:
        if it['name'] in ('.gitkeep','README.md'): continue
        if it['type']=='dir' and d<3: out+=walk(it['path'],t,d+1)
        elif it['type']=='file': out.append({'path':it['path'],'name':it['name'],'size':it.get('size',0)})
    return out

t=tok()
if not t: print("❌ 无 Token"); sys.exit(1)
print("检查上传区 ...\n")
files=walk('',t)
if not files: print("✅ 空（没有新上传）"); sys.exit(0)
print(f"📤 发现 {len(files)} 个文件：\n")
for f in files:
    s=f"{f['size']/1024:.1f}KB" if f['size']<1048576 else f"{f['size']/1048576:.1f}MB"
    print(f"  {f['path']}  ({s})")
