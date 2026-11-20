from io import BytesIO
import pytest
from pypdf import PdfWriter

from loaders import DocumentLoadError, load_txt, load_pdf, load_uploaded_file


def test_txt_loader_and_empty_txt_error():
    assert load_txt(b"Hello\nWorld") == "Hello\nWorld"
    with pytest.raises(DocumentLoadError):
        load_txt(b"  ")


def test_pdf_text_extraction_empty_pdf_and_unsupported_file_errors(monkeypatch):
    class FakePage:
        def extract_text(self):
            return "Project notes from a text-based PDF."

    class FakeReader:
        pages = [FakePage()]

    monkeypatch.setattr("loaders.PdfReader", lambda *_args, **_kwargs: FakeReader())
    assert load_pdf(b"mock pdf bytes") == "Project notes from a text-based PDF."

    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    output = BytesIO()
    writer.write(output)
    with pytest.raises(DocumentLoadError):
        load_pdf(output.getvalue())
    with pytest.raises(DocumentLoadError):
        load_uploaded_file("data.docx", b"content")
