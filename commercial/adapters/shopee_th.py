"""Shopee Thailand listing adapter — Thai, title 25–100, keyword library."""
from __future__ import annotations

from typing import Any

from .compliance_gate import gate_listing, load_rules

MARKET = "shopee_th"

REQUIRED_KEYWORDS = ("กล่องแบ่งลิ้นชัก", "ที่จัดระเบียบลิ้นชัก")


def _cm_line(sku: dict[str, Any]) -> str:
    parts = []
    label_th = {
        "large": "ใหญ่",
        "medium_long": "ยาว",
        "medium": "กลาง",
        "small": "เล็ก",
    }
    for s in sku.get("sizes") or []:
        d = s.get("dims_cm_approx") or {}
        lab = label_th.get(s.get("label"), s.get("label"))
        if d:
            parts.append(
                f"{s.get('qty')} ชิ้น{lab} (~{d.get('l'):.0f}x{d.get('w'):.0f}x{d.get('h'):.0f} cm)"
            )
        else:
            parts.append(f"{s.get('qty')} ชิ้น{lab}")
    return "; ".join(parts)


def generate(sku: dict[str, Any]) -> dict[str, Any]:
    pcs = sku.get("piece_count", 0)
    pads = sku.get("pad_count", 0)
    n_sizes = len(sku.get("sizes") or [])
    brand = sku.get("brand") or ""

    # Thai-first title; Latin "Organizer" ok; not ALL-CAPS; no promo spam
    title = (
        f"กล่องแบ่งลิ้นชัก {pcs} ชิ้น พลาสติกใส {n_sizes} ขนาด กันลื่น Organizer"
    )
    if len(title) < 25:
        title = f"ที่จัดระเบียบลิ้นชัก {pcs} ชิ้น พลาสติกใส {n_sizes} ขนาด Organizer"
    if len(title) > 100:
        title = title[:100].rstrip()

    cm = _cm_line(sku)
    bullets = [
        (
            f"ชุด {pcs} ชิ้น {n_sizes} ขนาด — {cm}; จัดเลย์เอาต์ลิ้นชักได้ตามต้องการ"
        ),
        (
            "พลาสติกใส — มองเห็นเครื่องสำอาง เครื่องครัว ของใช้ในห้องน้ำ หรือเครื่องเขียนได้ชัด"
        ),
        (
            f"แผ่นซิลิโคนกันลื่น {pads} ชิ้น — ติดมุมกล่องช่วยลดการเลื่อนเมื่อเปิด-ปิดลิ้นชัก"
        ),
        (
            "โมดูลาร์ ซ้อนเก็บได้ — วางเรียงในลิ้นชัก; กล่องว่างซ้อนกันประหยัดที่"
        ),
        (
            "ทำความสะอาดง่าย — เช็ดด้วยผ้าชุบน้ำหรือล้างมือ ไม่ต้องใช้เครื่องมือ"
        ),
        (
            "ใช้ได้หลายจุด — ลิ้นชักเมคอัพ ใต้ซิงก์ ครัว และโต๊ะทำงาน"
        ),
    ]

    description = (
        f"จัดระเบียบลิ้นชักด้วยชุดกล่องแบ่งพลาสติกใส {pcs} ชิ้น {n_sizes} ขนาด "
        f"เหมาะกับเมคอัพ ห้องน้ำ ครัว และโต๊ะทำงาน มาพร้อมแผ่นซิลิโคนกันลื่น "
        f"จัดเรียงแบบโมดูลาร์ในลิ้นชัก กล่องว่างซ้อนเก็บได้ "
        f"เช็ดด้วยผ้าชุบน้ำหรือล้างมือ สำหรับจัดเก็บของใช้ในบ้านเท่านั้น"
    )
    if len(description) < 100:
        description += " วัสดุพลาสติก PET ใส ทนใช้งานในบ้าน"

    keywords = [
        "กล่องแบ่งลิ้นชัก",
        "ที่จัดระเบียบลิ้นชัก",
        "organizer",
        "กล่องเก็บของลิ้นชัก",
        "กล่องแบ่งลิ้นชักพลาสติกใส",
        "organizer ลิ้นชัก",
        f"กล่องแบ่งลิ้นชัก {pcs} ชิ้น {n_sizes} ขนาด กันลื่น",
        "ที่จัดระเบียบลิ้นชักเมคอัพครัวห้องน้ำ",
        "กล่องลิ้นชักใส ประหยัดพื้นที่",
    ]
    for req in REQUIRED_KEYWORDS:
        if req not in keywords:
            keywords.insert(0, req)

    listing = {
        "market": MARKET,
        "locale": "th_TH",
        "brand": brand,
        "title": title,
        "bullets": bullets,
        "highlights": bullets,
        "description": description,
        "keywords": keywords,
        "keyword_library": {
            "primary": [
                "กล่องแบ่งลิ้นชัก",
                "ที่จัดระเบียบลิ้นชัก",
                "organizer",
                "กล่องเก็บของลิ้นชัก",
                "กล่องแบ่งลิ้นชักพลาสติกใส",
                "organizer ลิ้นชัก",
            ],
            "long_tail": keywords[6:],
        },
    }
    rules = load_rules()
    listing["compliance"] = gate_listing(listing, MARKET, rules)
    return listing
