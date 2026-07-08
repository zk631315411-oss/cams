"""
Build a combined evidence pool for chapter-2 MVP question analysis.

The pool combines:
- cams工作台/data/cards_ch2.json
- cams工作台/data/cards_v6_except_ch2_sentence.json

Each card keeps its own original evidence_scope, so downstream mappings can tell
whether a citation came from chapter 2 or from the cross-chapter fallback pool.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
DATA = ROOT / "cams工作台" / "data"
OUTPUT = DATA / "cards_ch2_plus_v6_except_ch2_sentence.json"

INPUTS = [
    ("ch2", DATA / "cards_ch2.json"),
    ("v6-except-ch2", DATA / "cards_v6_except_ch2_sentence.json"),
]


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    cards: list[dict[str, Any]] = []
    input_stats = []
    seen_ids = set()
    duplicates = []

    for scope, path in INPUTS:
        raw = read_json(path)
        source_cards = raw.get("cards", raw) if isinstance(raw, dict) else raw
        if not isinstance(source_cards, list):
            raise ValueError(f"{path} does not contain a card list")
        input_stats.append({"scope": scope, "path": str(path), "cards": len(source_cards)})
        for card in source_cards:
            cid = card.get("card_id")
            if not cid:
                continue
            if cid in seen_ids:
                duplicates.append(cid)
                continue
            seen_ids.add(cid)
            cards.append(card)

    payload = {
        "schema_version": "ch2_plus_v6_except_ch2_sentence_cards_v1",
        "asset_note": (
            "Combined textbook evidence pool for chapter-2 MVP option-evidence binding. "
            "It combines second-chapter sentence cards with cross-chapter fallback sentence cards. "
            "Each card keeps its original evidence_scope; this file is not an exam-point asset."
        ),
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "inputs": input_stats,
        "cards": cards,
        "stats": {
            "cards": len(cards),
            "duplicates_skipped": len(duplicates),
        },
        "duplicates_skipped": duplicates[:200],
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload["stats"], ensure_ascii=False, indent=2))
    print(f"Wrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
