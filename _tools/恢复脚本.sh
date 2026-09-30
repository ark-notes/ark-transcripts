#!/bin/bash
# 沙箱重启后，一键恢复环境
echo "=== 1. 装中文字体 ==="
fc-list :lang=zh 2>/dev/null | wc -l | grep -q "^0$" && sudo agent-pkg install fonts-wqy-microhei fonts-wqy-zenhei 2>&1 | tail -1 || echo "字体已存在"

echo "=== 2. 装 Python 依赖 ==="
python3 -c "import faster_whisper" 2>/dev/null || pip install --user -q "faster-whisper==1.0.3" requests
python3 -c "import playwright" 2>/dev/null || pip install --user -q playwright
python3 -c "import docx" 2>/dev/null || pip install --user -q python-docx
python3 -c "import opencc" 2>/dev/null || pip install --user -q opencc-python-reimplemented

echo "=== 3. 检查 Token ==="
ls /app/workspace/build/.token /app/workspace/build/.token_site 2>/dev/null || echo "⚠️ Token 需重新提供"

echo "=== 4. 从 GitHub 拉回网站 ==="
python3 /app/workspace/build/pull_site.py 2>/dev/null || echo "（pull_site.py 不存在，需先拉脚本）"

echo "完成"
