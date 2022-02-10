import uuid
from django.conf import settings
from django.db import models
from document.models import Document, DocumentImage


class ShareLink(models.Model):
    id = models.UUIDField(primary_key=True,
                          default=uuid.uuid4, editable=False, auto_created=True, unique=True,)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL,
                               on_delete=models.CASCADE)
    expiry_date = models.DateField()
