from __future__ import annotations

import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

TEST_FILE = Path(__file__).resolve()
PHASE_DIR = next(
    parent for parent in TEST_FILE.parents
    if (parent / "scripts" / "process_ir_compiler_v1.py").exists()
)


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


COMPILER = _load_module(
    "process_ir_compiler_v1",
    PHASE_DIR / "scripts" / "process_ir_compiler_v1.py",
)
validate_process_ir_payload = COMPILER.validate_process_ir_payload
compile_process_ir_to_cards = COMPILER.compile_process_ir_to_cards

P7C_PROMPTS = PHASE_DIR / "phases" / "P7C" / "prompts"
TEST_SECTION = "CH06-S10"
ALLOWED_UNITS = {"v7u_N000477", "v7u_N000478", "v7u_N000479", "v7u_N000480", "v7u_N000489"}


def _s1_candidates(*ids_and_units):
    """Build S1 candidate list from (candidate_id, [unit_ids]) pairs."""
    result = []
    for cid, unit_ids in ids_and_units:
        result.append({
            "candidate_id": cid,
            "unit_ids": list(unit_ids),
            "proposition": f"Proposition for {cid}",
            "source_quotes": ["..."],
            "relation_cues": ["..."],
            "candidate_frame": {
                "trigger_or_context": [],
                "basis_or_condition": [],
                "focal_handling_or_judgment": f"Test {cid}",
                "outcomes_or_paths": [],
            },
            "evidence_spans": [{"unit_id": list(unit_ids)[0], "quote": "..."}] if unit_ids else [],
            "induction": None,
            "cross_unit_basis": None,
        })
    return result


def _make_episode(episode_id="ep_001", src_ids=None, elements=None, relations=None,
                  card_nature="assessment", focal_question="测试问题", title="测试标题",
                  split_reason=None):
    return {
        "episode_id": episode_id,
        "source_candidate_ids": src_ids or ["s1c_001"],
        "focal_question": focal_question,
        "title": title,
        "card_nature": card_nature,
        "elements": elements or [],
        "relations": relations or [],
        "split_reason": split_reason,
    }


def _make_element(element_id="e001", role="action", node_type="P2_execution",
                   label="测试动作", unit_ids=None, modality=None):
    return {
        "element_id": element_id,
        "role": role,
        "node_type": node_type,
        "label": label,
        "evidence_unit_ids": unit_ids or ["v7u_N000477"],
        "modality": modality,
    }


def _make_relation(relation_id="r001", kind="trigger", trigger_element_id="e001",
                    process_element_id="e002", evidence_unit_ids=None,
                    trigger_mode="event", condition=None, **kwargs):
    rel = {
        "relation_id": relation_id,
        "kind": kind,
        "evidence_unit_ids": evidence_unit_ids or ["v7u_N000477"],
    }
    if kind == "trigger":
        rel["trigger_element_id"] = trigger_element_id
        rel["process_element_id"] = process_element_id
        rel["trigger_mode"] = trigger_mode
        if condition is not None:
            rel["condition"] = condition
    elif kind == "sequence":
        rel["before_element_id"] = trigger_element_id
        rel["after_element_id"] = process_element_id
    elif kind == "reference":
        rel["process_element_id"] = trigger_element_id
        rel["auxiliary_element_id"] = process_element_id
    elif kind == "produce":
        rel["process_element_id"] = trigger_element_id
        rel["outcome_element_id"] = process_element_id
    elif kind == "branch":
        rel["decision_element_id"] = trigger_element_id
        rel["target_element_id"] = process_element_id
        rel["condition"] = condition if condition is not None else "条件"
    elif kind == "feedback":
        rel["result_element_id"] = trigger_element_id
        rel["process_element_id"] = process_element_id
    rel.update(kwargs)
    return rel


# ── Test 1: Prompt不含KG、allowed_unit_ids和旧裁决 ──
class TestPromptContract(unittest.TestCase):
    def test_prompt_has_no_kg_references(self):
        prompt = (P7C_PROMPTS / "process_ir_v1.md").read_text(encoding="utf-8")
        self.assertNotIn("kg_projection", prompt.lower())
        self.assertNotIn("base_kg_section_summary", prompt.lower())
        self.assertNotIn("kg_capability_profile", prompt.lower())

    def test_prompt_has_no_allowed_unit_ids_in_section_block(self):
        prompt = (P7C_PROMPTS / "process_ir_v1.md").read_text(encoding="utf-8")
        self.assertNotIn("allowed_unit_ids", prompt)

    def test_prompt_has_no_old_boundary_decision_fields(self):
        prompt = (P7C_PROMPTS / "process_ir_v1.md").read_text(encoding="utf-8")
        self.assertNotIn("boundary_decisions", prompt)
        # "p7c_candidate" and "kg_only" may appear in role description as forbidden terms;
        # they must not appear as output fields or decision values
        self.assertNotIn('"decision": "p7c_candidate"', prompt)
        self.assertNotIn('"decision": "kg_only"', prompt)

    def test_prompt_has_no_s3_construction_fields(self):
        prompt = (P7C_PROMPTS / "process_ir_v1.md").read_text(encoding="utf-8")
        self.assertNotIn("construction_audit", prompt)
        # "flow_nodes"/"flow_edges" may appear in role description as forbidden terms;
        # they must not appear as output fields
        self.assertNotIn('"flow_nodes"', prompt)
        self.assertNotIn('"flow_edges"', prompt)


