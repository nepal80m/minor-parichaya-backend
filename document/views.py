from django.shortcuts import get_object_or_404
from rest_framework import views, viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from document import serializers
from document.models import Document, DocumentImage, Tag


class TagViewSet(viewsets.GenericViewSet,
                 mixins.ListModelMixin,
                 mixins.CreateModelMixin,
                 mixins.DestroyModelMixin,
                 #  mixins.RetrieveModelMixin,
                 #  mixins.UpdateModelMixin,
                 ):
    """Manage Tags in the database """
    queryset = Tag.objects.all()
    serializer_class = serializers.TagSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """Return object for the current authenticated use only"""
        return self.queryset.filter(user=self.request.user).order_by('-name')

    def perform_create(self, serializer):
        """Create a new tag"""
        serializer.save(user=self.request.user)


class DocumentViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.ListModelMixin, mixins.DestroyModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin):
    serializer_class = serializers.DocumentListSerializer
    queryset = Document.objects.all()
    permission_classes = (IsAuthenticated,)

    def perform_create(self, serializer):
        """Create a new recipe"""
        serializer.save(user=self.request.user)

    def get_queryset(self):
        """Retrieve the recipe for the authenticated user"""
        return self.queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        """Return appropriate serializer class"""
        # list,create,retrieve,update,partial_update,destroy
        if self.action == 'create':
            return serializers.DocumentCreateSerializer
        elif self.action == 'retrieve':
            return serializers.DocumentDetailSerializer
        elif self.action == 'upload_image':
            return serializers.DocumentImageSerializer
        return self.serializer_class

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        """Upload an image to a document"""
        document = self.get_object()
        request.data['document'] = document
        # print(request.data)
        serializer = self.get_serializer(
            data=request.data
        )

        if serializer.is_valid():
            serializer.save(document=document)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # return Response("Failed", status=status.HTTP_400_BAD_REQUEST)
