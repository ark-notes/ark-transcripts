#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
沙箱重启后一键恢复：规则 + Token + 逐字稿 + 脚本
用途：每次开工前自动跑（或沙箱重启后跑）
"""
import json, urllib.request, urllib.parse, base64, os, sys

WS = '/app/workspace/build'
TRANS_REPO = 'ark-notes/ark-transcripts'
SITE_REPO = 'ark-notes/ark-notes.github.io'

def tok(name):
    p = os.path.join(WS, name)
    if not os.path.exists(p):
        print(f"❌ 缺 {name} —— 需要从对话记录找 Token")
        return None
    return open(p).read().strip()

def api(repo, path, token, method='GET', data=None):
    url = f"https://api.github.com/repos/{repo}/contents/" + urllib.parse.quote(path)
    body = json.dumps(data).encode() if data else None
    r = urllib.request.Request(url, data=body, method=method,
        headers={'Authorization': f'token {token}',
                 'Accept': 'application/vnd.github+json',
                 'Content-Type': 'application/json'})
    return json.loads(urllib.request.urlopen(r, timeout=30).read())

def listdir(repo, token, path=''):
    try:
        return api(repo, path, token) if path else json.loads(
            urllib.request.urlopen(urllib.request.Request(
                f"https://api.github.com/repos/{repo}/contents/",
                headers={'Authorization': f'token {token}'}), timeout=30).read())
    except Exception as e:
        print(f"  ⚠️ {repo}/{path}: {e}")
        return []

def pull(repo, token, path, dest):
    try:
        d = api(repo, path, token)
        raw = base64.b64decode(d['content'])
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        open(dest, 'wb').write(raw)
        return len(raw)
    except Exception as e:
        return None

def main():
    print("=" * 50)
    print("  ARK 项目 — 沙箱恢复")
    print("=" * 50)
    tt = tok('.token')
    ts = tok('.token_site')

    # ① 规则（最重要）
    if tt:
        os.makedirs(f'{WS}/rules', exist_ok=True)
        n = pull(TRANS_REPO, tt, '_tools/核心规则.md', f'{WS}/rules/核心规则.md')
        print(f"① 核心规则: {'✓ ' + str(n) + ' 字' if n else '✗ 失败'}")

    # ② 逐字稿
    if tt:
        items = listdir(TRANS_REPO, tt)
        cnt = 0
        for it in items:
            if it['type'] == 'file' and it['name'].endswith('.txt'):
                if pull(TRANS_REPO, tt, it['name'], f'{WS}/transcripts/{it["name"]}'):
                    cnt += 1
        print(f"② 逐字稿: ✓ {cnt} 支")

    # ③ 网站
    if ts:
        items = listdir(SITE_REPO, ts)
        print(f"③ 网站根: {len(items)} 项（用 pull_site.py 拉完整站）")

    print("=" * 50)
    print("完成。开工前请先读 rules/核心规则.md")
    print("=" * 50)

if __name__ == '__main__':
    main()