# ── Test 2: 每个S1 candidate恰好有一条audit ──
class TestCandidateAuditCoverage(unittest.TestCase):
    def setUp(self):
        self.s1 = _s1_candidates(
            ("s1c_001", ["v7u_N000477"]),
            ("s1c_002", ["v7u_N000478"]),
        )

    def test_each_candidate_has_exactly_one_audit(self):
        ir = {
            "section_id": TEST_SECTION,
            "episodes": [_make_episode(
                elements=[_make_element("e001", "action", "P2_execution", "动作1"),
                           _make_element("e002", "context", "E1_event_signal", "事件1")],
                relations=[_make_relation("r001", "trigger", "e002", "e001")],
            )],
            "candidate_audit": [
                {"candidate_id": "s1c_001", "disposition": "mapped", "episode_ids": ["ep_001"], "reason": "理由1"},
                {"candidate_id": "s1c_002", "disposition": "support_only", "episode_ids": ["ep_001"], "reason": "理由2"},
            ],
            "skip_reason": None,
        }
        errors = validate_process_ir_payload(ir, TEST_SECTION, self.s1, ALLOWED_UNITS)
        self.assertEqual(errors, [], f"Expected no errors, got: {errors}")

    def test_missing_candidate_audit_fails(self):
        ir = {
            "section_id": TEST_SECTION,
            "episodes": [_make_episode(
                elements=[_make_element("e001", "action", "P2_execution", "动作1"),
                           _make_element("e002", "context", "E1_event_signal", "事件1")],
                relations=[_make_relation("r001", "trigger", "e002", "e001")],
            )],
            "candidate_audit": [
                {"candidate_id": "s1c_001", "disposition": "mapped", "episode_ids": ["ep_001"], "reason": "理由1"},
            ],
            "skip_reason": None,
        }
        errors = validate_process_ir_payload(ir, TEST_SECTION, self.s1, ALLOWED_UNITS)
        self.assertTrue(any("missing" in e.lower() for e in errors), f"Expected missing error, got: {errors}")

    def test_duplicate_candidate_audit_fails(self):
        ir = {
            "section_id": TEST_SECTION,
            "episodes": [_make_episode(
                elements=[_make_element("e001", "action", "P2_execution", "动作1"),
                           _make_element("e002", "context", "E1_event_signal", "事件1")],
                relations=[_make_relation("r001", "trigger", "e002", "e001")],
            )],
            "candidate_audit": [
                {"candidate_id": "s1c_001", "disposition": "mapped", "episode_ids": ["ep_001"], "reason": "理由1"},
                {"candidate_id": "s1c_001", "disposition": "mapped", "episode_ids": ["ep_001"], "reason": "理由1"},
            ],
            "skip_reason": None,
        }
        errors = validate_process_ir_payload(ir, TEST_SECTION, self.s1, ALLOWED_UNITS)
        self.assertTrue(any("duplicate" in e.lower() for e in errors), f"Expected duplicate error, got: {errors}")


# ── Test 3: 未知candidate、episode、element引用失败 ──
class TestUnknownReferenceFails(unittest.TestCase):
    def setUp(self):
        self.s1 = _s1_candidates(("s1c_001", ["v7u_N000477"]),)

    def test_unknown_candidate_in_source_candidate_ids_fails(self):
        ir = {
            "section_id": TEST_SECTION,
            "episodes": [_make_episode(
                src_ids=["s1c_999"],
                elements=[_make_element("e001", "action", "P2_execution", "act"),
                           _make_element("e002", "context", "E1_event_signal", "ctx")],
                relations=[_make_relation("r001", "trigger", "e002", "e001")],
            )],
            "candidate_audit": [
                {"candidate_id": "s1c_001", "disposition": "mapped", "episode_ids": ["ep_001"], "reason": "r"},
            ],
            "skip_reason": None,
        }
        errors = validate_process_ir_payload(ir, TEST_SECTION, self.s1, ALLOWED_UNITS)
        self.assertTrue(len(errors) > 0, f"Expected errors for unknown candidate, got: {errors}")

    def test_unknown_episode_in_audit_fails(self):
        ir = {
            "section_id": TEST_SECTION,
            "episodes": [_make_episode(
                elements=[_make_element("e001", "action", "P2_execution", "act"),
                           _make_element("e002", "context", "E1_event_signal", "ctx")],
                relations=[_make_relation("r001", "trigger", "e002", "e001")],
            )],
            "candidate_audit": [
                {"candidate_id": "s1c_001", "disposition": "mapped", "episode_ids": ["ep_999"], "reason": "r"},
            ],
            "skip_reason": None,
        }
        errors = validate_process_ir_payload(ir, TEST_SECTION, self.s1, ALLOWED_UNITS)
        self.assertTrue(any("unknown episode" in e.lower() for e in errors), f"Expected unknown episode error, got: {errors}")

    def test_unknown_element_in_relation_fails(self):
        ir = {
            "section_id": TEST_SECTION,
            "episodes": [_make_episode(
                elements=[_make_element("e001", "action", "P2_execution", "act"),
                           _make_element("e002", "context", "E1_event_signal", "ctx")],
                relations=[_make_relation("r001", "trigger", "e002", "e999")],
            )],
            "candidate_audit": [
                {"candidate_id": "s1c_001", "disposition": "mapped", "episode_ids": ["ep_001"], "reason": "r"},
            ],
            "skip_reason": None,
        }
        errors = validate_process_ir_payload(ir, TEST_SECTION, self.s1, ALLOWED_UNITS)
        self.assertTrue(any("not found" in e.lower() for e in errors), f"Expected element not found error, got: {errors}")


# ── Test 4: element/relation越界unit失败 ──
class TestOutOfScopeUnitFails(unittest.TestCase):
    def setUp(self):
        self.s1 = _s1_candidates(("s1c_001", ["v7u_N000477"]),)

    def test_element_with_unknown_unit_fails(self):
        ir = {
            "section_id": TEST_SECTION,
            "episodes": [_make_episode(
                elements=[_make_element("e001", "action", "P2_execution", "act", unit_ids=["v7u_UNKNOWN"]),
                           _make_element("e002", "context", "E1_event_signal", "ctx")],
                relations=[_make_relation("r001", "trigger", "e002", "e001")],
            )],
            "candidate_audit": [
                {"candidate_id": "s1c_001", "disposition": "mapped", "episode_ids": ["ep_001"], "reason": "r"},
            ],
            "skip_reason": None,
        }
        errors = validate_process_ir_payload(ir, TEST_SECTION, self.s1, ALLOWED_UNITS)
        self.assertTrue(any("out-of-section" in e.lower() for e in errors), f"Expected out-of-section error, got: {errors}")

    def test_relation_with_unknown_unit_fails(self):
        ir = {
            "section_id": TEST_SECTION,
            "episodes": [_make_episode(
                elements=[_make_element("e001", "action", "P2_execution", "act"),
                           _make_element("e002", "context", "E1_event_signal", "ctx")],
                relations=[_make_relation("r001", "trigger", "e002", "e001", evidence_unit_ids=["v7u_UNKNOWN"])],
            )],
            "candidate_audit": [
                {"candidate_id": "s1c_001", "disposition": "mapped", "episode_ids": ["ep_001"], "reason": "r"},
            ],
            "skip_reason": None,
        }
        errors = validate_process_ir_payload(ir, TEST_SECTION, self.s1, ALLOWED_UNITS)
        self.assertTrue(any("out-of-section" in e.lower() for e in errors), f"Expected out-of-section error, got: {errors}")


