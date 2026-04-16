# documents/models.py
from django.db import models
from django.contrib.postgres.search import SearchVectorField
from django.db.models.signals import post_delete
from django.dispatch import receiver



class Document(models.Model):
    title       = models.TextField()
    contributor = models.CharField(max_length=200, blank=True, default='')
    created_at  = models.DateTimeField(auto_now_add=True)
    file      = models.FileField(upload_to='uploads/', blank=True) # The file itself lands on disk (MEDIA_ROOT/uploads/) but the DB only stores the relative path via file_path.
    file_mime = models.CharField(max_length=100, blank=True)

    # Docling output — markdown extracted from the file
    markdown_text = models.TextField(blank=True)

    search_text = SearchVectorField(null=True, blank=True) 

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title[:100]
    

@receiver(post_delete, sender=Document) #When a Document instance is deleted, this signal handler ensures that the associated file on disk is also removed, preventing orphaned files and saving storage space.
def delete_file_on_document_delete(sender, instance, **kwargs):
 if instance.file:
  instance.file.delete(save=False)