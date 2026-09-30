#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""同步网站到 ark-notes.github.io"""
import base64, json, os, urllib.request, urllib.parse, time

REPO = "ark-notes/ark-notes.github.io"
SITE = "/app/workspace/build/site"

def token():
    return open("/app/workspace/build/.token_site").read().strip()

def gh(method, path, data=None):
    req = urllib.request.Request("https://api.github.com"+path,
        data=json.dumps(data).encode() if data else None, method=method,
        headers={"Authorization":f"Bearer {token()}","Accept":"application/vnd.github+json",
                 "User-Agent":"sync","Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())

def upload(local, remote):
    for attempt in range(3):
        try:
            b64 = base64.b64encode(open(local,"rb").read()).decode()
            p = f"/repos/{REPO}/contents/{urllib.parse.quote(remote)}"
            sha = None
            try: sha = gh("GET", p).get("sha")
            except Exception: pass
            data = {"message": f"sync {remote}", "content": b64}
            if sha: data["sha"] = sha
            r = gh("PUT", p, data)
            return ("content" in r), str(r.get("message",""))
        except Exception as e:
            if attempt == 2: return False, str(e)[:60]
            time.sleep(3)
    return False, "?"

def main():
    targets=[]
    for root, dirs, files in os.walk(SITE):
        dirs[:] = [d for d in dirs if d != ".git" and d != "transcripts"]
        for fn in files:
            if fn.startswith(".") or fn.endswith((".bak",".tmp")): continue
            full=os.path.join(root,fn)
            rel=os.path.relpath(full,SITE).replace("\\","/")
            targets.append((full,rel))
    print(f"=== 同步 {len(targets)} 个文件 ===\n")
    ok=fail=0
    for local,remote in sorted(targets):
        s,m = upload(local,remote)
        if s: ok+=1
        else:
            fail+=1; print(f"  ❌ {remote}: {m[:50]}")
    print(f"\n✅ {ok} 成功 / ❌ {fail} 失败")

if __name__ == "__main__":
    main()