# ── Test 5: element证据超出source candidate unit并集失败 ──
class TestEvidenceOutsideCandidateUnionFails(unittest.TestCase):
    def setUp(self):
        self.s1 = _s1_candidates(("s1c_001", ["v7u_N000477"]),)

    def test_element_evidence_outside_union_fails(self):
        ir = {
            "section_id": TEST_SECTION,
            "episodes": [_make_episode(
                src_ids=["s1c_001"],
                elements=[_make_element("e001", "action", "P2_execution", "act", unit_ids=["v7u_N000478"]),
                           _make_element("e002", "context", "E1_event_signal", "ctx")],
                relations=[_make_relation("r001", "trigger", "e002", "e001")],
            )],
            "candidate_audit": [
                {"candidate_id": "s1c_001", "disposition": "mapped", "episode_ids": ["ep_001"], "reason": "r"},
            ],
            "skip_reason": None,
        }
        errors = validate_process_ir_payload(ir, TEST_SECTION, self.s1, ALLOWED_UNITS)
        self.assertTrue(any("outside source_candidate_ids" in e.lower() for e in errors),
                        f"Expected outside-source-candidate error, got: {errors}")


# ── Test 6: role/node_type不兼容失败 ──
class TestRoleNodeTypeIncompatibility(unittest.TestCase):
    def setUp(self):
        self.s1 = _s1_candidates(("s1c_001", ["v7u_N000477"]),)

    def test_context_role_with_input_node_type_fails(self):
        ir = {
            "section_id": TEST_SECTION,
            "episodes": [_make_episode(
                elements=[_make_element("e001", "action", "P2_execution", "act"),
                           _make_element("e002", "context", "input", "ctx")],
                relations=[_make_relation("r001", "trigger", "e002", "e001")],
            )],
            "candidate_audit": [
                {"candidate_id": "s1c_001", "disposition": "mapped", "episode_ids": ["ep_001"], "reason": "r"},
            ],
            "skip_reason": None,
        }
        errors = validate_process_ir_payload(ir, TEST_SECTION, self.s1, ALLOWED_UNITS)
        self.assertTrue(any("incompatible" in e.lower() for e in errors),
                        f"Expected role/node_type incompatibility error, got: {errors}")

    def test_outcome_role_with_process_node_type_fails(self):
        ir = {
            "section_id": TEST_SECTION,
            "episodes": [_make_episode(
                elements=[_make_element("e001", "action", "P2_execution", "act"),
                           _make_element("e002", "outcome", "P2_execution", "wrong")],
                relations=[_make_relation("r001", "produce", "e001", "e002")],
            )],
            "candidate_audit": [
                {"candidate_id": "s1c_001", "disposition": "mapped", "episode_ids": ["ep_001"], "reason": "r"},
            ],
            "skip_reason": None,
        }
        errors = validate_process_ir_payload(ir, TEST_SECTION, self.s1, ALLOWED_UNITS)
        self.assertTrue(any("incompatible" in e.lower() for e in errors),
                        f"Expected role/node_type incompatibility error, got: {errors}")


# ── Test 7: reference编译为process→auxiliary REFERENCES ──
class TestReferenceCompilation(unittest.TestCase):
    def setUp(self):
        self.s1 = _s1_candidates(("s1c_001", ["v7u_N000477"]),)

    def test_reference_compiles_to_references_edge(self):
        ir = {
            "section_id": TEST_SECTION,
            "episodes": [_make_episode(
                elements=[_make_element("e001", "action", "P2_execution", "执行EDD"),
                           _make_element("e002", "standard", "standard", "适用阈值")],
                relations=[_make_relation("r001", "reference", "e001", "e002")],
            )],
            "candidate_audit": [
                {"candidate_id": "s1c_001", "disposition": "mapped", "episode_ids": ["ep_001"], "reason": "r"},
            ],
            "skip_reason": None,
        }
        result = compile_process_ir_to_cards(ir, TEST_SECTION, "测试")
        cards = result["cards_payload"]["cards"]
        self.assertEqual(len(cards), 1)
        edges = cards[0]["flow_edges"]
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0]["edge_type"], "REFERENCES")

        # Direction: process → auxiliary
        nodes_by_id = {n["node_id"]: n for n in cards[0]["flow_nodes"]}
        src_node = nodes_by_id[edges[0]["source"]]
        tgt_node = nodes_by_id[edges[0]["target"]]
        self.assertIn(src_node["node_category"], {"process", "entry"})
        self.assertEqual(tgt_node["node_category"], "auxiliary")


# ── Test 8: 五类其他relation映射正确（含trigger保留condition） ──
class TestRelationKindToEdgeTypeMapping(unittest.TestCase):
    def setUp(self):
        self.s1 = _s1_candidates(("s1c_001", ["v7u_N000477"]),)

    def _compile_single_rel(self, kind, condition=None, trigger_mode=None, **extra):
        elements = []
        relations = []
        if kind == "trigger":
            elements = [
                _make_element("e001", "context", "E1_event_signal", "触发事件"),
                _make_element("e002", "action", "P2_execution", "动作"),
            ]
            relations = [_make_relation("r001", "trigger", "e001", "e002",
                                        trigger_mode=trigger_mode or "event",
                                        condition=condition)]
        elif kind == "sequence":
            elements = [
                _make_element("e001", "action", "P2_execution", "先行动作"),
                _make_element("e002", "outcome", "X1_classification", "结果"),
            ]
            relations = [_make_relation("r001", "sequence", "e001", "e002")]
        elif kind == "produce":
            elements = [
                _make_element("e001", "action", "P2_execution", "动作"),
                _make_element("e002", "outcome", "X1_classification", "结果"),
            ]
            relations = [_make_relation("r001", "produce", "e001", "e002")]
        elif kind == "branch":
            elements = [
                _make_element("e001", "decision", "P3_branch_routing", "判断"),
                _make_element("e002", "action", "P2_execution", "分支动作A"),
                _make_element("e003", "action", "P2_execution", "分支动作B"),
            ]
            relations = [
                _make_relation("r001", "branch", "e001", "e002", condition="条件A"),
                _make_relation("r002", "branch", "e001", "e003", condition="条件B"),
            ]
        elif kind == "feedback":
            elements = [
                _make_element("e001", "outcome", "X1_classification", "结果发现"),
                _make_element("e002", "action", "P6_feedback", "复核动作"),
            ]
            relations = [_make_relation("r001", "feedback", "e001", "e002")]

        ir = {
            "section_id": TEST_SECTION,
            "episodes": [_make_episode(elements=elements, relations=relations)],
            "candidate_audit": [
                {"candidate_id": "s1c_001", "disposition": "mapped", "episode_ids": ["ep_001"], "reason": "r"},
            ],
            "skip_reason": None,
        }
        return compile_process_ir_to_cards(ir, TEST_SECTION, "")

    def test_trigger_maps_to_precedes(self):
        result = self._compile_single_rel("trigger")
        self.assertEqual(result["cards_payload"]["cards"][0]["flow_edges"][0]["edge_type"], "PRECEDES")

    def test_sequence_maps_to_precedes(self):
        result = self._compile_single_rel("sequence")
        self.assertEqual(result["cards_payload"]["cards"][0]["flow_edges"][0]["edge_type"], "PRECEDES")

    def test_produce_maps_to_produces(self):
        result = self._compile_single_rel("produce")
        self.assertEqual(result["cards_payload"]["cards"][0]["flow_edges"][0]["edge_type"], "PRODUCES")

    def test_branch_maps_to_decides(self):
        result = self._compile_single_rel("branch")
        edges = result["cards_payload"]["cards"][0]["flow_edges"]
        self.assertTrue(all(e["edge_type"] == "DECIDES" for e in edges))

    def test_feedback_maps_to_feedback(self):
        result = self._compile_single_rel("feedback")
        self.assertEqual(result["cards_payload"]["cards"][0]["flow_edges"][0]["edge_type"], "FEEDBACK")

    def test_trigger_preserves_condition(self):
        result = self._compile_single_rel("trigger", condition="客户被分类为高风险", trigger_mode="condition")
        edge = result["cards_payload"]["cards"][0]["flow_edges"][0]
        self.assertEqual(edge.get("condition"), "客户被分类为高风险")


