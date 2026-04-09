"""
ingest_hf.py — improved version
Creates documents between 2–10 pages (~800–4500 words).
Splits large topics and skips short ones.
"""

from collections import defaultdict
from django.core.management.base import BaseCommand
from django.contrib.postgres.search import SearchVector
from django.db import transaction
from documents.models import Document
from documents.media_storage import save_text_as_file, get_absolute_path
from documents.docling_pipeline import extract_markdown

BATCH_SIZE = 20
CONTRIBUTOR = 'Hugging Face / MedQuad Health Dataset'

MIN_WORDS = 800     # ~2 pages
MAX_WORDS = 4500    # ~10 pages


class Command(BaseCommand):
    help = 'Ingest MedQuad into 2–10 page documents.'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=500)

    def handle(self, *args, **options):
        limit = options['limit']

        self.stdout.write('Loading dataset...')

        from datasets import load_dataset
        ds = load_dataset('keivalya/MedQuad-MedicalQnADataset', split='train')

        # Group by condition
        grouped = defaultdict(list)
        for row in ds:
            focus = (row.get('focus') or 'General Health').strip().title()
            q = (row.get('Question') or '').strip()
            a = (row.get('Answer') or '').strip()
            qtype = (row.get('qtype') or '').strip().title()

            if a:
                grouped[focus].append((qtype, q, a))

        self.stdout.write(f'{len(grouped)} conditions found.')

        batch = []
        done = 0
        skipped = 0

        for focus, pairs in grouped.items():
            if done >= limit:
                break

            chunks = []
            current_chunk = []
            current_words = 0

            # Build chunks within size limits
            for qtype, question, answer in pairs:
                section = []

                if qtype:
                    section.append(f"\n## {qtype}\n")
                if question:
                    section.append(f"**{question}**\n")
                section.append(f"{answer}\n")

                section_text = "\n".join(section)
                section_words = len(section_text.split())

                # If adding exceeds max → save current chunk
                if current_words + section_words > MAX_WORDS:
                    if current_words >= MIN_WORDS:
                        chunks.append(current_chunk)
                    current_chunk = []
                    current_words = 0

                current_chunk.append(section_text)
                current_words += section_words

            # Add last chunk
            if MIN_WORDS <= current_words <= MAX_WORDS:
                chunks.append(current_chunk)
            else:
                skipped += 1
                continue

            # Save each chunk as a separate document
            for i, chunk in enumerate(chunks):
                if done >= limit:
                    break

                full_text = f"# {focus} (Part {i+1})\n\n" + "\n".join(chunk)

                safe_name = focus[:50].replace(' ', '_')
                filename = f"health_{done:04d}_{safe_name}_{i+1}.txt"

                meta = save_text_as_file(full_text, filename, subfolder='health')
                abs_path = get_absolute_path(meta['file_path'])
                markdown = extract_markdown(abs_path)

                batch.append(Document(
                    title=f"{focus} (Part {i+1})",
                    contributor=CONTRIBUTOR,
                    file_path=meta['file_path'],
                    file_size=meta['file_size'],
                    file_mime='text/plain',
                    markdown_text=markdown,
                ))

                done += 1

                if len(batch) >= BATCH_SIZE:
                    self._flush(batch)
                    batch = []
                    self.stdout.write(f"... {done} docs saved")

        if batch:
            self._flush(batch)

        self.stdout.write(f"Done: {done} docs | Skipped: {skipped}")
        self._rebuild_vectors()

    @staticmethod
    @transaction.atomic
    def _flush(docs):
        Document.objects.bulk_create(docs, ignore_conflicts=True)

    @staticmethod
    def _rebuild_vectors():
        Document.objects.update(
            search_text=(
                SearchVector('title', weight='A') +
                SearchVector('markdown_text', weight='B')
            )
        )