#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
沙箱重启后一键完整恢复
拉回：规则 + 需求总表 + 深挖成果 + 知识库 + 逐字稿 + 网站全站
用法：cd /app/workspace/build && python3 restore.py
"""
import json, urllib.request, urllib.parse, base64, os

WS = '/app/workspace/build'
TRANS_REPO = 'ark-notes/ark-transcripts'
SITE_REPO = 'ark-notes/ark-notes.github.io'

def tok(name):
    p = os.path.join(WS, name)
    if not os.path.exists(p):
        print(f"  ❌ 缺 {name}（需从对话记录找 Token）")
        return None
    return open(p).read().strip()

def api(repo, path, token):
    url = f"https://api.github.com/repos/{repo}/contents/" + urllib.parse.quote(path)
    r = urllib.request.Request(url, headers={
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github+json'})
    return json.loads(urllib.request.urlopen(r, timeout=30).read())

def pull_file(repo, path, dest, token):
    try:
        d = api(repo, path, token)
        if d.get('type') != 'file':
            return False
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        open(dest, 'wb').write(base64.b64decode(d['content']))
        return True
    except Exception:
        return False

def pull_tree(repo, token, repo_path, dest_dir):
    cnt = 0
    try:
        items = api(repo, repo_path, token)
    except Exception:
        return 0
    if not isinstance(items, list):
        return 0
    for it in items:
        if it['type'] == 'dir':
            cnt += pull_tree(repo, token, it['path'], os.path.join(dest_dir, it['name']))
        elif it['type'] == 'file':
            if pull_file(repo, it['path'], os.path.join(dest_dir, it['name']), token):
                cnt += 1
    return cnt

def ensure_fonts():
    """沙箱重启会清空系统字体 → 必须重装中文"""
    import subprocess
    try:
        out = subprocess.run(['fc-list'], capture_output=True, text=True, timeout=15).stdout
        if 'wqy' in out.lower() or 'microhei' in out.lower():
            print("⓪ 中文字体: ✓ 已存在")
            return
    except Exception:
        pass
    # 顺带装 megatools（读 Mega 分享链接）
    try:
        if not shutil.which('megadl'):
            subprocess.run(['sudo','agent-pkg','install','megatools'],capture_output=True,timeout=180)
    except Exception: pass
    print("⓪ 中文字体: 缺失 → 安装中...")
    try:
        subprocess.run(['sudo', 'agent-pkg', 'install', 'fonts-wqy-microhei'],
                       capture_output=True, timeout=180)
        subprocess.run(['fc-cache', '-f'], capture_output=True, timeout=60)
        print("⓪ 中文字体: ✓ 已安装")
    except Exception as e:
        print(f"⓪ 中文字体: ✗ {e}")

def main():
    print("=" * 56)
    print("  ARK 项目 · 沙箱完整恢复")
    print("=" * 56)
    ensure_fonts()
    tt = tok('.token')
    ts = tok('.token_site')

    # ① 规则 + 需求总表 + 脚本
    if tt:
        os.makedirs(f'{WS}/rules', exist_ok=True)
        for src in ['_tools/核心规则.md', '_tools/开工自检.md', '_tools/需求总表.md',
                    '_tools/BOOT.md', '_tools/恢复脚本.py', '_tools/sync_site.py', '_tools/upload.py',
                    '_tools/qa_audit.py']:
            dst = f'{WS}/' + os.path.basename(src)
            if '核心规则' in src or '开工自检' in src:
                dst = f'{WS}/rules/' + os.path.basename(src)
            if '需求总表' in src:
                dst = f'{WS}/REQUIREMENTS.md'
            if 'qa_audit' in src:
                dst = f'{WS}/qa/audit.py'
            ok = pull_file(TRANS_REPO, src, dst, tt)
            print(f"① {'✓' if ok else '✗'} {os.path.basename(src)}")

    # ② 知识库
    if tt:
        n = pull_tree(TRANS_REPO, tt, '_knowledge', f'{WS}/知识库')
        print(f"② 知识库: ✓ {n} 个文件")

    # ③ 深挖成果（兜底按已知文件名）
    if tt:
        os.makedirs(f'{WS}/深挖', exist_ok=True)
        try:
            items = api(TRANS_REPO, '_knowledge/D1_网站/深挖', tt)
            k = 0
            for it in items:
                if it.get('type') == 'file' and it['name'].endswith('.md'):
                    if pull_file(TRANS_REPO, it['path'], f'{WS}/深挖/{it["name"]}', tt):
                        k += 1
            print(f"③ 深挖成果: ✓ {k} 份（自动列举）")
        except Exception as e:
            print(f"③ 深挖成果: ✗ {e}")

    # ④ 逐字稿
    if tt:
        n = pull_tree(TRANS_REPO, tt, '', f'{WS}/transcripts')
        print(f"④ 逐字稿: ✓ {n} 支")

    # ⑤ 网站全站（根目录扁平）
    if ts:
        try:
            items = api(SITE_REPO, '', ts)
            n = 0
            os.makedirs(f'{WS}/site', exist_ok=True)
            for it in items:
                if it['type'] == 'file':
                    if pull_file(SITE_REPO, it['name'], f'{WS}/site/{it["name"]}', ts):
                        n += 1
                elif it['type'] == 'dir':
                    n += pull_tree(SITE_REPO, ts, it['name'], f'{WS}/site/{it["name"]}')
            print(f"⑤ 网站全站: ✓ {n} 个文件")
        except Exception as e:
            print(f"⑤ 网站全站: ✗ {e}")

    print("=" * 56)
    print("完成。开工前读 REQUIREMENTS.md + rules/核心规则.md")
    print("=" * 56)

if __name__ == '__main__':
    main()