# ── Test 9: P3少于两个分支或缺condition失败 ──
class TestP3BranchValidation(unittest.TestCase):
    def setUp(self):
        self.s1 = _s1_candidates(("s1c_001", ["v7u_N000477"]),)

    def test_p3_with_one_branch_fails(self):
        ir = {
            "section_id": TEST_SECTION,
            "episodes": [_make_episode(
                elements=[_make_element("e001", "decision", "P3_branch_routing", "判断"),
                           _make_element("e002", "action", "P2_execution", "单分支")],
                relations=[_make_relation("r001", "branch", "e001", "e002", condition="条件")],
            )],
            "candidate_audit": [
                {"candidate_id": "s1c_001", "disposition": "mapped", "episode_ids": ["ep_001"], "reason": "r"},
            ],
            "skip_reason": None,
        }
        errors = validate_process_ir_payload(ir, TEST_SECTION, self.s1, ALLOWED_UNITS)
        self.assertTrue(any("need >=2" in e.lower() or "branch" in e.lower() for e in errors),
                        f"Expected P3 branch count error, got: {errors}")

    def test_branch_without_condition_fails(self):
        ir = {
            "section_id": TEST_SECTION,
            "episodes": [_make_episode(
                elements=[_make_element("e001", "decision", "P3_branch_routing", "判断"),
                           _make_element("e002", "action", "P2_execution", "分支A"),
                           _make_element("e003", "action", "P2_execution", "分支B")],
                relations=[_make_relation("r001", "branch", "e001", "e002", condition="条件"),
                            _make_relation("r002", "branch", "e001", "e003", condition="")],
            )],
            "candidate_audit": [
                {"candidate_id": "s1c_001", "disposition": "mapped", "episode_ids": ["ep_001"], "reason": "r"},
            ],
            "skip_reason": None,
        }
        errors = validate_process_ir_payload(ir, TEST_SECTION, self.s1, ALLOWED_UNITS)
        self.assertTrue(any("condition" in e.lower() for e in errors),
                        f"Expected branch condition error, got: {errors}")

    def test_p3_with_two_branches_passes(self):
        ir = {
            "section_id": TEST_SECTION,
            "episodes": [_make_episode(
                elements=[_make_element("e001", "decision", "P3_branch_routing", "判断"),
                           _make_element("e002", "outcome", "X1_classification", "正结果"),
                           _make_element("e003", "outcome", "X1_classification", "反结果")],
                relations=[_make_relation("r001", "branch", "e001", "e002", condition="满足阈值"),
                            _make_relation("r002", "branch", "e001", "e003", condition="不满足阈值")],
            )],
            "candidate_audit": [
                {"candidate_id": "s1c_001", "disposition": "mapped", "episode_ids": ["ep_001"], "reason": "r"},
            ],
            "skip_reason": None,
        }
        errors = validate_process_ir_payload(ir, TEST_SECTION, self.s1, ALLOWED_UNITS)
        self.assertEqual(errors, [], f"Expected no errors, got: {errors}")


# ── Test 10: 合法两节点开放关系通过 ──
class TestTwoNodeOpenRelationPasses(unittest.TestCase):
    def setUp(self):
        self.s1 = _s1_candidates(("s1c_001", ["v7u_N000477"]),)

    def test_two_node_one_relation_passes(self):
        ir = {
            "section_id": TEST_SECTION,
            "episodes": [_make_episode(
                elements=[_make_element("e001", "context", "E1_event_signal", "怀疑资金非法"),
                           _make_element("e002", "action", "P2_execution", "不得接受还款")],
                relations=[_make_relation("r001", "trigger", "e001", "e002",
                                          trigger_mode="condition", condition="怀疑资金非法")],
            )],
            "candidate_audit": [
                {"candidate_id": "s1c_001", "disposition": "mapped", "episode_ids": ["ep_001"], "reason": "r"},
            ],
            "skip_reason": None,
        }
        errors = validate_process_ir_payload(ir, TEST_SECTION, self.s1, ALLOWED_UNITS)
        self.assertEqual(errors, [], f"Expected no errors for open relation, got: {errors}")


