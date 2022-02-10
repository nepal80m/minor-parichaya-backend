from django.urls import path, include
from rest_framework.routers import DefaultRouter

from document import views

router = DefaultRouter()
router.register('tags', views.TagViewSet)
router.register('documents', views.DocumentViewSet)

app_name = 'document'

urlpatterns = [
    path('', include(router.urls)),
]
