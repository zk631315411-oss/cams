import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[2] / "tools" / "v7_release" / "build_release.py"
SPEC = importlib.util.spec_from_file_location("build_release", SCRIPT)
BUILD_RELEASE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(BUILD_RELEASE)
sys.modules["build_release"] = BUILD_RELEASE

TEXTBOOK_SCRIPT = Path(__file__).parents[2] / "tools" / "v7_release" / "build_textbook_release.py"
TEXTBOOK_SPEC = importlib.util.spec_from_file_location("build_textbook_release", TEXTBOOK_SCRIPT)
BUILD_TEXTBOOK = importlib.util.module_from_spec(TEXTBOOK_SPEC)
assert TEXTBOOK_SPEC.loader is not None
TEXTBOOK_SPEC.loader.exec_module(BUILD_TEXTBOOK)


class V7ReleaseBuilderTests(unittest.TestCase):
    def write_json(self, path, payload):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    def test_builds_partial_release_and_marks_missing_evidence_unpublished(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            units = root / "units.json"
            questions = root / "questions.json"
            evidence = root / "evidence" / "questions" / "q_v7_q_000001.json"
            output = root / "release"
            self.write_json(units, {"units": [{"unit_id": "v7u_N000001", "chapter": "CH01", "knowledge_zh": "中文", "en_quote": "English", "heading_context": ["CH01"], "pdf_page": 1}]})
            self.write_json(questions, {"items": [{"question_id": "v7_q_000001", "stem_zh": "题目", "options": {"A": "选项"}, "risk_flags": [{"code": "ocr_fixed"}]}, {"question_id": "v7_q_000002", "stem_zh": "未发布", "options": {"A": "选项"}}]})
            self.write_json(evidence, {"question_id": "v7_q_000001", "pipeline_status": "ok", "predicted_answer": ["A"], "option_analysis": [{"option": "A", "judgement": "correct", "evidence_status": "direct", "evidence_cards": [{"unit_id": "v7u_N000001"}]}]})
            args = BUILD_RELEASE.parse_args(["--units", str(units), "--questions", str(questions), "--evidence-dir", str(root / "evidence"), "--output-dir", str(output), "--release-id", "v7-test", "--activate"])
            manifest = BUILD_RELEASE.create_release(args)
            release_questions = json.loads((output / "questions.json").read_text(encoding="utf-8"))["items"]
            self.assertEqual(manifest["counts"]["published_questions"], 1)
            self.assertEqual(release_questions[1]["publication_status"], "unpublished")
            self.assertIn("ocr_fixed", release_questions[0]["risk_flags"])
            self.assertTrue((output.parent / "active.json").exists())

    def test_rejects_unknown_unit_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_json(root / "units.json", {"units": [{"unit_id": "v7u_N000001"}]})
            self.write_json(root / "questions.json", {"items": [{"question_id": "v7_q_000001"}]})
            self.write_json(root / "evidence" / "q_v7_q_000001.json", {"question_id": "v7_q_000001", "option_analysis": [{"evidence_status": "direct", "evidence_cards": [{"unit_id": "v7u_N999999"}]}]})
            args = BUILD_RELEASE.parse_args(["--units", str(root / "units.json"), "--questions", str(root / "questions.json"), "--evidence-dir", str(root / "evidence"), "--output-dir", str(root / "release")])
            with self.assertRaises(BUILD_RELEASE.ReleaseError):
                BUILD_RELEASE.create_release(args)

    def test_rejects_v6_card_identifier_in_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_json(root / "units.json", {"units": [{"unit_id": "v7u_N000001"}]})
            self.write_json(root / "questions.json", {"items": [{"question_id": "v7_q_000001"}]})
            self.write_json(root / "evidence" / "q_v7_q_000001.json", {"question_id": "v7_q_000001", "option_analysis": [], "generated_explanation": {"core_analysis": {"text": "引用 v6s_N00001"}}})
            args = BUILD_RELEASE.parse_args(["--units", str(root / "units.json"), "--questions", str(root / "questions.json"), "--evidence-dir", str(root / "evidence"), "--output-dir", str(root / "release")])
            with self.assertRaises(BUILD_RELEASE.ReleaseError):
                BUILD_RELEASE.create_release(args)

    def test_builds_and_activates_bilingual_textbook_release(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            units = root / "units.json"
            self.write_json(units, {"units": [{"unit_id": "v7u_N000001", "chapter": "CH01", "knowledge_zh": "中文", "en_quote": "English", "heading_context": ["CH01"], "pdf_page": 1}]})
            self.write_json(root / "page-map.json", {"items": [{"zh_pdf_page": 1, "en_pdf_page": 1}]})
            aligned = root / "aligned.json"
            self.write_json(aligned, {"items": [
                {"zh_printed_page": "i", "en_printed_page": "i", "zh_text": "目录 中文章节 .... 1", "en_text": "Table of Contents CH01 .... 1"},
                {"zh_printed_page": "ii", "en_printed_page": "ii", "zh_text": "中文小节 .... 2", "en_text": "Section .... 2"},
            ]})
            (root / "zh.pdf").write_bytes(b"%PDF-1.4 zh")
            (root / "en.pdf").write_bytes(b"%PDF-1.4 en")
            output = root / "releases" / "textbook" / "v7-textbook-test"
            args = BUILD_TEXTBOOK.parse_args(["--units", str(units), "--zh-pdf", str(root / "zh.pdf"), "--en-pdf", str(root / "en.pdf"), "--page-map", str(root / "page-map.json"), "--aligned-pages", str(root / "aligned.json"), "--output-dir", str(output), "--release-id", "v7-textbook-test", "--activate"])
            manifest = BUILD_TEXTBOOK.create_textbook_release(args)
            self.assertEqual(manifest["counts"]["bilingual_pdf_pages"], 1)
            self.assertTrue((output / "textbook-zh.pdf").exists())
            self.assertTrue((root / "releases" / "textbook-active.json").exists())
            chapter = json.loads((output / "chapters.json").read_text(encoding="utf-8"))["items"][0]
            self.assertEqual(chapter["title_zh"], "中文章节")
            titles = BUILD_TEXTBOOK.bilingual_chapter_titles(aligned, [{"title": "CH01"}, {"title": "Section"}])
            self.assertEqual(titles["section"], "中文小节")


if __name__ == "__main__":
    unittest.main()