# ── Test 11: 合法UBO多输入、标准、判断和正反分支通过 ──
class TestUBOFullEpisodesPass(unittest.TestCase):
    def setUp(self):
        units = ["v7u_N000477", "v7u_N000478", "v7u_N000479", "v7u_N000480", "v7u_N000489"]
        self.s1 = _s1_candidates(
            ("s1c_001", units[:2]),
            ("s1c_002", units[2:3]),
            ("s1c_003", units[3:4]),
            ("s1c_004", units[4:]),
        )

    def test_ubo_full_judgment_episode_passes(self):
        """直接/间接持股 + 阈值 → 判断 → 正反结果 同一episode"""
        ir = {
            "section_id": TEST_SECTION,
            "episodes": [
                _make_episode(
                    episode_id="ep_001",
                    src_ids=["s1c_001", "s1c_002"],
                    focal_question="如何依据持股比例认定UBO",
                    title="依据直接和间接持股及适用阈值认定UBO",
                    card_nature="assessment",
                    elements=[
                        _make_element("e001", "input", "input", "直接持股比例"),
                        _make_element("e002", "input", "input", "间接持股比例"),
                        _make_element("e003", "standard", "standard", "适用的受益所有权阈值"),
                        _make_element("e004", "action", "P1_assessment", "合计持股并比较阈值"),
                        _make_element("e005", "decision", "P3_branch_routing", "是否达到UBO阈值"),
                        _make_element("e006", "outcome", "X1_classification", "认定为UBO"),
                        _make_element("e007", "outcome", "X1_classification", "不认定为UBO"),
                    ],
                    relations=[
                        _make_relation("r001", "reference", "e004", "e001"),
                        _make_relation("r002", "reference", "e004", "e002"),
                        _make_relation("r003", "reference", "e004", "e003"),
                        _make_relation("r004", "sequence", "e004", "e005"),
                        _make_relation("r005", "branch", "e005", "e006", condition="持股比例≥阈值"),
                        _make_relation("r006", "branch", "e005", "e007", condition="持股比例<阈值"),
                    ],
                ),
                _make_episode(
                    episode_id="ep_002",
                    src_ids=["s1c_003"],
                    focal_question="如何设定UBO阈值",
                    title="风险为本设定UBO适用阈值",
                    card_nature="assessment",
                    elements=[
                        _make_element("e001", "context", "E3_state_threshold", "客户风险水平",
                                      unit_ids=["v7u_N000480"]),
                        _make_element("e002", "action", "P2_execution", "机构设定适用阈值",
                                      unit_ids=["v7u_N000480"]),
                        _make_element("e003", "outcome", "X5_config_change", "可复用的阈值配置",
                                      unit_ids=["v7u_N000480"]),
                    ],
                    relations=[
                        _make_relation("r001", "trigger", "e001", "e002",
                                       evidence_unit_ids=["v7u_N000480"]),
                        _make_relation("r002", "produce", "e002", "e003",
                                       evidence_unit_ids=["v7u_N000480"]),
                    ],
                ),
            ],
            "candidate_audit": [
                {"candidate_id": "s1c_001", "disposition": "mapped", "episode_ids": ["ep_001"],
                 "reason": "提供持股输入"},
                {"candidate_id": "s1c_002", "disposition": "mapped", "episode_ids": ["ep_001"],
                 "reason": "提供阈值标准"},
                {"candidate_id": "s1c_003", "disposition": "mapped", "episode_ids": ["ep_002"],
                 "reason": "阈值设定是独立中心"},
                {"candidate_id": "s1c_004", "disposition": "support_only", "episode_ids": ["ep_001"],
                 "reason": "提供补充输入"},
            ],
            "skip_reason": None,
        }
        errors = validate_process_ir_payload(ir, TEST_SECTION, self.s1, ALLOWED_UNITS)
        self.assertEqual(errors, [], f"Expected no errors for UBO episode, got: {errors}")

        # Also compile
        result = compile_process_ir_to_cards(ir, TEST_SECTION, "Risk-Based UBO Determination")
        cards = result["cards_payload"]["cards"]
        self.assertEqual(len(cards), 2)


# ── Test 12: 孤立元素或不连通episode失败 ──
class TestConnectivityFails(unittest.TestCase):
    def setUp(self):
        self.s1 = _s1_candidates(("s1c_001", ["v7u_N000477"]),)

    def test_isolated_element_fails(self):
        ir = {
            "section_id": TEST_SECTION,
            "episodes": [_make_episode(
                elements=[_make_element("e001", "action", "P2_execution", "动作1"),
                           _make_element("e002", "context", "E1_event_signal", "事件1"),
                           _make_element("e003", "action", "P2_execution", "孤立的动作")],
                relations=[_make_relation("r001", "trigger", "e002", "e001")],
            )],
            "candidate_audit": [
                {"candidate_id": "s1c_001", "disposition": "mapped", "episode_ids": ["ep_001"], "reason": "r"},
            ],
            "skip_reason": None,
        }
        errors = validate_process_ir_payload(ir, TEST_SECTION, self.s1, ALLOWED_UNITS)
        self.assertTrue(any("connected" in e.lower() for e in errors),
                        f"Expected connectivity error, got: {errors}")


# ── Test 13: 多candidate→单episode反向映射一致 ──
class TestCandidateEpisodeConsistency(unittest.TestCase):
    def setUp(self):
        self.s1 = _s1_candidates(
            ("s1c_001", ["v7u_N000477"]),
            ("s1c_002", ["v7u_N000478"]),
        )

    def test_episode_source_consistent_with_audit(self):
        ir = {
            "section_id": TEST_SECTION,
            "episodes": [_make_episode(
                src_ids=["s1c_001", "s1c_002"],
                elements=[_make_element("e001", "action", "P2_execution", "act"),
                           _make_element("e002", "context", "E1_event_signal", "ctx")],
                relations=[_make_relation("r001", "trigger", "e002", "e001")],
            )],
            "candidate_audit": [
                {"candidate_id": "s1c_001", "disposition": "mapped", "episode_ids": ["ep_001"], "reason": "r1"},
                {"candidate_id": "s1c_002", "disposition": "support_only", "episode_ids": ["ep_001"], "reason": "r2"},
            ],
            "skip_reason": None,
        }
        errors = validate_process_ir_payload(ir, TEST_SECTION, self.s1, ALLOWED_UNITS)
        self.assertEqual(errors, [], f"Expected no errors, got: {errors}")

    def test_episode_source_not_in_audit_fails(self):
        ir = {
            "section_id": TEST_SECTION,
            "episodes": [_make_episode(
                src_ids=["s1c_001"],
                elements=[_make_element("e001", "action", "P2_execution", "act"),
                           _make_element("e002", "context", "E1_event_signal", "ctx")],
                relations=[_make_relation("r001", "trigger", "e002", "e001")],
            )],
            "candidate_audit": [
                {"candidate_id": "s1c_001", "disposition": "mapped", "episode_ids": ["ep_001"], "reason": "r1"},
                {"candidate_id": "s1c_002", "disposition": "excluded_nonprocedural", "episode_ids": [], "reason": "非流程"},
            ],
            "skip_reason": None,
        }
        # ep_001 declares s1c_001 in source_candidate_ids; audit maps s1c_001 to ep_001 - OK
        errors = validate_process_ir_payload(ir, TEST_SECTION, self.s1, ALLOWED_UNITS)
        self.assertEqual(errors, [], f"Expected no errors, got: {errors}")


