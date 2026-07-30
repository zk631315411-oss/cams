import sys
import tempfile
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND))

from storage import WorkspaceError, WorkspaceStore


class WorkflowV2Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.store = WorkspaceStore(self.root)
        self.qid = "v7_q_000001"
        self.content = {"stem": "Which action is correct?", "options": {"A": "One", "B": "Two"},
                        "answer": ["A"], "source_answer": "A"}
        self.question = self.store.write_question(self.qid, self.content, "test", "test", "seed")

    def tearDown(self):
        self.temp.cleanup()

    def register(self, method="question_rag", route="bge"):
        question = self.store.read_question(self.qid)
        return self.store.register_evidence_run(
            self.qid,
            {"asset_versions": {"textbook": "v7-test"}, "query": "correct action",
             "items": [{"unit_id": "u1", "knowledge_zh": "教材中的直接规则", "pdf_page": 12,
                        "printed_page": "10", "route": route, "score": .9}]},
            method, "codex", "test", f"register {method}", question["version"], question["archive_revision"],
        )

    def curate_submit_confirm(self):
        self.register()
        question = self.store.read_question(self.qid)
        evidence_id = self.store.read_evidence_catalog(self.qid, limit=10)["items"][0]["evidence_id"]
        self.store.curate_evidence(
            self.qid, [{"evidence_id": evidence_id, "selected": True, "role": "support_answer"}],
            "codex", "test", "curate", expected_question_version=question["version"],
            expected_archive_revision=question["archive_revision"],
        )
        question = self.store.read_question(self.qid)
        self.store.submit_evidence_candidate(self.qid, "codex", "test", "submit", question["version"], question["archive_revision"])
        question = self.store.read_question(self.qid)
        return self.store.review_evidence_candidate(self.qid, "confirm", "educator", "frontend", "confirmed",
                                                    question["version"], question["archive_revision"])

    @staticmethod
    def analysis():
        return {"exam_point": "识别正确处置", "core_analysis": "规则与题干相符。",
                "option_analysis": {"A": "正确", "B": "主体错误"},
                "pitfall": "注意行为主体。", "evidence": ["u1"]}

    def test_discovery_channels_deduplicate_and_preserve_discovery_history(self):
        self.register("question_rag", "bge")
        self.register("grep_keyword", "grep")
        catalog = self.store.read_evidence_catalog(self.qid, limit=10)
        self.assertEqual(catalog["total"], 1)
        methods = {hit["method"] for hit in catalog["items"][0]["discoveries"]}
        self.assertEqual(methods, {"question_rag", "grep_keyword"})
        self.assertEqual(len(self.store._read_jsonl(self.root / "data/questions/v7_q_000001/retrieval_runs.jsonl")), 2)

    def test_full_version_bundle_is_required_for_release(self):
        self.curate_submit_confirm()
        question = self.store.read_question(self.qid)
        self.store.write_analysis_version(self.qid, self.analysis(), "codex", "test", "formal analysis",
                                          expected_question_version=question["version"],
                                          expected_archive_revision=question["archive_revision"])
        question = self.store.read_question(self.qid)
        self.store.add_analysis_feedback(self.qid, "core_analysis", "补充主体限制", "educator", "frontend", "feedback",
                                         question["version"], question["archive_revision"])
        question = self.store.read_question(self.qid)
        self.store.write_analysis_version(
            self.qid, self.analysis(), "codex", "test", "address feedback",
            [{"feedback_id": "fb_0001", "status": "addressed", "response": "已补充主体限制"}],
            question["version"], question["archive_revision"],
        )
        question = self.store.read_question(self.qid)
        self.store.mark_polishing_complete(self.qid, "educator", "frontend", "polishing done",
                                            question["version"], question["archive_revision"])
        question = self.store.read_question(self.qid)
        self.store.write_final_check(self.qid, {"status": "passed", "checks": ["question", "evidence", "analysis"],
                                                 "summary": "all exact"}, "codex", "test", "final check",
                                     question["version"], question["archive_revision"])
        question = self.store.read_question(self.qid)
        decision = self.store.record_workflow_decision(self.qid, "approved", "educator", "frontend", "approved",
                                                       question["version"], question["archive_revision"])
        self.assertEqual(decision["workflow"]["stage"], "release_ready")
        manifest = self.store.build_release("v7-workflow-test", "educator")
        self.assertEqual(manifest["counts"]["approved_questions"], 1)
        self.assertEqual(self.store.read_workflow(self.qid)["stage"], "released")

    def test_reopening_evidence_invalidates_downstream_references(self):
        self.curate_submit_confirm()
        question = self.store.read_question(self.qid)
        reopened = self.store.reopen_evidence(self.qid, "codex", "test", "direct rule is insufficient",
                                              question["version"], question["archive_revision"])
        self.assertEqual(reopened["workflow"]["stage"], "evidence_research")
        self.assertIsNone(reopened["workflow"]["references"]["confirmed_evidence_version"])
        self.assertEqual(self.store._read_json(self.root / "data/questions/v7_q_000001/evidence_confirmation.json")["status"], "reopened")

    def test_submitted_candidate_freezes_evidence_until_educator_decides(self):
        self.register()
        question = self.store.read_question(self.qid)
        evidence_id = self.store.read_evidence_catalog(self.qid, limit=10)["items"][0]["evidence_id"]
        self.store.curate_evidence(self.qid, [{"evidence_id": evidence_id, "selected": True, "role": "support_answer"}],
                                   "codex", "test", "curate", expected_question_version=question["version"],
                                   expected_archive_revision=question["archive_revision"])
        question = self.store.read_question(self.qid)
        self.store.submit_evidence_candidate(self.qid, "codex", "test", "submit", question["version"], question["archive_revision"])
        with self.assertRaises(WorkspaceError):
            self.register("grep_keyword", "grep")

    def test_task_state_never_advances_formal_milestone(self):
        before = self.store.read_workflow(self.qid)["stage"]
        question = self.store.read_question(self.qid)
        result = self.store.set_task_state(self.qid, "grep_keyword", "running", "codex", "search exact phrase",
                                           next_step="核对原页", expected_question_version=question["version"],
                                           expected_archive_revision=question["archive_revision"])
        self.assertEqual(result["workflow"]["stage"], before)
        self.assertEqual(result["task"]["status"], "running")

    def test_optional_ds_input_hides_source_answer_and_failure_does_not_change_stage(self):
        self.register()
        question = self.store.read_question(self.qid)
        evidence_id = self.store.read_evidence_catalog(self.qid, limit=10)["items"][0]["evidence_id"]
        self.store.curate_evidence(self.qid, [{"evidence_id": evidence_id, "selected": True, "role": "support_answer"}],
                                   "codex", "test", "curate", expected_question_version=question["version"],
                                   expected_archive_revision=question["archive_revision"])
        packet = self.store.prepare_ds_opinion_input(self.qid)
        self.assertNotIn("answer", packet["question"]["content"])
        self.assertNotIn("source_answer", packet["question"]["content"])
        stage = self.store.read_workflow(self.qid)["stage"]
        question = self.store.read_question(self.qid)
        result = self.store.save_ds_opinion(self.qid, packet, None, "test-model", "failed", "codex",
                                            "optional second opinion", error="offline",
                                            expected_question_version=question["version"],
                                            expected_archive_revision=question["archive_revision"])
        self.assertEqual(result["workflow"]["stage"], stage)
        self.assertEqual(result["opinion"]["status"], "failed")

    def test_analysis_cannot_start_before_evidence_confirmation(self):
        with self.assertRaises(WorkspaceError):
            self.store.write_analysis_version(self.qid, self.analysis(), "codex", "test", "bypass")

    def test_v2_workflow_never_falls_back_to_legacy_approval(self):
        question = self.store.read_question(self.qid)
        question["status"] = "approved"
        self.store._write_json(self.root / "data/questions/v7_q_000001/question.json", question)
        self.store._write_json(self.root / "data/questions/v7_q_000001/codex_review.json",
                               {"question_version": question["version"], "version": 1,
                                "review": {"status": "reviewable"}})
        self.store._write_json(self.root / "data/questions/v7_q_000001/decision.json",
                               {"question_version": question["version"], "version": 1,
                                "decision": {"status": "approved"}})
        manifest = self.store.build_release("v7-no-legacy-bypass", "test")
        self.assertEqual(manifest["counts"]["approved_questions"], 0)


if __name__ == "__main__":
    unittest.main()
