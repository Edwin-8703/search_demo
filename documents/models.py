# documents/models.py
from django.db import models
from django.contrib.postgres.search import SearchVectorField


class Document(models.Model):
    title       = models.TextField()
    contributor = models.CharField(max_length=200, blank=True, default='')
    created_at  = models.DateTimeField(auto_now_add=True)

    # FileField — Django saves the file to MEDIA_ROOT/uploads/
    # DB stores only the relative path (e.g. 'uploads/report.pdf')
    # No BinaryField, no manual file_path CharField
    file      = models.FileField(upload_to='uploads/', blank=True)
    file_mime = models.CharField(max_length=100, blank=True)

    # Docling output — markdown extracted from the file
    markdown_text = models.TextField(blank=True)

    # FTS — no GinIndex per spec
    search_text = SearchVectorField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title[:100]