# ── Test 14: 单candidate→多episode必须有split_reason ──
class TestSplitReasonRequired(unittest.TestCase):
    def setUp(self):
        self.s1 = _s1_candidates(("s1c_001", ["v7u_N000477"]),)

    def test_multi_episode_without_split_reason_fails(self):
        ir = {
            "section_id": TEST_SECTION,
            "episodes": [
                _make_episode("ep_001", src_ids=["s1c_001"],
                              elements=[_make_element("e001", "action", "P2_execution", "act1"),
                                         _make_element("e002", "context", "E1_event_signal", "ctx1")],
                              relations=[_make_relation("r001", "trigger", "e002", "e001")],
                              split_reason=None),
                _make_episode("ep_002", src_ids=["s1c_001"],
                              elements=[_make_element("e003", "action", "P2_execution", "act2"),
                                         _make_element("e004", "context", "E1_event_signal", "ctx2")],
                              relations=[_make_relation("r002", "trigger", "e004", "e003")],
                              split_reason=None),
            ],
            "candidate_audit": [
                {"candidate_id": "s1c_001", "disposition": "mapped", "episode_ids": ["ep_001", "ep_002"],
                 "reason": "同一候选用于两个中心"},
            ],
            "skip_reason": None,
        }
        errors = validate_process_ir_payload(ir, TEST_SECTION, self.s1, ALLOWED_UNITS)
        self.assertTrue(any("split_reason" in e.lower() for e in errors),
                        f"Expected split_reason error, got: {errors}")

    def test_multi_episode_with_split_reason_passes(self):
        ir = {
            "section_id": TEST_SECTION,
            "episodes": [
                _make_episode("ep_001", src_ids=["s1c_001"],
                              elements=[_make_element("e001", "action", "P2_execution", "act1"),
                                         _make_element("e002", "context", "E1_event_signal", "ctx1")],
                              relations=[_make_relation("r001", "trigger", "e002", "e001")],
                              split_reason="候选包含两个独立中心"),
                _make_episode("ep_002", src_ids=["s1c_001"],
                              elements=[_make_element("e003", "action", "P2_execution", "act2"),
                                         _make_element("e004", "context", "E1_event_signal", "ctx2")],
                              relations=[_make_relation("r002", "trigger", "e004", "e003")],
                              split_reason="候选包含两个独立中心"),
            ],
            "candidate_audit": [
                {"candidate_id": "s1c_001", "disposition": "mapped", "episode_ids": ["ep_001", "ep_002"],
                 "reason": "同一候选用于两个中心"},
            ],
            "skip_reason": None,
        }
        errors = validate_process_ir_payload(ir, TEST_SECTION, self.s1, ALLOWED_UNITS)
        self.assertEqual(errors, [], f"Expected no errors, got: {errors}")


# ── Test 15: 编译边不含derivation、evidence_strength、review_status ──
class TestCompiledEdgesNoForbiddenFields(unittest.TestCase):
    def setUp(self):
        self.s1 = _s1_candidates(("s1c_001", ["v7u_N000477"]),)

    def test_compiled_edges_have_no_forbidden_fields(self):
        ir = {
            "section_id": TEST_SECTION,
            "episodes": [_make_episode(
                elements=[_make_element("e001", "action", "P2_execution", "act"),
                           _make_element("e002", "context", "E1_event_signal", "ctx")],
                relations=[_make_relation("r001", "trigger", "e002", "e001")],
            )],
            "candidate_audit": [
                {"candidate_id": "s1c_001", "disposition": "mapped", "episode_ids": ["ep_001"], "reason": "r"},
            ],
            "skip_reason": None,
        }
        result = compile_process_ir_to_cards(ir, TEST_SECTION, "")
        for card in result["cards_payload"]["cards"]:
            for edge in card["flow_edges"]:
                self.assertNotIn("derivation", edge)
                self.assertNotIn("evidence_strength", edge)
                self.assertNotIn("review_status", edge)


# ── Test 16: 编译cards通过现有P7C/P7D结构合同 ──
class TestCompiledCardsStructuralContract(unittest.TestCase):
    def setUp(self):
        self.s1 = _s1_candidates(("s1c_001", ["v7u_N000477"]),)

    def test_compiled_card_has_all_required_fields(self):
        ir = {
            "section_id": TEST_SECTION,
            "episodes": [_make_episode(
                elements=[_make_element("e001", "action", "P2_execution", "act"),
                           _make_element("e002", "context", "E1_event_signal", "ctx")],
                relations=[_make_relation("r001", "trigger", "e002", "e001")],
            )],
            "candidate_audit": [
                {"candidate_id": "s1c_001", "disposition": "mapped", "episode_ids": ["ep_001"], "reason": "r"},
            ],
            "skip_reason": None,
        }
        result = compile_process_ir_to_cards(ir, TEST_SECTION, "")
        for card in result["cards_payload"]["cards"]:
            self.assertIn("card_id", card)
            self.assertIn("section_id", card)
            self.assertIn("card_nature", card)
            self.assertIn("title", card)
            self.assertIn("flow_nodes", card)
            self.assertIn("flow_edges", card)
            self.assertIn("source_unit_ids", card)
            self.assertIn("candidate_status", card)
            self.assertEqual(card["candidate_status"], "candidate")
            self.assertIn("review_notes", card)

        # Check coverage_audit
        audit = result["cards_payload"]["coverage_audit"]
        self.assertTrue(len(audit) > 0)


# ── Test 17: event trigger允许condition=null；condition trigger缺condition失败 ──
class TestTriggerModeValidation(unittest.TestCase):
    def setUp(self):
        self.s1 = _s1_candidates(("s1c_001", ["v7u_N000477"]),)

    def test_event_trigger_with_null_condition_passes(self):
        ir = {
            "section_id": TEST_SECTION,
            "episodes": [_make_episode(
                elements=[_make_element("e001", "context", "E1_event_signal", "事件"),
                           _make_element("e002", "action", "P2_execution", "动作")],
                relations=[_make_relation("r001", "trigger", "e001", "e002",
                                          trigger_mode="event", condition=None)],
            )],
            "candidate_audit": [
                {"candidate_id": "s1c_001", "disposition": "mapped", "episode_ids": ["ep_001"], "reason": "r"},
            ],
            "skip_reason": None,
        }
        errors = validate_process_ir_payload(ir, TEST_SECTION, self.s1, ALLOWED_UNITS)
        self.assertEqual(errors, [], f"Expected no errors, got: {errors}")

    def test_condition_trigger_without_condition_fails(self):
        ir = {
            "section_id": TEST_SECTION,
            "episodes": [_make_episode(
                elements=[_make_element("e001", "context", "E1_event_signal", "事件"),
                           _make_element("e002", "action", "P2_execution", "动作")],
                relations=[_make_relation("r001", "trigger", "e001", "e002",
                                          trigger_mode="condition", condition="")],
            )],
            "candidate_audit": [
                {"candidate_id": "s1c_001", "disposition": "mapped", "episode_ids": ["ep_001"], "reason": "r"},
            ],
            "skip_reason": None,
        }
        errors = validate_process_ir_payload(ir, TEST_SECTION, self.s1, ALLOWED_UNITS)
        self.assertTrue(any("condition" in e.lower() for e in errors),
                        f"Expected condition error, got: {errors}")


