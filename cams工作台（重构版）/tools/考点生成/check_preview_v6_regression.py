from __future__ import annotations

import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
V6_DIR = HERE / "work" / "preview_v6"


EXPECTED_RELATIONS = {
    "v6s_N02786__v6s_N02787": "sibling_under_parent",
    "v6s_N02174__v6s_N02176": "sibling_under_parent",
    "v6s_N02777__v6s_N02778": "parent_child",
    "v6s_N00139__v6s_N00141": "parent_child",
    "v6s_N01302__v6s_N01303": "parent_child",
    "v6s_N00302__v6s_N00309": "sibling_under_parent",
    "v6s_N00134__v6s_N03753": "keep_separate",
    "v6s_N01497__v6s_N02832": "keep_separate",
    "v6s_N01824__v6s_N01825": "parent_child",
    "v6s_N02794__v6s_N02795": "parent_child",
    "v6s_N02217__v6s_N02240": "merge_same_point",
    "v6s_N02728__v6s_N02731": "parent_child",
    "v6s_N02766__v6s_N02767": "parent_child",
}

OPTIONAL_EXPECTED_RELATIONS = {
    "v6s_N02176__v6s_N02178": "merge_same_point",
    "v6s_N02174__v6s_N02178": "keep_separate",
    "v6s_N01177__v6s_N02174": "keep_separate",
    "v6s_N01945__v6s_N02174": "keep_separate",
    "v6s_N02174__v6s_N02694": "keep_separate",
    "v6s_N02178__v6s_N02468": "keep_separate",
}

EXPECTED_CONTRAST_ACTIONS = {
    "2.1_16::C::v6s_N00134::contrast": "count_in_exam_point",
    "2.1_16::C::v6s_N00165::contrast": "hold_for_review",
    "2.1_31::C::v6s_N03652::contrast": "hold_for_review",
    "2.1_31::C::v6s_N04907::contrast": "hold_for_review",
    "2.1_37::A::v6s_N00784::contrast": "hold_for_review",
    "2.1_49::D::v6s_N00443::contrast": "count_in_exam_point",
    "5.2_9::D::v6s_N04589::contrast": "hold_for_review",
    "5.1_27::D::v6s_N04508::contrast": "hold_for_review",
    "3.6_41::A::v6s_N02781::contrast": "hold_for_review",
    "5.2_21::C::v6s_N03460::contrast": "hold_for_review",
    "3.6_50::C::v6s_N02693::contrast": "hold_for_review",
    "4.1_28::B::v6s_N02070::contrast": "count_in_exam_point",
    "4.2_47::C::v6s_N02252::contrast": "count_in_exam_point",
    "4.3_3::D::v6s_N02228::contrast": "hold_for_review",
    "4.5_22::C::v6s_N04041::contrast": "count_in_exam_point",
    "4.2_18::A::v6s_N03266::contrast": "count_in_exam_point",
    "3.6_52::D::v6s_N02334::contrast": "count_in_exam_point",
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    relation_items = read_json(V6_DIR / "relation_draft.json")["items"]
    contrast_items = read_json(V6_DIR / "contrast_draft.json")["items"]
    relation_by_id = {item["pair_id"]: item for item in relation_items}
    contrast_by_id = {item["edge_key"]: item for item in contrast_items}

    failures = []
    for pair_id, expected in EXPECTED_RELATIONS.items():
        actual = relation_by_id.get(pair_id, {}).get("draft_label")
        if actual != expected:
            failures.append(f"relation {pair_id}: expected {expected}, got {actual}")

    optional_checked = 0
    for pair_id, expected in OPTIONAL_EXPECTED_RELATIONS.items():
        if pair_id not in relation_by_id:
            continue
        optional_checked += 1
        actual = relation_by_id[pair_id].get("draft_label")
        if actual != expected:
            failures.append(f"optional relation {pair_id}: expected {expected}, got {actual}")

    for edge_key, expected in EXPECTED_CONTRAST_ACTIONS.items():
        actual = contrast_by_id.get(edge_key, {}).get("draft_action")
        if actual != expected:
            failures.append(f"contrast {edge_key}: expected {expected}, got {actual}")

    if failures:
        print("Preview v6 regression check failed:")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)

    print("Preview v6 regression check passed.")
    print(f"- relation cases: {len(EXPECTED_RELATIONS)}")
    print(f"- optional relation cases checked: {optional_checked}")
    print(f"- contrast cases: {len(EXPECTED_CONTRAST_ACTIONS)}")


if __name__ == "__main__":
    main()
