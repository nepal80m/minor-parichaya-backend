from asyncore import write
from rest_framework import serializers
from document.models import Document, DocumentImage, Tag


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tag object."""
    class Meta:
        model = Tag
        fields = ("id", "name")
        read_only_fields = ('id',)


class DocumentImageSerializer(serializers.ModelSerializer):
    """Serializer for uploading image to document"""

    class Meta:
        model = DocumentImage
        fields = ('id', 'image')
        read_only_fields = ('id',)


class DocumentListTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("name",)


class DocumentListDocumentImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentImage
        fields = ("image",)


class DocumentListSerializer(serializers.ModelSerializer):
    """Serializer for document"""
    tags = DocumentListTagSerializer(many=True, read_only=True)
    images = DocumentListDocumentImageSerializer(many=True, read_only=True)

    class Meta:
        model = Document
        fields = ('id', 'title', 'note', 'images', 'tags')
        read_only_fields = ('id',)


class DocumentCreateSerializer(serializers.ModelSerializer):
    """Serializer for document"""
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all())

    class Meta:
        model = Document
        fields = ('id', 'title', 'note', 'tags')
        read_only_fields = ('id',)


class DocumentDetailSerializer(serializers.ModelSerializer):
    """Serializer for document"""
    tags = TagSerializer(many=True, read_only=True)
    images = DocumentImageSerializer(many=True, read_only=True)

    class Meta:
        model = Document
        fields = ('id', 'title', 'note', 'images', 'tags')
        read_only_fields = ('id',)

    # def create(self, validated_data):
    #     print(validated_data)
    #     # print(self.context['request'])
    #     # images = self.context['request'].FILES.getlist('images', None)

    #     tags = validated_data.pop('tags', None)
    #     document = Document.objects.create(**validated_data)
    #     document.tags.add()

    #     print(self.context['request'].FILES)

    #     # if images:
    #     #     [DocumentImage.objects.create(
    #     #         document=document, image=image) for image in images]
    #     # if tags:
    #     #     [Tag.objects.create(
    #     #         document=document, name=tag['name']) for tag in tags]
    #     return document

# class DocumentDetailSerializer(ViewDocumentSerializer):
#     """Serializer for document"""
#     tags = TagSerializer(many=True)