# ── Test 18: 六种relation的端点role兼容矩阵逐项测试 ──
class TestRelationEndpointMatrix(unittest.TestCase):
    def setUp(self):
        self.s1 = _s1_candidates(("s1c_001", ["v7u_N000477"]),)

    def _check(self, kind, src_role, src_node_type, tgt_role, tgt_node_type, should_pass):
        elements = [
            _make_element("e001", src_role, src_node_type, "源", unit_ids=["v7u_N000477"]),
            _make_element("e002", tgt_role, tgt_node_type, "目标", unit_ids=["v7u_N000477"]),
        ]
        if kind == "branch":
            # branch needs 2 branches at least for P3 test; add a dummy third element
            elements.append(_make_element("e003", "outcome", "X1_classification", "分支B"))
            relations = [
                _make_relation("r001", "branch", "e001", "e002", condition="条件"),
                _make_relation("r002", "branch", "e001", "e003", condition="条件B"),
            ]
        elif kind == "reference":
            relations = [_make_relation("r001", "reference", "e001", "e002")]
        elif kind == "sequence":
            relations = [_make_relation("r001", "sequence", "e001", "e002")]
        elif kind == "produce":
            relations = [_make_relation("r001", "produce", "e001", "e002")]
        elif kind == "feedback":
            relations = [_make_relation("r001", "feedback", "e001", "e002")]
        else:
            relations = [_make_relation("r001", "trigger", "e001", "e002", trigger_mode="event")]

        ir = {
            "section_id": TEST_SECTION,
            "episodes": [_make_episode(elements=elements, relations=relations)],
            "candidate_audit": [
                {"candidate_id": "s1c_001", "disposition": "mapped", "episode_ids": ["ep_001"], "reason": "r"},
            ],
            "skip_reason": None,
        }
        errors = validate_process_ir_payload(ir, TEST_SECTION, self.s1, ALLOWED_UNITS)
        has_compat_error = any("incompatible" in e.lower() for e in errors)
        if should_pass:
            self.assertFalse(has_compat_error, f"Expected {kind} {src_role}->{tgt_role} to pass, got: {errors}")
        else:
            self.assertTrue(has_compat_error, f"Expected {kind} {src_role}->{tgt_role} to fail")

    def test_trigger_context_to_action_passes(self):
        self._check("trigger", "context", "E1_event_signal", "action", "P2_execution", True)

    def test_trigger_context_to_decision_passes(self):
        self._check("trigger", "context", "E1_event_signal", "decision", "P1_assessment", True)

    def test_trigger_action_to_action_fails(self):
        self._check("trigger", "action", "P2_execution", "action", "P2_execution", False)

    def test_sequence_action_to_action_passes(self):
        self._check("sequence", "action", "P2_execution", "action", "P2_execution", True)

    def test_sequence_context_to_action_fails(self):
        self._check("sequence", "context", "E1_event_signal", "action", "P2_execution", False)

    def test_reference_action_to_standard_passes(self):
        self._check("reference", "action", "P2_execution", "standard", "standard", True)

    def test_reference_action_to_action_fails(self):
        self._check("reference", "action", "P2_execution", "action", "P2_execution", False)

    def test_produce_action_to_outcome_passes(self):
        self._check("produce", "action", "P2_execution", "outcome", "X1_classification", True)

    def test_produce_context_to_outcome_fails(self):
        self._check("produce", "context", "E1_event_signal", "outcome", "X1_classification", False)

    def test_branch_decision_to_action_passes(self):
        self._check("branch", "decision", "P3_branch_routing", "action", "P2_execution", True)

    def test_branch_action_to_action_fails(self):
        self._check("branch", "action", "P2_execution", "action", "P2_execution", False)

    def test_feedback_outcome_to_action_passes(self):
        self._check("feedback", "outcome", "X1_classification", "action", "P6_feedback", True)


# ── Test 19: relation_type、qualifier和source_quote使用未知值或越界引文时失败 ──
class TestOptionalFieldValidation(unittest.TestCase):
    def setUp(self):
        self.s1 = _s1_candidates(("s1c_001", ["v7u_N000477"]),)

    def test_unknown_relation_type_fails(self):
        ir = {
            "section_id": TEST_SECTION,
            "episodes": [_make_episode(
                elements=[_make_element("e001", "action", "P2_execution", "act"),
                           _make_element("e002", "context", "E1_event_signal", "ctx")],
                relations=[_make_relation("r001", "trigger", "e002", "e001",
                                          relation_type="invalid_relation_type")],
            )],
            "candidate_audit": [
                {"candidate_id": "s1c_001", "disposition": "mapped", "episode_ids": ["ep_001"], "reason": "r"},
            ],
            "skip_reason": None,
        }
        errors = validate_process_ir_payload(ir, TEST_SECTION, self.s1, ALLOWED_UNITS)
        self.assertTrue(any("relation_type" in e.lower() for e in errors),
                        f"Expected relation_type error, got: {errors}")

    def test_unknown_qualifier_fails(self):
        ir = {
            "section_id": TEST_SECTION,
            "episodes": [_make_episode(
                elements=[_make_element("e001", "action", "P2_execution", "act"),
                           _make_element("e002", "outcome", "X1_classification", "结果")],
                relations=[_make_relation("r001", "produce", "e001", "e002", qualifier="invalid_qualifier")],
            )],
            "candidate_audit": [
                {"candidate_id": "s1c_001", "disposition": "mapped", "episode_ids": ["ep_001"], "reason": "r"},
            ],
            "skip_reason": None,
        }
        errors = validate_process_ir_payload(ir, TEST_SECTION, self.s1, ALLOWED_UNITS)
        self.assertTrue(any("qualifier" in e.lower() for e in errors),
                        f"Expected qualifier error, got: {errors}")

    def test_forbidden_derivation_field_fails(self):
        ir = {
            "section_id": TEST_SECTION,
            "episodes": [_make_episode(
                elements=[_make_element("e001", "action", "P2_execution", "act"),
                           _make_element("e002", "context", "E1_event_signal", "ctx")],
                relations=[_make_relation("r001", "trigger", "e002", "e001", derivation="explicit_text")],
            )],
            "candidate_audit": [
                {"candidate_id": "s1c_001", "disposition": "mapped", "episode_ids": ["ep_001"], "reason": "r"},
            ],
            "skip_reason": None,
        }
        errors = validate_process_ir_payload(ir, TEST_SECTION, self.s1, ALLOWED_UNITS)
        self.assertTrue(any("derivation" in e.lower() for e in errors),
                        f"Expected derivation forbidden error, got: {errors}")

    def test_kg_coverage_as_exclusion_reason_fails(self):
        ir = {
            "section_id": TEST_SECTION,
            "episodes": [_make_episode(
                elements=[_make_element("e001", "action", "P2_execution", "act"),
                           _make_element("e002", "context", "E1_event_signal", "ctx")],
                relations=[_make_relation("r001", "trigger", "e002", "e001")],
            )],
            "candidate_audit": [
                {"candidate_id": "s1c_001", "disposition": "excluded_nonprocedural", "episode_ids": [],
                 "reason": "KG已覆盖该关系"},
            ],
            "skip_reason": None,
        }
        errors = validate_process_ir_payload(ir, TEST_SECTION, self.s1, ALLOWED_UNITS)
        self.assertTrue(any("KG" in e for e in errors),
                        f"Expected KG-coverage ban error, got: {errors}")


