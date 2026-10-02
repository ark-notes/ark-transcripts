#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""下载上传区文件（用 download_url，支持大文件）"""
import json, urllib.request, urllib.parse, os, sys
WS='/app/workspace/build'; REPO='ark-notes/ark-uploads'; DEST=f'{WS}/user-uploads'
def tok():
    for f in ['.upload_token','.token']:
        p=os.path.join(WS,f)
        if os.path.exists(p): return open(p).read().strip()
def api(path,t):
    url=f"https://api.github.com/repos/{REPO}/contents/"+urllib.parse.quote(path)
    r=urllib.request.Request(url,headers={'Authorization':f'token {t}','Accept':'application/vnd.github+json'})
    return json.loads(urllib.request.urlopen(r,timeout=30).read())
def dl(url,t,dest):
    req=urllib.request.Request(url,headers={'Authorization':f'token {t}'})
    data=urllib.request.urlopen(req,timeout=300).read()
    os.makedirs(os.path.dirname(dest),exist_ok=True)
    open(dest,'wb').write(data)
    return len(data)
def pull(path,t,d=0):
    n=0
    try: items=api(path,t)
    except Exception: return 0
    if not isinstance(items,list): return 0
    for it in items:
        if it['name'] in ('.gitkeep','README.md'): continue
        if it['type']=='dir' and d<3: n+=pull(it['path'],t,d+1)
        elif it['type']=='file':
            try:
                info=api(it['path'],t)
                dest=os.path.join(DEST,it['path'])
                # 小文件用 content；大文件用 download_url
                sz=info.get('size',0)
                if sz < 500*1024 and info.get('content'):
                    import base64
                    raw=base64.b64decode(info['content'])
                    os.makedirs(os.path.dirname(dest),exist_ok=True)
                    open(dest,'wb').write(raw)
                    print(f"  ⬇ {it['path']} ({len(raw)}B via content)")
                else:
                    du=info.get('download_url')
                    if not du: print(f"  ✗ {it['path']}: 无 download_url"); continue
                    n2=dl(du,t,dest)
                    print(f"  ⬇ {it['path']} ({n2}B via download_url)")
                n+=1
            except Exception as e: print(f"  ✗ {it['path']}: {str(e)[:60]}")
    return n
t=tok(); os.makedirs(DEST,exist_ok=True)
n=pull('',t)
print(f"\n✅ 下载 {n} 个到 {DEST}")
