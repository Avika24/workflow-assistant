from io import BytesIO
import pytest
from pypdf import PdfWriter

from loaders import DocumentLoadError, load_txt, load_pdf, load_uploaded_file


def test_load_txt():
    assert load_txt(b"Hello\nWorld") == "Hello\nWorld"


def test_empty_txt_rejected():
    with pytest.raises(DocumentLoadError):
        load_txt(b"  ")


def test_empty_pdf_rejected():
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    output = BytesIO()
    writer.write(output)
    with pytest.raises(DocumentLoadError):
        load_pdf(output.getvalue())


def test_unsupported_file_rejected():
    with pytest.raises(DocumentLoadError):
        load_uploaded_file("data.docx", b"content")
