import io
import logging
from typing import Tuple

from fastapi import HTTPException

logger = logging.getLogger(__name__)

_MAX_FILE_BYTES = 20 * 1024 * 1024
_ALLOWED_MIME = {
    "application/pdf",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/tiff",
    "image/webp",
}
_ALLOWED_EXT = {".pdf", ".txt", ".docx", ".png", ".jpg", ".jpeg", ".tiff", ".webp"}


def _ext(filename: str) -> str:
    import os
    return os.path.splitext(filename.lower())[1]


def _extract_pdf(data: bytes) -> str:
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(data))
    parts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            parts.append(text.strip())
    return "\n".join(parts)


def _extract_docx(data: bytes) -> str:
    from docx import Document
    doc = Document(io.BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def _extract_txt(data: bytes) -> str:
    for enc in ("utf-8", "utf-16", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    raise HTTPException(status_code=422, detail="Could not decode text file encoding.")


def _extract_image(data: bytes) -> str:
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        raise HTTPException(
            status_code=501,
            detail="OCR dependencies not installed. Run: pip install pillow pytesseract",
        )
    img = Image.open(io.BytesIO(data))
    text = pytesseract.image_to_string(img)
    if not text.strip():
        raise HTTPException(status_code=422, detail="OCR produced no text from image.")
    return text


class FileExtractorService:
    def validate_and_extract(
        self, filename: str, content_type: str, data: bytes
    ) -> Tuple[str, str]:
        if len(data) > _MAX_FILE_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"File exceeds 20 MB limit ({len(data) // 1024} KB received).",
            )

        ext = _ext(filename)
        if ext not in _ALLOWED_EXT:
            raise HTTPException(
                status_code=415,
                detail=f"Unsupported file extension '{ext}'. Allowed: {sorted(_ALLOWED_EXT)}",
            )

        if content_type and content_type.split(";")[0].strip() not in _ALLOWED_MIME:
            logger.warning(
                "MIME type '%s' not in allowlist for file '%s', proceeding by extension.",
                content_type,
                filename,
            )

        if ext == ".pdf":
            text = _extract_pdf(data)
            file_type = "PDF"
        elif ext == ".docx":
            text = _extract_docx(data)
            file_type = "DOCX"
        elif ext == ".txt":
            text = _extract_txt(data)
            file_type = "TXT"
        elif ext in (".png", ".jpg", ".jpeg", ".tiff", ".webp"):
            text = _extract_image(data)
            file_type = "IMAGE"
        else:
            raise HTTPException(status_code=415, detail="Unhandled extension.")

        text = text.strip()
        if not text:
            raise HTTPException(
                status_code=422,
                detail="File extracted successfully but contained no readable text.",
            )

        logger.info(
            "Extracted %d chars from %s file '%s'.", len(text), file_type, filename
        )
        return text, file_type


file_extractor = FileExtractorService()
