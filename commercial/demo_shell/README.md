# demo_shell — 第3步中文演示壳

本地/内网小服务：中文表单 → `pipeline.build_pack` → 三站文案 + 词库 + 合规红黄绿 → 下载 Markdown / 按站复制。

**不做支付、不做计费多租户、不做第4步录屏。**

## 启动

```bash
cd /workspace/advertools/commercial
source .venv/bin/activate
export DEMO_SHELL_PASSWORD=demo2026   # 可选，默认即此值
./demo_shell/run.sh
# 或：PYTHONPATH=. python -m demo_shell
```

- URL: http://127.0.0.1:8765/
- 认证: HTTP Basic（用户名任意，密码 = `DEMO_SHELL_PASSWORD`）
- 默认预填: `fixtures/drawer_organizer_25pcs.json`

## API（冒烟用）

```bash
# health
curl -u demo:demo2026 http://127.0.0.1:8765/api/health

# fixture defaults
curl -u demo:demo2026 http://127.0.0.1:8765/api/fixture

# generate from fixture fields
curl -u demo:demo2026 -H 'Content-Type: application/json' \
  -d @<(python -c "import json;from demo_shell.sku_form import load_default_fixture;print(json.dumps(load_default_fixture()))") \
  http://127.0.0.1:8765/api/generate
```

## 布局

- `server.py` — stdlib `ThreadingHTTPServer` + Basic Auth
- `sku_form.py` — 表单 → SKU dict（缺省 forbidden_claims / sizes 从 fixture 补）
- `templates/index.html` — 单页中文 UI
- `tmp/` — 生成物临时落盘
- `run.sh` — 一键启动

复用：`pipeline.build_pack` / `render_listing_pack_md`；不改上游 `advertools/` 包源码。

## Windows（GM241）

```powershell
cd D:\Apps\advertools\commercial
$env:DEMO_SHELL_PASSWORD='demo2026'
$env:PYTHONPATH=(Get-Location).Path
.\demo_shell\run.ps1
# 或: python -m demo_shell
```

路径：`D:\Apps\advertools\commercial\demo_shell\`