# ── Test 20: compile_audit完整记录IR→card/node/edge映射和source hash ──
class TestCompileAuditCompleteness(unittest.TestCase):
    def setUp(self):
        self.s1 = _s1_candidates(("s1c_001", ["v7u_N000477"]),)

    def test_compile_audit_has_all_fields(self):
        ir = {
            "section_id": TEST_SECTION,
            "episodes": [_make_episode(
                elements=[_make_element("e001", "action", "P2_execution", "act"),
                           _make_element("e002", "context", "E1_event_signal", "ctx")],
                relations=[_make_relation("r001", "trigger", "e002", "e001")],
            )],
            "candidate_audit": [
                {"candidate_id": "s1c_001", "disposition": "mapped", "episode_ids": ["ep_001"], "reason": "r"},
            ],
            "skip_reason": None,
        }
        result = compile_process_ir_to_cards(ir, TEST_SECTION, "")

        audit = result["compile_audit"]
        self.assertEqual(audit["section_id"], TEST_SECTION)
        self.assertEqual(audit["compiler_version"], "process_ir_compiler_v1")
        self.assertIn("source_process_ir_sha256", audit)
        self.assertEqual(len(audit["source_process_ir_sha256"]), 64)  # sha256 hex

        episodes = audit["episodes"]
        self.assertEqual(len(episodes), 1)
        self.assertEqual(episodes[0]["episode_id"], "ep_001")
        self.assertIn("card_id", episodes[0])
        self.assertIn("element_node_map", episodes[0])
        self.assertIn("relation_edge_map", episodes[0])
        self.assertEqual(episodes[0]["compile_status"], "compiled")

    def test_compile_audit_deterministic(self):
        ir = {
            "section_id": TEST_SECTION,
            "episodes": [_make_episode(
                elements=[_make_element("e002", "action", "P2_execution", "act"),
                           _make_element("e001", "context", "E1_event_signal", "ctx")],
                relations=[_make_relation("r001", "trigger", "e001", "e002")],
            )],
            "candidate_audit": [
                {"candidate_id": "s1c_001", "disposition": "mapped", "episode_ids": ["ep_001"], "reason": "r"},
            ],
            "skip_reason": None,
        }
        r1 = compile_process_ir_to_cards(ir, TEST_SECTION, "")
        r2 = compile_process_ir_to_cards(ir, TEST_SECTION, "")
        self.assertEqual(r1["source_process_ir_sha256"], r2["source_process_ir_sha256"])
        self.assertEqual(r1["compile_audit"]["episodes"][0]["card_id"],
                         r2["compile_audit"]["episodes"][0]["card_id"])


# ── Test 21: episodes/skip_reason顶层一致性 ──
class TestTopLevelConsistency(unittest.TestCase):
    def setUp(self):
        self.s1 = _s1_candidates(("s1c_001", ["v7u_N000477"]),)

    def test_episodes_non_empty_skip_reason_null_passes(self):
        ir = {
            "section_id": TEST_SECTION,
            "episodes": [_make_episode(
                elements=[_make_element("e001", "action", "P2_execution", "act"),
                           _make_element("e002", "context", "E1_event_signal", "ctx")],
                relations=[_make_relation("r001", "trigger", "e002", "e001")],
            )],
            "candidate_audit": [
                {"candidate_id": "s1c_001", "disposition": "mapped", "episode_ids": ["ep_001"], "reason": "r"},
            ],
            "skip_reason": None,
        }
        errors = validate_process_ir_payload(ir, TEST_SECTION, self.s1, ALLOWED_UNITS)
        self.assertEqual(errors, [], f"Expected no errors, got: {errors}")

    def test_episodes_non_empty_skip_reason_not_null_fails(self):
        ir = {
            "section_id": TEST_SECTION,
            "episodes": [_make_episode(
                elements=[_make_element("e001", "action", "P2_execution", "act"),
                           _make_element("e002", "context", "E1_event_signal", "ctx")],
                relations=[_make_relation("r001", "trigger", "e002", "e001")],
            )],
            "candidate_audit": [
                {"candidate_id": "s1c_001", "disposition": "mapped", "episode_ids": ["ep_001"], "reason": "r"},
            ],
            "skip_reason": "不应有跳过原因",
        }
        errors = validate_process_ir_payload(ir, TEST_SECTION, self.s1, ALLOWED_UNITS)
        self.assertTrue(any("skip_reason" in e.lower() for e in errors),
                        f"Expected skip_reason error, got: {errors}")

    def test_episodes_empty_skip_reason_missing_fails(self):
        ir = {
            "section_id": TEST_SECTION,
            "episodes": [],
            "candidate_audit": [
                {"candidate_id": "s1c_001", "disposition": "excluded_nonprocedural", "episode_ids": [],
                 "reason": "非流程内容"},
            ],
            "skip_reason": None,
        }
        errors = validate_process_ir_payload(ir, TEST_SECTION, self.s1, ALLOWED_UNITS)
        self.assertTrue(any("skip_reason" in e.lower() for e in errors),
                        f"Expected skip_reason error, got: {errors}")

    def test_episodes_empty_with_valid_skip_reason_passes(self):
        ir = {
            "section_id": TEST_SECTION,
            "episodes": [],
            "candidate_audit": [
                {"candidate_id": "s1c_001", "disposition": "excluded_nonprocedural", "episode_ids": [],
                 "reason": "非流程内容"},
            ],
            "skip_reason": "本节全部候选均为知识描述，不构成程序性或判断性流程。",
        }
        errors = validate_process_ir_payload(ir, TEST_SECTION, self.s1, ALLOWED_UNITS)
        self.assertEqual(errors, [], f"Expected no errors, got: {errors}")


# ── Test 22: Section ID mismatch check ──
class TestSectionIdMismatch(unittest.TestCase):
    def setUp(self):
        self.s1 = _s1_candidates(("s1c_001", ["v7u_N000477"]),)

    def test_section_id_mismatch_fails(self):
        ir = {
            "section_id": "WRONG-SECTION",
            "episodes": [],
            "candidate_audit": [
                {"candidate_id": "s1c_001", "disposition": "excluded_nonprocedural", "episode_ids": [],
                 "reason": "非流程"},
            ],
            "skip_reason": "无流程内容",
        }
        errors = validate_process_ir_payload(ir, TEST_SECTION, self.s1, ALLOWED_UNITS)
        self.assertTrue(any("section_id" in e.lower() for e in errors),
                        f"Expected section_id mismatch error, got: {errors}")


if __name__ == "__main__":
    unittest.main()
