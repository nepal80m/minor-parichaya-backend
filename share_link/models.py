import os
import uuid
from django.conf import settings
from django.db import models
from document.models import Document, DocumentImage
from django.utils import timezone


class ShareLink(models.Model):
    """Share link"""
    id = models.UUIDField(primary_key=True,
                          default=uuid.uuid4, editable=False, auto_created=True, unique=True,)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL,
                               on_delete=models.CASCADE)

    created_on = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateTimeField(
        default=timezone.now()+timezone.timedelta(days=7))


class SharedDocument(models.Model):
    """Shared Identity Document"""

    # user = models.ForeignKey(settings.AUTH_USER_MODEL,
    #                          on_delete=models.CASCADE)
    share_link = models.ForeignKey(
        ShareLink, on_delete=models.CASCADE, related_name='documents', )
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.title


def document_image_file_path(instance, filename):
    """Generate file path for new document image"""
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'
    return os.path.join(f'uploads/shared_document/{instance.document.id}', filename)


class SharedDocumentImage(models.Model):
    """Image of document object"""
    document = models.ForeignKey(
        SharedDocument, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=document_image_file_path)

    def __str__(self):
        return f'{self.document.title}-{self.id}'
