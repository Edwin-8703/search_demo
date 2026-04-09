from django.db import models
from django.contrib.postgres.search import SearchVectorField


class Document(models.Model):
    # ── Identity ──────────────────────────────────────────────────────────────
    title       = models.TextField()
    contributor = models.CharField(max_length=200, blank=True, default='')
    created_at  = models.DateTimeField(auto_now_add=True)

    # ── Media-storage metadata (path/size only — no blobs) ───────────────────
    file_path = models.CharField(max_length=500, blank=True)
    file_size = models.PositiveIntegerField(null=True, blank=True)
    file_mime = models.CharField(max_length=100, blank=True)

    # ── Docling output ────────────────────────────────────────────────────────
    markdown_text = models.TextField(blank=True)

    # ── Full-text search (no GIN index per spec) ──────────────────────────────
    search_text = SearchVectorField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title[:100]