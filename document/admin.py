from django.contrib import admin
from document import models
# Register your models here.

admin.site.register(models.Document)
admin.site.register(models.Tag)
admin.site.register(models.DocumentImage)
