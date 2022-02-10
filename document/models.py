import os
import uuid
from django.db import models
from django.conf import settings


class Tag(models.Model):
    """Tag to be use for documents."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Document(models.Model):
    """Identity Document"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    note = models.TextField(blank=True)
    tags = models.ManyToManyField('Tag', blank=True, )

    def __str__(self):
        return self.title


def document_image_file_path(instance, filename):
    """Generate file path for new document image"""
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'
    return os.path.join(f'uploads/document/{instance.document.id}', filename)


class DocumentImage(models.Model):
    """Image of document object"""
    document = models.ForeignKey(
        Document, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=document_image_file_path)

    def __str__(self):
        return f'{self.document.title}-{self.id}'
