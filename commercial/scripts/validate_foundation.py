#!/usr/bin/env python3
"""Step 0 foundation validator: SKU schema + title length gates."""
from __future__ import annotations
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "sku.schema.json"
FIXTURE = ROOT / "fixtures" / "drawer_organizer_25pcs.json"
TITLES = ROOT / "fixtures" / "sample_titles.json"
RULES = ROOT / "rules" / "compliance.yaml"
UPSTREAM_LICENSE = ROOT.parent / "LICENSE"

def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(1)

def ok(msg: str) -> None:
    print(f"PASS: {msg}")

def main() -> None:
    if not UPSTREAM_LICENSE.is_file():
        fail(f"upstream LICENSE missing: {UPSTREAM_LICENSE}")
    ok(f"upstream LICENSE present ({UPSTREAM_LICENSE.name})")

    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    try:
        import jsonschema
        jsonschema.validate(instance=fixture, schema=schema)
        ok("drawer fixture validates against sku.schema.json")
    except ImportError:
        # Minimal required-key check without jsonschema
        for k in schema.get("required", []):
            if k not in fixture:
                fail(f"fixture missing required key: {k}")
        sizes = fixture.get("sizes") or []
        if sum(s.get("qty", 0) for s in sizes) != fixture.get("piece_count"):
            fail("piece_count does not equal sum of size qtys")
        ok("drawer fixture basic schema checks (install jsonschema for full validate)")

    if yaml is None:
        # Parse length limits with a tiny fallback
        text = RULES.read_text(encoding="utf-8")
        limits = {
            "amazon_us": 75,
            "shopee_id": 100,
            "meli_mx": 60,
        }
        ok("compliance.yaml present (PyYAML not installed; using baked limits)")
    else:
        rules = yaml.safe_load(RULES.read_text(encoding="utf-8"))
        limits = {
            "amazon_us": rules["markets"]["amazon_us"]["title_max_chars"],
            "shopee_id": rules["markets"]["shopee_id"]["title_max_chars"],
            "meli_mx": rules["markets"]["meli_mx"]["title_max_chars"],
        }
        ok("compliance.yaml loaded")

    titles = json.loads(TITLES.read_text(encoding="utf-8"))
    checks = [
        ("amazon_en_v0", "amazon_us", False),
        ("amazon_en_fixed", "amazon_us", True),
        ("shopee_id_v0", "shopee_id", False),
        ("shopee_id_fixed", "shopee_id", True),
        ("meli_mx_v0", "meli_mx", False),
        ("meli_mx_fixed", "meli_mx", True),
    ]
    for key, market, expect_pass in checks:
        t = titles[key]
        n = len(t)
        lim = limits[market]
        passed = n <= lim
        status = "pass" if passed else "fail"
        print(f"TITLE {key}: {n}/{lim} chars -> {status}")
        if passed != expect_pass:
            fail(f"{key}: expected {'pass' if expect_pass else 'fail'}, got {status}")
    ok("sample title length gates behave as expected (v0 over-limit, fixed under-limit)")
    print("FOUNDATION_OK")

if __name__ == "__main__":
    main()
