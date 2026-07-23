import unittest
from xml.etree import ElementTree as ET

from tools.extract_v6_bold_methods import (
    W,
    Paragraph,
    Run,
    bold_spans,
    build_style_bold_map,
    segment_questions,
)


class BoldExtractionTests(unittest.TestCase):
    def test_adjacent_bold_runs_are_merged_and_punctuation_is_ignored(self):
        paragraph = Paragraph(
            paragraph_index=4,
            text="",
            runs=[
                Run("加粗", True, 0),
                Run("方法", True, 1),
                Run("。", True, 2),
                Run("普通", False, 3),
            ],
            location="body.p4",
        )
        self.assertEqual(bold_spans(paragraph)[0]["text"], "加粗方法。")
        self.assertEqual(bold_spans(paragraph)[0]["run_start"], 0)
        self.assertEqual(bold_spans(paragraph)[0]["run_end"], 2)

    def test_style_based_bold_is_resolved_through_based_on(self):
        xml = f"""
        <w:styles xmlns:w="{W[1:-1]}">
          <w:style w:type="character" w:styleId="Base">
            <w:rPr><w:b/></w:rPr>
          </w:style>
          <w:style w:type="character" w:styleId="Derived">
            <w:basedOn w:val="Base"/>
          </w:style>
        </w:styles>
        """
        self.assertTrue(build_style_bold_map(xml.strip().encode("utf-8"))["Derived"])

    def test_question_segmentation_preserves_answer_and_sections(self):
        paragraphs = [
            Paragraph(0, "文档标题", [Run("文档标题", False, 0)], "body.p0"),
            Paragraph(1, "1.题干", [Run("1.题干", False, 0)], "body.p1"),
            Paragraph(2, "A.选项", [Run("A.选项", False, 0)], "body.p2"),
            Paragraph(3, "答案:A", [Run("答案:A", False, 0)], "body.p3"),
            Paragraph(4, "解析:具体知识点:", [Run("解析:具体知识点:", False, 0)], "body.p4"),
            Paragraph(5, "2.第二题", [Run("2.第二题", False, 0)], "body.p5"),
            Paragraph(6, "答案:B", [Run("答案:B", False, 0)], "body.p6"),
        ]
        questions = segment_questions(paragraphs)
        self.assertEqual(len(questions), 2)
        self.assertEqual(questions[0]["answer"], "答案:A")
        self.assertEqual(questions[0]["fields"][2]["section"], "answer")
        self.assertEqual(questions[1]["question_id"], "2")


if __name__ == "__main__":
    unittest.main()
