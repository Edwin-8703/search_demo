from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from documents.models import Document


class Command(BaseCommand):
    help = 'Delete all Hugging Face ingested documents and their media files.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help='Preview only, no deletion.')

    def handle(self, *args, **options):
        dry_run    = options['dry_run']
        media_root = Path(settings.MEDIA_ROOT)

        qs    = Document.objects.filter(contributor__istartswith='Hugging Face')
        total = qs.count()

        if total == 0:
            self.stdout.write('No Hugging Face documents found.')
            return

        self.stdout.write(f'Found {total} Hugging Face document(s).')

        if dry_run:
            self.stdout.write('--- DRY RUN ---')
            for doc in qs[:10]:
                self.stdout.write(f'  Would delete: [{doc.id}] {doc.title[:60]}')
            if total > 10:
                self.stdout.write(f'  ... and {total - 10} more.')
            return

        files_deleted = 0
        files_missing = 0
        for doc in qs:
            if doc.file_path:
                abs_path = media_root / doc.file_path
                if abs_path.exists():
                    abs_path.unlink()
                    files_deleted += 1
                else:
                    files_missing += 1

        ag_news_dir = media_root / 'ag_news'
        if ag_news_dir.exists() and not any(ag_news_dir.iterdir()):
            ag_news_dir.rmdir()
            self.stdout.write('Removed empty ag_news/ folder.')

        qs.delete()
        self.stdout.write(self.style.SUCCESS(
            f'Done. {total} DB records deleted, '
            f'{files_deleted} file(s) removed, '
            f'{files_missing} already missing.'
        ))
