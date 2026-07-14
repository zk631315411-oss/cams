from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


PHASE_DIR = Path(__file__).resolve().parents[4]
SCRIPTS_DIR = PHASE_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from generate_p7c_drawio_flow_readable import PageBuilder, draw_card  # noqa: E402
from generate_p7c_drawio_review import make_section_page  # noqa: E402
from p7_edge_runtime import (  # noqa: E402
    build_proof_adjacency,
    find_proof_paths,
    node_render_kind,
    node_role,
    render_edge_endpoints,
    render_edge_label,
    section_summary_rows,
)


def sample_card() -> dict:
    return {
        "card_id": "p7card_TEST_001",
        "section_id": "TEST",
        "card_nature": "assessment",
        "title": "持股阈值判断",
        "flow_nodes": [
            {"node_id": "S", "node_category": "auxiliary", "node_type": "standard", "label": "适用阈值"},
            {"node_id": "I", "node_category": "auxiliary", "node_type": "input", "label": "持股信息"},
            {"node_id": "P", "node_category": "process", "node_type": "P1_assessment", "label": "合计持股"},
            {"node_id": "D", "node_category": "process", "node_type": "P3_branch_routing", "label": "比较阈值"},
            {"node_id": "X", "node_category": "exit", "node_type": "X1_classification", "label": "认定为UBO"},
        ],
        "flow_edges": [
            {
                "edge_id": "E_REF_STANDARD",
                "edge_type": "REFERENCES",
                "source": "P",
                "target": "S",
                "relation_type": "standard_constrains_action",
            },
            {
                "edge_id": "E_REF_INPUT",
                "edge_type": "REFERENCES",
                "source": "P",
                "target": "I",
                "relation_type": "clue_supports_identification",
            },
            {"edge_id": "E_PRECEDES", "edge_type": "PRECEDES", "source": "P", "target": "D"},
            {
                "edge_id": "E_DECIDES",
                "edge_type": "DECIDES",
                "source": "D",
                "target": "X",
                "condition": "达到阈值",
            },
            {"edge_id": "E_REJECTED", "edge_type": "PRODUCES", "source": "P", "target": "X"},
        ],
    }


def review(edge_id: str, status: str) -> dict:
    edge = next(row for row in sample_card()["flow_edges"] if row["edge_id"] == edge_id)
    return {
        "card_id": "p7card_TEST_001",
        "edge_id": edge_id,
        "edge_type": edge["edge_type"],
        "source": edge["source"],
        "target": edge["target"],
        "review_status": status,
        "answer_eligible": status == "accepted",
        "retrieval_eligible": status in {"accepted", "pending"},
        "source_edge_snapshot": copy.deepcopy(edge),
    }


def sample_reviews() -> list[dict]:
    return [
        review("E_REF_STANDARD", "accepted"),
        review("E_REF_INPUT", "pending"),
        review("E_PRECEDES", "accepted"),
        review("E_DECIDES", "accepted"),
        review("E_REJECTED", "rejected"),
    ]


def vertex_id_by_text(page: PageBuilder, needle: str) -> str:
    for cell in page.root.findall("mxCell"):
        if cell.get("vertex") == "1" and needle in str(cell.get("value") or ""):
            return str(cell.get("id"))
    raise AssertionError(f"Vertex not found: {needle}")


def edge_by_label(page: PageBuilder, needle: str):
    for cell in page.root.findall("mxCell"):
        if cell.get("edge") == "1" and needle in str(cell.get("value") or ""):
            return cell
    raise AssertionError(f"Edge not found: {needle}")


class RuntimePolicyTests(unittest.TestCase):
    def test_schema_declares_reference_runtime_policy(self) -> None:
        schema = json.loads((PHASE_DIR / "inputs" / "procedural_schema_v2.json").read_text(encoding="utf-8-sig"))
        policy = schema["edge_runtime_policies"]["REFERENCES"]
        self.assertEqual(policy["storage_direction"], "process_to_auxiliary")
        self.assertEqual(policy["render_direction"], "auxiliary_to_process")
        self.assertEqual(policy["reasoning_traversal"], "bidirectional")
        self.assertFalse(policy["causal"])
        self.assertFalse(policy["temporal"])
        self.assertEqual(
            set(schema["edge_runtime_policies"]),
            {"PRECEDES", "REFERENCES", "PRODUCES", "DECIDES", "FEEDBACK"},
        )

    def test_current_node_categories_drive_render_roles(self) -> None:
        nodes = {node["node_id"]: node for node in sample_card()["flow_nodes"]}
        self.assertEqual(node_role(nodes["P"]), "process")
        self.assertEqual(node_render_kind(nodes["P"]), "action")
        self.assertEqual(node_render_kind(nodes["D"]), "decision")
        self.assertEqual(node_render_kind(nodes["X"]), "output")
        self.assertEqual(node_role(nodes["S"]), "auxiliary")

    def test_current_run_summary_object_is_supported(self) -> None:
        payload = {
            "arm": "variant",
            "sections": ["CH06-S10"],
            "manifests": [{"section_id": "CH06-S10", "status": "ok"}],
        }
        self.assertEqual(section_summary_rows(payload), payload["manifests"])

    def test_reference_rendering_reverses_only_the_derived_view(self) -> None:
        card = sample_card()
        before = copy.deepcopy(card)
        nodes = {node["node_id"]: node for node in card["flow_nodes"]}
        reference = card["flow_edges"][0]
        precedes = card["flow_edges"][2]
        self.assertEqual(render_edge_endpoints(reference), ("S", "P"))
        self.assertEqual(render_edge_endpoints(precedes), ("P", "D"))
        self.assertEqual(render_edge_label(reference, nodes), "作为判定标准或规范依据")
        self.assertEqual(card, before)

    def test_both_drawio_renderers_show_standard_to_process(self) -> None:
        card = sample_card()
        readable = PageBuilder("test")
        draw_card(readable, card, 1, 20)
        readable_reference = edge_by_label(readable, "作为判定标准或规范依据")
        self.assertEqual(readable_reference.get("source"), vertex_id_by_text(readable, "适用阈值"))
        self.assertEqual(readable_reference.get("target"), vertex_id_by_text(readable, "合计持股"))

        section = {
            "section_id": "TEST",
            "section_title": "test",
            "status": "ok",
            "validation_error_count": 0,
            "cards": [card],
            "skip_reason": "",
        }
        review_page = make_section_page(section)
        review_reference = edge_by_label(review_page, "作为判定标准或规范依据")
        self.assertEqual(review_reference.get("source"), vertex_id_by_text(review_page, "适用阈值"))
        self.assertEqual(review_reference.get("target"), vertex_id_by_text(review_page, "合计持股"))


