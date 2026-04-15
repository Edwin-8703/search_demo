from collections import defaultdict
from django.core.management.base import BaseCommand
from django.contrib.postgres.search import SearchVector
from django.db import transaction
from documents.models import Document
from django.core.files import File
from pathlib import Path
import tempfile


BATCH_SIZE = 20
CONTRIBUTOR = 'Hugging Face / MedQuad Health Dataset'

MIN_WORDS = 800
MAX_WORDS = 4500


class Command(BaseCommand):
    help = 'Ingest MedQuad into structured documents'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=500)

    @transaction.atomic
    def handle(self, *args, **options):
        limit = options['limit']

        self.stdout.write('Loading dataset...')

        from datasets import load_dataset
        ds = load_dataset('keivalya/MedQuad-MedicalQnADataset', split='train')

        grouped = defaultdict(list)

        for row in ds:
            focus = (row.get('focus') or 'General Health').strip().title()
            question = (row.get('Question') or '').strip()
            answer = (row.get('Answer') or '').strip()
            qtype = (row.get('qtype') or '').strip().title()

            if answer:
                grouped[focus].append((qtype, question, answer))

        self.stdout.write(f'{len(grouped)} conditions found.')

        done = 0
        skipped = 0

        for focus, pairs in grouped.items():
            if done >= limit:
                break

            current_chunk = []
            current_words = 0

            chunks = []

            # Build chunks
            for qtype, question, answer in pairs:
                section = []

                if qtype:
                    section.append(f"\n## {qtype}\n")
                if question:
                    section.append(f"**{question}**\n")

                section.append(f"{answer}\n")

                section_text = "\n".join(section)
                section_words = len(section_text.split())

                if current_words + section_words > MAX_WORDS:
                    if current_words >= MIN_WORDS:
                        chunks.append(current_chunk)
                    current_chunk = []
                    current_words = 0

                current_chunk.append(section_text)
                current_words += section_words

            # finalize last chunk
            if current_chunk and MIN_WORDS <= current_words <= MAX_WORDS:
                chunks.append(current_chunk)
            else:
                skipped += 1
                continue

            # Save each chunk as a Document
            for chunk in chunks:
                if done >= limit:
                    break

                full_text = "\n\n".join(chunk)

                if not full_text.strip():
                    continue

                # Create temp file
                with tempfile.NamedTemporaryFile(
                    mode='w',
                    suffix='.txt',
                    delete=False,
                    encoding='utf-8'
                ) as tmp:
                    tmp.write(full_text)
                    tmp_path = tmp.name

                # Create document
                doc = Document(
                    title=focus,
                    contributor=CONTRIBUTOR,
                    file_mime='text/plain',
                )

                # Attach file
                with open(tmp_path, 'rb') as f:
                    doc.file.save(f"{focus[:50]}.txt", File(f), save=False)

                doc.save()

                # Extract markdown
                try:
                    from documents.docling_pipeline import extract_markdown
                    markdown = extract_markdown(Path(doc.file.path))
                    doc.markdown_text = markdown
                    doc.save()
                except Exception as e:
                    self.stdout.write(f"Markdown extraction failed: {e}")

                done += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Created {done} documents. Skipped {skipped} groups."
            )
        )

    @staticmethod
    def _rebuild_vectors():
        Document.objects.update(
            search_text=(
                SearchVector('title', weight='A') +
                SearchVector('markdown_text', weight='B')
            )
        )