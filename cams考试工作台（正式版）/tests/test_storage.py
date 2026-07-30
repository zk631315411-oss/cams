import json
import sys
import tarfile
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND))

from backup import create_backup
from storage import LockError, WorkspaceError, WorkspaceStore
from retrieval.assets import WorkspacePaths
from retrieval.pipeline import _option_supplements, build_question_heads, make_config
from drafting.service import prepare_draft_input
import mcp_server


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.store = WorkspaceStore(self.root)
        self.qid = "v7_q_000001"
        self.content = {"stem_cn": "测试", "options": {"A": "正确"}, "answer": ["A"], "explanation": "说明"}

    def tearDown(self):
        self.temp.cleanup()

    def approve(self):
        self.store.write_question(self.qid, self.content, "tester", "test", "创建")
        # Exercise the pre-v2 compatibility branch explicitly.
        directory = self.root / "data" / "questions" / self.qid
        (directory / "workflow.json").unlink(missing_ok=True)
        (directory / "task_state.json").unlink(missing_ok=True)
        (directory / "task_history.jsonl").unlink(missing_ok=True)
        self.store.write_ds_draft(self.qid, {"evidence": [{"unit_id": "v7u_test"}]}, "tester", "test", "草稿")
        self.store.write_codex_review(self.qid, {"status": "reviewable", "textbook_evidence": [{"unit_id": "v7u_test"}], "external_sources": []}, "tester", "test", "核验")
        self.store.record_decision(self.qid, {"status": "approved"}, "tester", "test", "批准")

    def test_question_retrieval_keeps_heads_and_general_search_disables_p5(self):
        heads = build_question_heads({"stem": "识别受益所有人", "options": {"A": "自然人"}, "stem_en": "Identify beneficial owners", "options_en": {"A": "Natural persons"}})
        self.assertEqual([head["head_id"] for head in heads], ["stem_zh", "option_A_zh", "stem_en", "option_A_en"])
        self.assertTrue(make_config({}, question_mode=True).enable_p5)
        self.assertFalse(make_config({"enable_p5": True}, question_mode=False).enable_p5)
        self.assertEqual(WorkspacePaths.resolve(self.root).index_dir, self.root / "data" / "infrastructure" / "index")

    def test_option_supplements_do_not_mix_evidence_between_options(self):
        assets = SimpleNamespace(index={"unit_lookup": {
            "u1": {"unit_id": "u1", "knowledge_zh": "证据一"},
            "u2": {"unit_id": "u2", "knowledge_zh": "证据二"},
        }})
        bge_rows = [
            {"head_id": "option_only_A_zh", "option": "A", "language": "zh", "query": "甲", "route": "bge", "rank": 1, "raw_score": 0.9, "unit_id": "u1"},
            {"head_id": "option_only_B_zh", "option": "B", "language": "zh", "query": "乙", "route": "bge", "rank": 1, "raw_score": 0.9, "unit_id": "u2"},
        ]
        with patch("retrieval.pipeline._bge_rows", return_value=bge_rows), patch("retrieval.pipeline._bm25_rows", return_value=[]):
            result = _option_supplements({"options": {"A": "甲", "B": "乙"}}, assets, set(), make_config({}, question_mode=True))
        self.assertEqual(result["A"][0]["unit_id"], "u1")
        self.assertEqual(result["B"][0]["unit_id"], "u2")
        self.assertEqual(result["A"][0]["retrieval_hits"][0]["head_id"], "option_only_A_zh")

    def test_same_question_lock_rejects_second_writer(self):
        with self.store.question_lock(self.qid, "first", "edit"):
            with self.assertRaises(LockError):
                with self.store.question_lock(self.qid, "second", "edit"):
                    pass

    def test_content_change_invalidates_approval_and_release_uses_current_versions(self):
        self.approve()
        manifest = self.store.build_release("v7-test-release", "tester")
        self.assertEqual(manifest["counts"]["approved_questions"], 1)
        changed = dict(self.content, answer=["B"])
        self.store.write_question(self.qid, changed, "tester", "test", "修正答案")
        self.assertEqual(self.store.read_question(self.qid)["status"], "needs_revalidation")
        manifest = self.store.build_release("v7-test-release-2", "tester")
        self.assertEqual(manifest["counts"]["approved_questions"], 0)

    def test_archive_revision_tracks_all_writes_and_rejects_stale_writer(self):
        question = self.store.write_question(self.qid, self.content, "tester", "test", "创建")
        self.assertEqual(question["archive_revision"], 1)
        draft = self.store.write_ds_draft(
            self.qid, {"evidence": []}, "tester", "test", "草稿", expected_question_version=1,
            expected_archive_revision=1,
        )
        self.assertEqual(draft["archive_revision"], 2)
        self.assertEqual(self.store.read_question(self.qid)["archive_revision"], 2)
        with self.assertRaises(WorkspaceError):
            self.store.write_codex_review(
                self.qid, {"status": "needs_evidence", "textbook_evidence": []}, "tester", "test", "陈旧核验",
                expected_question_version=1, expected_archive_revision=1,
            )
        review = self.store.write_codex_review(
            self.qid, {"status": "needs_evidence", "textbook_evidence": []}, "tester", "test", "当前核验",
            expected_question_version=1, expected_archive_revision=2,
        )
        self.assertEqual(review["archive_revision"], 3)

    def test_daily_backup_contains_mutable_records_once(self):
        self.store.write_question(self.qid, self.content, "tester", "test", "创建")
        backup_root = self.root / "backup"
        first = create_backup(self.root, backup_root, reason="startup", daily=True)
        second = create_backup(self.root, backup_root, reason="startup", daily=True)
        self.assertTrue(first["created"])
        self.assertFalse(second["created"])
        with tarfile.open(first["path"], "r:gz") as archive:
            names = archive.getnames()
        self.assertIn(f"data/questions/{self.qid}/question.json", names)
        self.assertIn("backup-manifest.json", names)
        self.assertFalse(any(name.startswith("data/infrastructure/") for name in names))

    def test_mcp_lists_questions_and_rejects_unconfirmed_question_update(self):
        self.store.write_question(self.qid, self.content, "tester", "test", "创建")
        previous = mcp_server.STORE
        mcp_server.STORE = self.store
        try:
            listed = mcp_server.invoke("list_questions", {"status": "needs_revalidation"})
            self.assertEqual(listed["total"], 1)
            with self.assertRaises(WorkspaceError):
                mcp_server.invoke("update_question", {
                    "question_id": self.qid, "content": self.content, "reason": "未确认的修改",
                    "expected_question_version": 1, "expected_archive_revision": 1,
                })
        finally:
            mcp_server.STORE = previous

    def test_active_context_is_read_only_question_state_and_available_to_mcp(self):
        question = self.store.write_question(self.qid, self.content, "tester", "test", "创建")
        revision = question["archive_revision"]
        audit_count = len(self.store.read_audit(self.qid))

        context = self.store.write_active_context(self.qid)

        self.assertEqual(context["question_id"], self.qid)
        self.assertEqual(context["suggested_action"], "整理证据")
        self.assertEqual(self.store.read_question(self.qid)["archive_revision"], revision)
        self.assertEqual(len(self.store.read_audit(self.qid)), audit_count)
        previous = mcp_server.STORE
        mcp_server.STORE = self.store
        try:
            self.assertEqual(mcp_server.invoke("read_active_context", {})["question_id"], self.qid)
            tool = next(item for item in mcp_server.TOOLS if item["name"] == "read_active_context")
            self.assertTrue(mcp_server.tool_payload(tool)["annotations"]["readOnlyHint"])
        finally:
            mcp_server.STORE = previous

    def test_intake_archives_source_allocates_id_and_records_duplicate_candidates(self):
        self.store.write_question(self.qid, self.content, "tester", "test", "seed")
        source = self.root / "memory.png"
        source.write_bytes(b"not-a-real-image-but-an-original-file")
        created = self.store.create_question_intake(
            dict(self.content),
            {"source_type": "memory", "source_description": "trainer recall", "answer_status": "unknown"},
            [str(source)], "codex", "codex", "new intake",
        )
        self.assertEqual(created["question"]["question_id"], "v7_q_000002")
        self.assertEqual(created["question"]["status"], "duplicate_pending")
        self.assertEqual(created["intake"]["answer_status"], "unknown")
        self.assertEqual(created["duplicate_check"]["candidates"][0]["method"], "exact_normalized")
        archived = self.root / "data" / "questions" / "v7_q_000002" / "source" / "files" / "memory.png"
        self.assertEqual(archived.read_bytes(), source.read_bytes())

    def test_intake_without_archivable_source_is_blocked(self):
        created = self.store.create_question_intake(
            {"stem": "question", "options": {"A": "one", "B": "two"}},
            {"source_type": "memory", "answer_status": "unknown", "raw_text": "question"},
            [], "codex", "codex", "source path unavailable",
        )
        qid = created["question"]["question_id"]
        self.assertEqual(created["question"]["status"], "needs_source_clarification")
        with self.assertRaises(WorkspaceError):
            self.store.assert_ds_ready(qid)
        with self.assertRaises(WorkspaceError):
            self.store.resolve_duplicate_check(qid, "new", "incorrect bypass", "codex", "codex", "bypass", 1)
        with self.assertRaises(WorkspaceError):
            self.store.write_ds_draft(qid, {"evidence": []}, "codex", "codex", "blocked")

    def test_duplicate_resolution_unlocks_ds_and_draft_input_hides_source_answer(self):
        source = self.root / "third-party.pdf"
        source.write_bytes(b"%PDF-1.4 source")
        created = self.store.create_question_intake(
            {"stem": "Which rule applies?", "options": {"A": "Rule A", "B": "Rule B"}, "answer": ["A"], "source_answer": "A"},
            {"source_type": "third_party", "answer_status": "known"}, [str(source)],
            "codex", "codex", "archive source",
        )
        qid = created["question"]["question_id"]
        resolved = self.store.resolve_duplicate_check(qid, "new", "no existing question matches", "codex", "codex", "duplicate review", 1)
        self.assertEqual(resolved["question"]["status"], "ready_for_ds")
        with patch("drafting.service.retrieve_question_evidence", return_value={"main_candidates": []}):
            packet = prepare_draft_input(self.store, qid)
        self.assertNotIn("answer", packet["question"]["content"])
        self.assertNotIn("source_answer", packet["question"]["content"])
        draft = self.store.write_ds_draft(qid, {"evidence": []}, "codex", "codex", "ds draft", 1, 2)
        self.assertEqual(draft["archive_revision"], 3)
        self.assertEqual(self.store.read_question(qid)["status"], "ds_draft")

    def test_evidence_review_controls_draft_input_and_requires_exclusion_reason(self):
        source = self.root / "source.pdf"
        source.write_bytes(b"%PDF source")
        created = self.store.create_question_intake(
            {"stem": "Which rule applies?", "options": {"A": "Rule A", "B": "Rule B"}},
            {"source_type": "third_party", "answer_status": "unknown"}, [str(source)],
            "codex", "codex", "archive source",
        )
        qid = created["question"]["question_id"]
        resolved = self.store.resolve_duplicate_check(qid, "new", "no match", "codex", "codex", "duplicate review", 1)
        retrieval = {"retrieval_kind": "question", "asset_versions": {"textbook": "test"},
                     "main_candidates": [{"unit_id": "u1", "knowledge_zh": "第一条依据", "pdf_page": 12, "route": "rag", "score": 0.9},
                                         {"unit_id": "u2", "knowledge_zh": "第二条依据", "pdf_page": 13, "route": "kg", "score": 0.8}],
                     "kg_candidates": [], "option_supplements": {}}
        saved = self.store.save_evidence_results(qid, retrieval, "codex", "codex", "save evidence", 1, resolved["question"]["archive_revision"])
        items = saved["evidence_review"]["items"]
        with self.assertRaises(WorkspaceError):
            self.store.update_evidence_review(qid, [{"evidence_id": items[1]["evidence_id"], "status": "excluded"}], "web", "frontend", "exclude", 1, saved["question"]["archive_revision"])
        reviewed = self.store.update_evidence_review(
            qid,
            [{"evidence_id": items[0]["evidence_id"], "status": "adopted", "note": "直接支持定义"},
             {"evidence_id": items[1]["evidence_id"], "status": "excluded", "exclusion_reason": "仅为相邻概念"}],
            "web", "frontend", "review evidence", 1, saved["question"]["archive_revision"],
        )
        packet = prepare_draft_input(self.store, qid)
        self.assertEqual(packet["evidence_packet"]["selected_evidence"][0]["evidence_id"], items[0]["evidence_id"])
        draft = self.store.write_ds_draft(qid, {"evidence": [{"evidence_id": items[0]["evidence_id"]}]}, "codex", "codex", "draft", 1, reviewed["question"]["archive_revision"])
        self.assertEqual(draft["evidence_review_version"], reviewed["evidence_review"]["version"])

    def test_intake_content_change_resets_duplicate_gate(self):
        source = self.root / "source.pdf"; source.write_bytes(b"%PDF source")
        created = self.store.create_question_intake(
            {"stem": "first stem", "options": {"A": "yes"}}, {"source_type": "memory"}, [str(source)],
            "codex", "codex", "archive source",
        )
        qid = created["question"]["question_id"]
        self.store.resolve_duplicate_check(qid, "new", "unique", "codex", "codex", "duplicate review", 1)
        changed = self.store.write_question(
            qid, {"stem": "changed stem", "options": {"A": "yes"}}, "codex", "codex", "correct extraction", 1, 2,
        )
        self.assertEqual(changed["status"], "duplicate_pending")
        self.assertIsNone(self.store.read_record(qid, "duplicate_check")["decision"])
        with self.assertRaises(WorkspaceError):
            self.store.assert_ds_ready(qid)

    def test_merge_decision_permanently_blocks_ds(self):
        source = self.root / "question.jpg"; source.write_bytes(b"image")
        created = self.store.create_question_intake(
            {"stem": "same", "options": {"A": "yes"}}, {"source_type": "third_party"}, [str(source)],
            "codex", "codex", "archive source",
        )
        qid = created["question"]["question_id"]
        self.store.resolve_duplicate_check(qid, "merge", "same as an existing record", "codex", "codex", "merge", 1)
        self.assertEqual(self.store.read_question(qid)["status"], "merged")
        with self.assertRaises(WorkspaceError):
            self.store.assert_ds_ready(qid)

    def test_concurrent_intakes_receive_unique_contiguous_ids(self):
        source = self.root / "source.png"; source.write_bytes(b"source")
        def create(index):
            return self.store.create_question_intake(
                {"stem": f"question {index}", "options": {"A": "yes"}}, {"source_type": "memory"}, [str(source)],
                f"codex-{index}", "codex", "concurrent intake",
            )["question"]["question_id"]
        with ThreadPoolExecutor(max_workers=2) as pool:
            identifiers = sorted(pool.map(create, [1, 2]))
        self.assertEqual(identifiers, ["v7_q_000001", "v7_q_000002"])

    def test_unsupported_and_oversized_sources_never_pass_intake(self):
        unsupported = self.root / "source.txt"; unsupported.write_text("source", encoding="utf-8")
        oversized = self.root / "large.pdf"
        with oversized.open("wb") as stream:
            stream.truncate(20 * 1024 * 1024 + 1)
        first = self.store.create_question_intake(
            {"stem": "one", "options": {"A": "yes"}}, {"source_type": "other"}, [str(unsupported)],
            "codex", "codex", "unsupported source",
        )
        second = self.store.create_question_intake(
            {"stem": "two", "options": {"A": "yes"}}, {"source_type": "other"}, [str(oversized)],
            "codex", "codex", "oversized source",
        )
        self.assertEqual(first["question"]["status"], "needs_source_clarification")
        self.assertEqual(second["question"]["status"], "needs_source_clarification")


if __name__ == "__main__":
    unittest.main()
