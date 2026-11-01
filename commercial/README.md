# commercial/ — Stevenfang88 overlay (MIT upstream preserved)

Upstream: https://github.com/eliasdabbas/advertools (MIT License — see ../LICENSE).
Do **not** modify upstream package code for product rules; put adapters and gates here.

## Layout
- `schemas/sku.schema.json` — SKU input contract
- `fixtures/drawer_organizer_25pcs.json` — golden sample (T1 Listing Pack v0)
- `fixtures/drawer_organizer_25pcs.generated.json` — Step 1 sample output (three markets)
- `rules/compliance.yaml` — claim bans + title length hard limits
- `adapters/` — Step 1 marketplace generators + compliance gate
- `pipeline/` — Step 2 one-command Listing Pack export (MD + JSON + compliance)
- `scripts/validate_foundation.py` — schema + compliance self-check (Step 0)
- `scripts/generate_listings.py` — generate three market packs (Step 1)
- `scripts/smoke_adapters.py` — Step 1 smoke assertions
- `scripts/export_listing_pack.py` — thin wrapper for Step 2 CLI
- `scripts/smoke_pipeline.py` — Step 2 acceptance smoke
- `demo_shell/` — Step 3 Chinese local web UI (Basic Auth, no payment)
- `scripts/smoke_demo_shell.py` — Step 3 offline smoke

## Foundation acceptance (Step 0)
1. Fixture loads and passes JSON Schema
2. Compliance rules load; sample titles can be scored pass/fail by length limits
3. Upstream LICENSE present at repo root

## Step 1 — adapters
```bash
source .venv/bin/activate
python scripts/generate_listings.py
python scripts/smoke_adapters.py
```
See `adapters/README.md`.

## Step 2 — Listing Pack pipeline
Turns a SKU JSON into a T1-aligned multi-market Listing Pack (Markdown + JSON)
plus a compliance report. Adapters own generation; pipeline owns pack export and
the overall `listable` gate.

**Primary command** (cwd = `commercial/`, venv active):

```bash
cd /workspace/advertools/commercial
source .venv/bin/activate
python -m pipeline.run --sku fixtures/drawer_organizer_25pcs.json --out-dir pipeline/out
```

Equivalent wrapper:

```bash
python scripts/export_listing_pack.py --sku fixtures/drawer_organizer_25pcs.json --out-dir pipeline/out
```

Smoke / acceptance:

```bash
python scripts/smoke_pipeline.py
```

### Outputs (drawer sample)
Under `pipeline/out/` (names include SKU slug):
- `*_listing_pack.md` — T1-mirrored sections (SKU, Amazon, Shopee ID, MELI MX, keywords, compliance)
- `*_listing_pack.json` — machine-readable pack + `listable` + `human_review_required`
- `*_listing_pack-compliance.md` — short compliance report

Exit code **0** and `listable: true` when all three market compliance gates pass.
Wording diffs vs the hand T1 pack are flagged as `human_review_required` only —
they do **not** flip `listable`.

GitHub fork to personal account: deferred until Cursor GitHub is connected; local vendor clone is the Step 0 deliverable.

## Step 3 — 中文演示壳
本地网页：填 SKU → 一键生成三站 Listing Pack（合规灯 + Markdown 下载）。无支付。

```bash
cd /workspace/advertools/commercial
source .venv/bin/activate
export DEMO_SHELL_PASSWORD=demo2026
./demo_shell/run.sh
# 打开 http://127.0.0.1:8765/  （Basic Auth：任意用户名 / 上列口令）
```

详见 `demo_shell/README.md`。
