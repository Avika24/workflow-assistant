"""Input loaders for pasted text, TXT, and text-based PDF files."""
from io import BytesIO
from pathlib import Path
from pypdf import PdfReader

class DocumentLoadError(ValueError):
    """Raised when a document cannot provide usable text."""

def clean_text(text: str) -> str:
    return "\n".join(line.strip() for line in text.replace("\x00", "").splitlines() if line.strip()).strip()

def load_txt(data: bytes) -> str:
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise DocumentLoadError("The TXT file is not valid UTF-8 text.") from exc
    cleaned = clean_text(text)
    if not cleaned:
        raise DocumentLoadError("The TXT file is empty.")
    return cleaned

def load_pdf(data: bytes) -> str:
    try:
        reader = PdfReader(BytesIO(data))
        pages = [page.extract_text() or "" for page in reader.pages]
    except Exception as exc:
        raise DocumentLoadError("This PDF could not be read. Please upload a valid PDF.") from exc
    cleaned = clean_text("\n".join(pages))
    if not cleaned:
        raise DocumentLoadError("No selectable text was found. This PDF may be scanned or empty; scanned PDFs are not supported.")
    return cleaned

def load_uploaded_file(name: str, data: bytes) -> str:
    suffix = Path(name).suffix.lower()
    if suffix == ".txt":
        return load_txt(data)
    if suffix == ".pdf":
        return load_pdf(data)
    raise DocumentLoadError("Unsupported file type. Please upload a TXT or PDF file.")
