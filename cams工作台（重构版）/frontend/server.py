#!/usr/bin/env python3
"""Serve the V7 workbench and render one textbook PDF page on demand."""

from __future__ import annotations

import argparse
import json
import mimetypes
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import fitz


ROOT = Path(__file__).resolve().parent
TEXTBOOK_ROOT = ROOT / "data" / "releases" / "v7"
DOCUMENTS: dict[Path, fitz.Document] = {}


def resolve_textbook_pdf(language: str) -> tuple[Path, int]:
    if language not in {"zh", "en"}:
        raise ValueError("language must be zh or en")
    active = json.loads((TEXTBOOK_ROOT / "textbook-active.json").read_text(encoding="utf-8"))
    release_path = Path(active["release_path"])
    release_dir = (TEXTBOOK_ROOT / release_path).resolve()
    if TEXTBOOK_ROOT.resolve() not in release_dir.parents:
        raise ValueError("invalid textbook release path")
    manifest = json.loads((release_dir / "manifest.json").read_text(encoding="utf-8"))
    asset_name = manifest["assets"]["zh_pdf" if language == "zh" else "en_pdf"]
    pdf_path = (release_dir / asset_name).resolve()
    if release_dir not in pdf_path.parents or pdf_path.suffix.lower() != ".pdf":
        raise ValueError("invalid textbook PDF path")
    return pdf_path, int(manifest["counts"]["bilingual_pdf_pages"])


class WorkbenchHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/textbook-page":
            self.render_textbook_page(parse_qs(parsed.query))
            return
        super().do_GET()

    def render_textbook_page(self, query: dict[str, list[str]]) -> None:
        try:
            language = query.get("lang", ["zh"])[0]
            page_number = int(query.get("page", ["1"])[0])
            scale = float(query.get("scale", ["1.6"])[0])
            pdf_path, page_count = resolve_textbook_pdf(language)
            if not 1 <= page_number <= page_count:
                raise ValueError("page is outside the textbook range")
            scale = min(2.5, max(0.8, scale))
            document = DOCUMENTS.get(pdf_path)
            if document is None:
                document = fitz.open(pdf_path)
                DOCUMENTS[pdf_path] = document
            page = document.load_page(page_number - 1)
            png = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False).tobytes("png")
        except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
            self.send_error(HTTPStatus.BAD_REQUEST, str(error))
            return
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "image/png")
        self.send_header("Content-Length", str(len(png)))
        self.send_header("Cache-Control", "public, max-age=86400")
        self.end_headers()
        self.wfile.write(png)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=5175)
    args = parser.parse_args()
    mimetypes.add_type("application/pdf", ".pdf")
    server = ThreadingHTTPServer(("127.0.0.1", args.port), WorkbenchHandler)
    print(f"CAMS V7 workbench: http://127.0.0.1:{args.port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
