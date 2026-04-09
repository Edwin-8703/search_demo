"""
docling_pipeline.py
───────────────────
Wraps Docling so the rest of the app just calls extract_markdown(path).

On upload / ingest:
  1. Original file is already saved to media storage.
  2. This module runs Docling on that path.
  3. Returns extracted markdown string → caller stores in search_demo.
"""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def extract_markdown(file_path: Path) -> str:
    """
    Run Docling on *file_path* and return the extracted markdown text.
    Falls back gracefully if Docling fails or the file is plain text.
    """
    suffix = file_path.suffix.lower()

    # ── Plain text / markdown files: read directly ────────────────────────────
    if suffix in ('.txt', '.md'):
        try:
            return file_path.read_text(encoding='utf-8', errors='replace')
        except Exception as exc:
            logger.warning("Could not read %s as text: %s", file_path, exc)
            return ''

    # ── PDF / DOCX / other: use Docling ──────────────────────────────────────
    try:
        from docling.document_converter import DocumentConverter

        converter = DocumentConverter()
        result    = converter.convert(str(file_path))
        markdown  = result.document.export_to_markdown()
        logger.info("Docling extracted %d chars from %s", len(markdown), file_path.name)
        return markdown

    except ImportError:
        logger.error(
            "Docling is not installed. Run: pip install docling\n"
            "Falling back to raw text read."
        )
        try:
            return file_path.read_text(encoding='utf-8', errors='replace')
        except Exception:
            return ''

    except Exception as exc:
        logger.error("Docling failed on %s: %s", file_path, exc)
        return ''