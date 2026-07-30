import sys
import unittest
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from textbook import TextbookError, TextbookService


class TextbookServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = TextbookService(ROOT)

    def test_manifest_and_page_render(self):
        info = self.service.info()
        self.assertEqual(info["page_count"], 547)
        png, metadata = self.service.render_page("zh", 1, 1.0)
        self.assertTrue(png.startswith(b"\x89PNG"))
        self.assertGreater(len(png), 1000)
        self.assertEqual(metadata["page"], 1)

    def test_text_match_returns_normalized_boxes(self):
        import fitz

        document = fitz.open(self.service.root / "textbook-zh.pdf")
        try:
            text = next(line.strip() for line in document.load_page(1).get_text().splitlines() if len(line.strip()) >= 8)
        finally:
            document.close()
        result = self.service.match("zh", 2, text)
        self.assertTrue(result["matched"])
        self.assertTrue(result["boxes"])
        self.assertGreaterEqual(result["boxes"][0]["x"], 0)
        self.assertLessEqual(result["boxes"][0]["x"] + result["boxes"][0]["width"], 1)

    def test_invalid_page_is_rejected(self):
        with self.assertRaises(TextbookError):
            self.service.render_page("zh", 548)


if __name__ == "__main__":
    unittest.main()
