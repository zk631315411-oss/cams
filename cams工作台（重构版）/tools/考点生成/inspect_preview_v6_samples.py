from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
V6_DIR = HERE / "work" / "preview_v6"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def compact(text: str, limit: int = 180) -> str:
    text = " ".join(str(text or "").split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


def relation_samples(label: str, limit: int, skip: int) -> None:
    items = read_json(V6_DIR / "relation_draft.json")["items"]
    rows = [item for item in items if item.get("draft_label") == label]
    print(f"label={label} total={len(rows)} skip={skip} limit={limit}")
    for item in rows[skip : skip + limit]:
        print()
        print(f"--- {item['pair_id']} score={item.get('score')} confidence={item.get('draft_confidence')}")
        print(f"candidate_type={item.get('candidate_type')}")
        print(f"reasons={','.join(item.get('reasons') or [])}")
        print(f"flags={','.join(item.get('draft_risk_flags') or [])}")
        a = item["card_a"]
        b = item["card_b"]
        print(f"A[{a['card_id']}] q={a.get('question_count')} {compact(a.get('quote'))}")
        print(f"B[{b['card_id']}] q={b.get('question_count')} {compact(b.get('quote'))}")
        print(f"why={item.get('draft_rationale')}")


def relation_pair(pair_id: str) -> None:
    items = read_json(V6_DIR / "relation_draft.json")["items"]
    for item in items:
        if item.get("pair_id") != pair_id:
            continue
        print(f"--- {item['pair_id']} label={item.get('draft_label')} score={item.get('score')} confidence={item.get('draft_confidence')}")
        print(f"candidate_type={item.get('candidate_type')}")
        print(f"reasons={','.join(item.get('reasons') or [])}")
        print(f"flags={','.join(item.get('draft_risk_flags') or [])}")
        a = item["card_a"]
        b = item["card_b"]
        print(f"A title={a.get('title_placeholder')}")
        print(f"A quote={a.get('quote')}")
        print(f"B title={b.get('title_placeholder')}")
        print(f"B quote={b.get('quote')}")
        print(f"why={item.get('draft_rationale')}")
        return
    print(f"pair not found: {pair_id}")


def relation_risks(limit: int, skip: int) -> None:
    items = read_json(V6_DIR / "dry_run_20260630_mid" / "relation_risks.json")["items"]
    print(f"relation_risks total={len(items)} skip={skip} limit={limit}")
    for item in items[skip : skip + limit]:
        print()
        print(f"--- {item['pair_id']} label={item.get('draft_label')} score={item.get('score')}")
        print(f"risks={','.join(item.get('risks') or [])}")
        print(f"A[{item.get('card_a')}] {compact(item.get('card_a_text'))}")
        print(f"B[{item.get('card_b')}] {compact(item.get('card_b_text'))}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="parent_child")
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--skip", type=int, default=0)
    parser.add_argument("--pair")
    parser.add_argument("--risks", action="store_true")
    args = parser.parse_args()

    if args.pair:
        relation_pair(args.pair)
    elif args.risks:
        relation_risks(args.limit, args.skip)
    else:
        relation_samples(args.label, args.limit, args.skip)


if __name__ == "__main__":
    main()
