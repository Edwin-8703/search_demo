# documents/models.py
from django.db import models
from django.contrib.postgres.search import SearchVectorField
from django.db.models.signals import post_delete
from django.dispatch import receiver



class Document(models.Model):
    title       = models.TextField()
    contributor = models.CharField(max_length=200, blank=True, default='')
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    file      = models.FileField(upload_to='uploads/', blank=True)
    file_mime = models.CharField(max_length=100, blank=True)


    markdown_text = models.TextField(blank=True)

    # FTS — no GinIndex per spec
    search_text = SearchVectorField(null=True, blank=True)


    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title[:100]
    

@receiver(post_delete, sender=Document)
def delete_file_on_document_delete(sender, instance, **kwargs):
 if instance.file:
  instance.file.delete(save=False)