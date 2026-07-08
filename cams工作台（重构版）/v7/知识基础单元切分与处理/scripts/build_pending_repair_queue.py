from __future__ import annotations

import argparse
import importlib.util
import json
from datetime import datetime
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
MODULE_DIR = SCRIPT_DIR.parent
V7_DIR = MODULE_DIR.parent
BASE_UNITS_DIR = V7_DIR / "work" / "base_units"
REPAIR_DIR = BASE_UNITS_DIR / "repairs"
OUT_DIR = BASE_UNITS_DIR / "repair_queue"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_approved_join_pairs() -> set[tuple[str, str]]:
    repair_script = SCRIPT_DIR / "apply_reviewed_repairs.py"
    spec = importlib.util.spec_from_file_location("apply_reviewed_repairs", repair_script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {repair_script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return {
        (str(join["left_block_id"]), str(join["right_block_id"]))
        for join in getattr(module, "APPROVED_SENTENCE_JOINS", [])
    }


def route_lookup() -> dict[str, dict]:
    route_file = BASE_UNITS_DIR / "fullbook_dry_run" / "v7_fullbook_routing_dry_run.json"
    if not route_file.exists():
        return {}
    payload = read_json(route_file)
    return {str(row.get("block_id")): row for row in payload.get("items", [])}


def build_queue(min_confidence: str | None = None) -> dict:
    suggestions = read_json(REPAIR_DIR / "block_repair_suggestions.json")
    approved = load_approved_join_pairs()
    routes = route_lookup()

    rows = []
    for item in suggestions.get("cross_block_joins", []):
        left = str(item.get("left_block_id"))
        right = str(item.get("right_block_id"))
        approved_status = (left, right) in approved
        confidence = str(item.get("confidence") or "")
        if min_confidence and confidence != min_confidence:
            continue
        if approved_status:
            continue
        left_route = routes.get(left, {})
        right_route = routes.get(right, {})
        rows.append(
            {
                "left_block_id": left,
                "right_block_id": right,
                "confidence": confidence,
                "suggested_join_scope": item.get("suggested_join_scope"),
                "left_printed_page": item.get("left_printed_page"),
                "right_printed_page": item.get("right_printed_page"),
                "left_route": left_route.get("route"),
                "right_route": right_route.get("route"),
                "left_evidence_status": left_route.get("evidence_status"),
                "right_evidence_status": right_route.get("evidence_status"),
                "reason": item.get("reason"),
                "joined_sample": item.get("joined_sample"),
            }
        )

    return {
        "schema_version": "v7_pending_repair_queue_v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source": "repairs/block_repair_suggestions.json",
        "approved_sentence_joins": len(approved),
        "pending_cross_block_joins": len(rows),
        "items": rows,
    }


def build_report(payload: dict, limit: int = 80) -> str:
    lines = [
        "# v7 Pending Repair Queue",
        "",
        f"Generated at: {payload['generated_at']}",
        "",
        f"- approved sentence joins: {payload['approved_sentence_joins']}",
        f"- pending cross-block joins: {payload['pending_cross_block_joins']}",
        "",
        "## Pending Examples",
        "",
    ]
    for item in payload["items"][:limit]:
        lines.extend(
            [
                f"### {item['left_block_id']} -> {item['right_block_id']}",
                "",
                f"- confidence: {item.get('confidence')}",
                f"- pages: {item.get('left_printed_page')} -> {item.get('right_printed_page')}",
                f"- routes: {item.get('left_route')} -> {item.get('right_route')}",
                f"- evidence_status: {item.get('left_evidence_status')} -> {item.get('right_evidence_status')}",
                f"- reason: {item.get('reason')}",
                f"- sample: {item.get('joined_sample')}",
                "",
            ]
        )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-confidence", choices=["high", "medium", "low"])
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = build_queue(args.min_confidence)
    out_json = args.out_dir / "pending_repair_queue.json"
    out_report = args.out_dir / "pending_repair_queue_report.md"
    write_json(out_json, payload)
    out_report.parent.mkdir(parents=True, exist_ok=True)
    out_report.write_text(build_report(payload), encoding="utf-8")
    print(f"pending cross-block joins: {payload['pending_cross_block_joins']}")
    print(f"wrote: {out_json}")
    print(f"wrote: {out_report}")


if __name__ == "__main__":
    main()
