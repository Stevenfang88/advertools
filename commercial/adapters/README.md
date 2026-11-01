# adapters/ — Step 1 marketplace listing packs

Generate Amazon US (EN), Shopee SEA (ID / TH / PH), and Mercado Libre LatAm
(MX / BR / AR) listing copy from a SKU JSON fixture, then score with the
compliance gate.

## Layout

| File | Role |
| --- | --- |
| `compliance_gate.py` | Load `rules/compliance.yaml`; title length + banned claims + market style |
| `amazon_en.py` | Amazon US EN — title ≤75, 5 bullets, item highlights, backend terms |
| `shopee_id.py` | Shopee ID — Bahasa title 25–100, keywords (`organizer laci`, `sekat laci`) |
| `shopee_th.py` | Shopee TH — Thai title 25–100, keywords (`กล่องแบ่งลิ้นชัก`, `ที่จัดระเบียบลิ้นชัก`) |
| `shopee_ph.py` | Shopee PH — English PH title 25–100, keywords (`drawer organizer`, `drawer divider`) |
| `meli_mx.py` | MELI MX — Spanish title ≤60, no punctuation, no Spanglish |
| `meli_br.py` | MELI BR — Portuguese title ≤60, no punctuation, no EN product nouns |
| `meli_ar.py` | MELI AR — Spanish AR title ≤60, no punctuation, no Spanglish |
| `generate_all.py` | Orchestrator for all markets |

## Run (commercial venv)

```bash
cd /workspace/advertools/commercial
source .venv/bin/activate

# Generate packs + write fixtures/drawer_organizer_25pcs.generated.json
python scripts/generate_listings.py

# Smoke assertions (exit 0 on PASS)
python scripts/smoke_adapters.py
```

Optional flags:

```bash
python scripts/generate_listings.py \
  --fixture fixtures/drawer_organizer_25pcs.json \
  --out fixtures/drawer_organizer_25pcs.generated.json
```

## Python API

```python
from adapters.generate_all import generate_from_path, generate_all
from adapters import amazon_en, shopee_id, shopee_th, shopee_ph, meli_mx, meli_br, meli_ar

result = generate_from_path()  # uses golden drawer fixture
am = amazon_en.generate(sku_dict)
```

## Hard rules (reminders)

- Care: wipe / hand-rinse only — never claim dishwasher-safe
- No absolute BPA / fake social proof / child-safety seals
- Amazon title hard ≤75 (overflow ideas → item highlights ≤125)
- MELI (MX/BR/AR): local nouns first; spaces only; no EN product nouns in title
- Shopee: no ALL-CAPS, no promo spam; ID/TH/PH keyword stems required per market
