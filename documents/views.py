import mimetypes
import threading
from pathlib import Path

from django.http import FileResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchHeadline, SearchVector
from django.db.models import F
from django.views.decorators.http import require_http_methods

from .models import Document
from .media_storage import save_file, get_absolute_path, file_exists
from .docling_pipeline import extract_markdown

ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.txt', '.md', '.html'}
MAX_UPLOAD_MB = 50
UPLOAD_TIMEOUT = 50  # seconds


def _index_document(doc):
    """Rebuild tsvector for one document."""
    Document.objects.filter(pk=doc.pk).update(
        search_text=(
            SearchVector('title',         weight='A', config='english') +
            SearchVector('markdown_text', weight='B', config='english')
        )
    )


def _run_with_timeout(fn, timeout, *args, **kwargs):
    """
    Run fn(*args, **kwargs) in a thread.
    Returns (result, None) on success or (None, error_message) on failure/timeout.
    Thread-safe — works in Django's dev server and production WSGI.
    """
    result = [None]
    error  = [None]

    def target():
        try:
            result[0] = fn(*args, **kwargs)
        except Exception as exc:
            error[0] = str(exc)

    t = threading.Thread(target=target, daemon=True)
    t.start()
    t.join(timeout)

    if t.is_alive():
        return None, f'Processing exceeded {timeout} seconds. Try a smaller file.'
    if error[0]:
        return None, error[0]
    return result[0], None


# ── Upload pipeline (wrapped for timeout) ────────────────────────────────────
def _upload_pipeline(raw, filename, content_type, title, contributor):
    """Runs in a thread — save → Docling → DB → index."""
    meta     = save_file(raw, filename, subfolder='uploads')
    abs_path = get_absolute_path(meta['file_path'])
    markdown = extract_markdown(abs_path)

    doc = Document.objects.create(
        title         = title,
        contributor   = contributor,
        file_path     = meta['file_path'],
        file_size     = meta['file_size'],
        file_mime     = content_type or 'application/octet-stream',
        markdown_text = markdown,
    )
    _index_document(doc)

    return {
        'title':       doc.title,
        'contributor': doc.contributor,
        'filename':    filename,
        'size':        meta['file_size'],
        'doc_id':      doc.id,
        'chars':       len(markdown),
    }


# ── Search ────────────────────────────────────────────────────────────────────
def search(request):
    query_str = request.GET.get('q', '').strip()
    results, count = [], 0
    total = Document.objects.count()

    if query_str:
        query = SearchQuery(query_str, search_type='websearch', config='english')
        qs = (
            Document.objects
            .annotate(rank=SearchRank(F('search_text'), query))
            .annotate(headline=SearchHeadline(
                'markdown_text', query, config='english',
                start_sel='<mark>', stop_sel='</mark>',
                max_words=40, min_words=20, max_fragments=2,
            ))
            .filter(search_text=query)
            .order_by('-rank')
        )
        count   = qs.count()
        results = qs[:50]

    return render(request, 'documents/search.html', {
        'query': query_str, 'results': results,
        'count': count, 'total': total, 'page': 'search',
    })


# ── Document list ─────────────────────────────────────────────────────────────
def document_list(request):
    docs  = Document.objects.order_by('-created_at')
    total = docs.count()
    return render(request, 'documents/document_list.html', {
        'docs': docs, 'total': total, 'page': 'docs',
    })


# ── Upload ────────────────────────────────────────────────────────────────────
@require_http_methods(['GET', 'POST'])
def upload(request):
    error   = None
    success = None

    if request.method == 'POST':
        uploaded    = request.FILES.get('file')
        title       = request.POST.get('title', '').strip()
        contributor = request.POST.get('contributor', '').strip()

        if not uploaded:
            error = 'Please select a file.'
        else:
            suffix = Path(uploaded.name).suffix.lower()
            if suffix not in ALLOWED_EXTENSIONS:
                error = f'File type "{suffix}" not allowed. Use: {", ".join(sorted(ALLOWED_EXTENSIONS))}'
            elif uploaded.size > MAX_UPLOAD_MB * 1024 * 1024:
                error = f'File too large. Max {MAX_UPLOAD_MB} MB.'

        if not error:
            # Default title to filename stem if user left it blank
            if not title:
                title = Path(uploaded.name).stem.replace('_', ' ').replace('-', ' ').title()

            raw = uploaded.read()

            success, error = _run_with_timeout(
                _upload_pipeline,
                UPLOAD_TIMEOUT,
                raw,
                uploaded.name,
                uploaded.content_type,
                title,
                contributor,
            )

    return render(request, 'documents/upload.html', {
        'error':   error,
        'success': success,
        'allowed': ', '.join(sorted(ALLOWED_EXTENSIONS)),
        'max_mb':  MAX_UPLOAD_MB,
        'page':    'upload',
    })


# ── Retrieve: preview or download ─────────────────────────────────────────────
def retrieve_document(request, doc_id):
    doc = get_object_or_404(Document, pk=doc_id)

    if not doc.file_path or not file_exists(doc.file_path):
        raise Http404('File not found in media storage.')

    abs_path  = get_absolute_path(doc.file_path)
    mime_type, _ = mimetypes.guess_type(str(abs_path))
    mime_type = mime_type or doc.file_mime or 'application/octet-stream'

    mode = request.GET.get('mode', 'preview')

    if mode == 'download':
        disposition = f'attachment; filename="{abs_path.name}"'
    elif mime_type.startswith('text/') or mime_type == 'application/pdf':
        disposition = f'inline; filename="{abs_path.name}"'
    else:
        disposition = f'attachment; filename="{abs_path.name}"'

    response = FileResponse(open(abs_path, 'rb'), content_type=mime_type)
    response['Content-Disposition'] = disposition
    return response