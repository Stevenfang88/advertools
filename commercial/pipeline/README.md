# pipeline/ — Step 2 Listing Pack export

SKU JSON → adapters `generate_all` → Markdown Pack + JSON Pack + compliance report.

Amazon US, Shopee ID, and MELI MX `keyword_library` rows come from
`adapters/keyword_engine.py` (advertools `word_frequency`, `kw_generate`,
`ad_from_string`), then the same compliance gate as the titles.

```bash
cd /workspace/advertools/commercial
source .venv/bin/activate
python -m pipeline.run --sku fixtures/drawer_organizer_25pcs.json --out-dir pipeline/out
```

| Module | Role |
| --- | --- |
| `run.py` | CLI (`python -m pipeline.run`) |
| `pack.py` | Assemble pack, write artifacts, set `listable` |
| `render_md.py` | T1-mirrored Markdown |
| `render_compliance.py` | Short compliance report |
| `compare_t1.py` | Diff vs hand T1 → `human_review_required` only |