class ProofTraversalTests(unittest.TestCase):
    def test_final_path_uses_reverse_reference_and_requires_condition(self) -> None:
        adjacency = build_proof_adjacency(sample_card(), sample_reviews(), mode="final")
        self.assertEqual(adjacency["S"][0]["traversal_direction"], "reverse")
        self.assertFalse(adjacency["S"][0]["causal"])
        self.assertFalse(adjacency["S"][0]["temporal"])
        self.assertNotIn("I", adjacency)

        without_condition = find_proof_paths(
            adjacency, "S", "X", require_result_edge=True
        )
        self.assertEqual(without_condition, [])

        paths = find_proof_paths(
            adjacency,
            "S",
            "X",
            satisfied_conditions=["达到阈值"],
            require_result_edge=True,
        )
        self.assertEqual(len(paths), 1)
        self.assertEqual(
            [step["edge_type"] for step in paths[0]],
            ["REFERENCES", "PRECEDES", "DECIDES"],
        )
        self.assertEqual(paths[0][0]["traversal_direction"], "reverse")
        self.assertEqual(paths[0][-1]["condition"], "达到阈值")

    def test_pending_reference_is_retrieval_only(self) -> None:
        final = build_proof_adjacency(sample_card(), sample_reviews(), mode="final")
        retrieval = build_proof_adjacency(sample_card(), sample_reviews(), mode="retrieval")
        self.assertNotIn("I", final)
        self.assertEqual(retrieval["I"][0]["review_status"], "pending")
        self.assertFalse(retrieval["I"][0]["answer_eligible"])
        paths = find_proof_paths(
            retrieval,
            "I",
            "X",
            satisfied_conditions=["达到阈值"],
            require_result_edge=True,
        )
        self.assertEqual(len(paths), 1)

    def test_rejected_and_unreviewed_edges_are_not_traversable(self) -> None:
        adjacency = build_proof_adjacency(sample_card(), sample_reviews(), mode="retrieval")
        edge_ids = {
            step["edge_id"]
            for steps in adjacency.values()
            for step in steps
        }
        self.assertNotIn("E_REJECTED", edge_ids)

        reviews = [row for row in sample_reviews() if row["edge_id"] != "E_PRECEDES"]
        adjacency = build_proof_adjacency(sample_card(), reviews, mode="final")
        paths = find_proof_paths(
            adjacency,
            "S",
            "X",
            satisfied_conditions=["达到阈值"],
            require_result_edge=True,
        )
        self.assertEqual(paths, [])

    def test_reused_edge_id_with_changed_snapshot_is_unreviewed(self) -> None:
        card = sample_card()
        changed_edge = next(edge for edge in card["flow_edges"] if edge["edge_id"] == "E_PRECEDES")
        changed_edge["target"] = "X"
        adjacency = build_proof_adjacency(card, sample_reviews(), mode="final")
        steps = [step for rows in adjacency.values() for step in rows]
        self.assertNotIn("E_PRECEDES", {step["edge_id"] for step in steps})

    def test_review_without_source_snapshot_is_unreviewed(self) -> None:
        reviews = sample_reviews()
        reviews[0].pop("source_edge_snapshot")
        adjacency = build_proof_adjacency(sample_card(), reviews, mode="final")
        self.assertNotIn("S", adjacency)

    def test_condition_on_any_edge_is_a_traversal_gate(self) -> None:
        adjacency = {
            "S": [
                {
                    "edge_id": "E_CONDITIONAL_REFERENCE",
                    "edge_type": "REFERENCES",
                    "source": "S",
                    "target": "P",
                    "condition": "客户为高风险",
                }
            ]
        }
        self.assertEqual(find_proof_paths(adjacency, "S", "P"), [])
        self.assertEqual(
            len(find_proof_paths(adjacency, "S", "P", satisfied_conditions=["客户为高风险"])),
            1,
        )


if __name__ == "__main__":
    unittest.main()
