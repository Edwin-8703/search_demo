
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def extract_markdown(file_path: Path, mode: str = "basic") -> str:
    import logging
    logger = logging.getLogger(__name__)

    suffix = file_path.suffix.lower()

    if suffix in ('.txt', '.md'):
        try:
            return file_path.read_text(encoding='utf-8', errors='replace')
        except Exception:
            return ''

    try:
        from docling.document_converter import DocumentConverter

        converter = DocumentConverter()
        result = converter.convert(str(file_path))
        markdown = result.document.export_to_markdown()

        # Simulate "modes" (since Docling doesn't support configs directly)
        if mode == "fast":
            markdown = markdown[:2000]  # shorter output
        elif mode == "layout":
            markdown = markdown  # keep full (best default)
        elif mode == "tables":
            markdown = markdown  # later you can enhance

        return markdown

    except Exception as exc:
        logger.error(f"Docling failed: {exc}")
        return ''