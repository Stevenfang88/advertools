#!/usr/bin/env python3
"""Smoke / acceptance for Step 2 pipeline on the drawer fixture."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "pipeline" / "out"


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(1)


def ok(msg: str) -> None:
    print(f"PASS: {msg}")


def main() -> None:
    cmd = [
        sys.executable,
        "-m",
        "pipeline.run",
        "--sku",
        "fixtures/drawer_organizer_25pcs.json",
        "--out-dir",
        "pipeline/out",
    ]
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    print(proc.stdout)
    if proc.stderr:
        print(proc.stderr, file=sys.stderr)
    if proc.returncode != 0:
        fail(f"pipeline.run exit {proc.returncode} (want 0)")
    ok("pipeline.run exit 0")

    json_files = sorted(OUT.glob("*_listing_pack.json"))
    md_files = sorted(OUT.glob("*_listing_pack.md"))
    comp_files = sorted(OUT.glob("*-compliance.md"))
    if not json_files:
        fail("no pack JSON written")
    if not md_files:
        fail("no pack Markdown written")
    if not comp_files:
        fail("no compliance report written")
    ok(f"artifacts: {json_files[0].name}, {md_files[0].name}, {comp_files[0].name}")

    pack = json.loads(json_files[0].read_text(encoding="utf-8"))
    if pack.get("listable") is not True:
        fail(f"listable={pack.get('listable')!r} want True")
    ok("listable=true")

    markets = pack.get("markets") or {}
    for key in ("amazon_us", "shopee_id", "meli_mx"):
        title = (markets.get(key) or {}).get("title") or ""
        if not title.strip():
            fail(f"missing title for {key}")
        ok(f"{key} title present ({len(title)} chars)")

    if not pack.get("compliance", {}).get("all_pass"):
        fail("compliance.all_pass is false")
    ok("compliance.all_pass")

    # MD should contain section headers mirroring T1
    md = md_files[0].read_text(encoding="utf-8")
    for needle in (
        "## 0) SKU summary",
        "## A) Amazon US",
        "## B) Shopee Indonesia",
        "## C) Mercado Libre MX",
        "## D) Category keyword library",
        "## E) Compliance gate checks",
    ):
        if needle not in md:
            fail(f"MD missing section {needle!r}")
    ok("MD has T1-mirrored sections")

    print("\nSMOKE_PIPELINE_OK")
    print(f"json={json_files[0]}")
    print(f"md={md_files[0]}")
    print(f"compliance={comp_files[0]}")


if __name__ == "__main__":
    main()
