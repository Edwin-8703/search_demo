from django.db import migrations, models
import django.contrib.postgres.search


class Migration(migrations.Migration):

    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id',            models.BigAutoField(auto_created=True, primary_key=True)),
                ('title',         models.TextField()),
                ('contributor',   models.CharField(max_length=200, blank=True, default='')),
                ('created_at',    models.DateTimeField(auto_now_add=True)),
                ('file_path',     models.CharField(max_length=500, blank=True)),
                ('file_size',     models.PositiveIntegerField(null=True, blank=True)),
                ('file_mime',     models.CharField(max_length=100, blank=True)),
                ('markdown_text', models.TextField(blank=True)),
                ('search_text',   django.contrib.postgres.search.SearchVectorField(null=True, blank=True)),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]