"""Helpers for creating test document bytes."""

from __future__ import annotations

import fitz


def make_pdf_bytes(pages: list[str]) -> bytes:
    document = fitz.open()
    for text in pages:
        page = document.new_page()
        page.insert_text((72, 72), text)
    content = document.tobytes()
    document.close()
    return content


def make_txt_bytes(text: str) -> bytes:
    return text.encode("utf-8")


def make_fake_pdf_html_bytes() -> bytes:
    return b"<html><body>Not a PDF</body></html>"
