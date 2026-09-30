#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""上传逐字稿到 ark-transcripts"""
import base64, json, os, sys, urllib.request, urllib.parse, time

REPO = "ark-notes/ark-transcripts"
API = "https://api.github.com"

def token():
    return open("/app/workspace/build/.token").read().strip()

def gh(method, path, data=None):
    req = urllib.request.Request(API+path,
        data=json.dumps(data).encode() if data else None, method=method,
        headers={"Authorization":f"Bearer {token()}","Accept":"application/vnd.github+json",
                 "User-Agent":"ark-up","Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode())

def upload(local, remote=None):
    name = remote or os.path.basename(local)
    b64 = base64.b64encode(open(local,"rb").read()).decode()
    p = f"/repos/{REPO}/contents/{urllib.parse.quote(name)}"
    sha = None
    try: sha = gh("GET", p).get("sha")
    except Exception: pass
    data = {"message": f"add/update {name}", "content": b64}
    if sha: data["sha"] = sha
    for attempt in range(3):
        try:
            r = gh("PUT", p, data)
            if "content" in r: return True, r["content"]["path"]
            return False, str(r)[:80]
        except Exception as e:
            if attempt == 2: return False, str(e)[:60]
            time.sleep(3)
    return False, "?"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 upload.py <文件> [远程名]"); sys.exit(1)
    ok, msg = upload(sys.argv[1], sys.argv[2] if len(sys.argv)>2 else None)
    print(("✅ " if ok else "❌ ") + msg)
