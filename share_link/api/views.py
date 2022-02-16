# from django.core.servers.basehttp import FileWrapper
import io
# import StringIO
import tempfile
import hmac
import secrets
from passlib.hash import pbkdf2_sha256
import zipfile
import os
from os.path import basename
from django.http import FileResponse
from wsgiref.util import FileWrapper
import mimetypes
from django.http import HttpResponse
from encrypted_files.base import EncryptedFile
from ..models import SharedDocumentImage
import os
import hashlib
from django.http import Http404
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.core.files.uploadhandler import MemoryFileUploadHandler, TemporaryFileUploadHandler
from encrypted_files.uploadhandler import EncryptedFileUploadHandler
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from rest_framework import authentication
from rest_framework import renderers
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer

from share_link.models import ShareLink, SharedDocument, SharedDocumentImage
from share_link.api.serializers import ShareLinkSerializer, SharedDocumentSerializer, SharedDocumentImageSerializer


class CreateShareLink(APIView):
    def post(self, request, format=None):
        serializer = ShareLinkSerializer(data=request.data)

        if serializer.is_valid():
            encryption_key = secrets.token_urlsafe(16)
            encryption_key_hash = pbkdf2_sha256.hash(encryption_key)
            serializer.save(encryption_key_hash=encryption_key_hash)
            context = serializer.data
            context['encryption_key'] = encryption_key
            return Response(context, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShareLinkDetail(APIView):
    def get(self, request, share_link_id, encryption_key, format=None):
        share_link = get_object_or_404(ShareLink, pk=share_link_id)

        is_key_correct = pbkdf2_sha256.verify(
            encryption_key, share_link.encryption_key_hash)
        if not is_key_correct:
            return Response({'detail': 'wrong decryption key.'},
                            status=status.HTTP_400_BAD_REQUEST)
        serializer = ShareLinkSerializer(share_link)
        context = serializer.data
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, share_link_id, encryption_key, format=None):
        share_link = get_object_or_404(ShareLink, pk=share_link_id)
        is_key_correct = pbkdf2_sha256.verify(
            encryption_key, share_link.encryption_key_hash)
        if not is_key_correct:
            return Response({'detail': 'wrong decryption key.'},
                            status=status.HTTP_400_BAD_REQUEST)
        serializer = ShareLinkSerializer(share_link, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, share_link_id, encryption_key, format=None):
        share_link = get_object_or_404(ShareLink, pk=share_link_id)
        is_key_correct = pbkdf2_sha256.verify(
            encryption_key, share_link.encryption_key_hash)
        if not is_key_correct:
            return Response({'detail': 'wrong decryption key.'},
                            status=status.HTTP_400_BAD_REQUEST)
        share_link.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AddSharedDocument(APIView):

    def post(self, request, share_link_id, encryption_key, format=None):
        share_link = get_object_or_404(ShareLink, pk=share_link_id)

        is_key_correct = pbkdf2_sha256.verify(
            encryption_key, share_link.encryption_key_hash)
        if not is_key_correct:
            return Response({'detail': 'wrong decryption key.'},
                            status=status.HTTP_400_BAD_REQUEST)

        key_string = hashlib.sha256(encryption_key.encode())
        byte_key = key_string.digest()

        request.upload_handlers = [
            EncryptedFileUploadHandler(request=request, key=byte_key),
            MemoryFileUploadHandler(request=request),
            TemporaryFileUploadHandler(request=request)
        ]
        serializer = SharedDocumentSerializer(
            data=request.data, context={'request': request})

        if serializer.is_valid():
            serializer.save(share_link=share_link)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def view_shared_document_image(request, shared_document_image_id, encryption_key):

    shared_document_image = get_object_or_404(
        SharedDocumentImage, pk=shared_document_image_id)

    is_key_correct = pbkdf2_sha256.verify(
        encryption_key, shared_document_image.document.share_link.encryption_key_hash)

    if not is_key_correct:
        raise Http404

    f = shared_document_image.image

    key_string = hashlib.sha256(encryption_key.encode())
    byte_key = key_string.digest()

    ef = EncryptedFile(f, key=byte_key)

    response = FileResponse(ef)

    return response


def download_shared_document_image(request, shared_document_image_id, encryption_key,):
    shared_document_image = get_object_or_404(
        SharedDocumentImage, pk=shared_document_image_id)

    is_key_correct = pbkdf2_sha256.verify(
        encryption_key, shared_document_image.document.share_link.encryption_key_hash)

    if not is_key_correct:
        raise Http404

    f = shared_document_image.image

    key_string = hashlib.sha256(encryption_key.encode())
    byte_key = key_string.digest()

    ef = EncryptedFile(f, key=byte_key)

    wrapper = FileWrapper(ef)

    content_type = mimetypes.guess_type(
        shared_document_image.filename)[0]
    response = HttpResponse(wrapper, content_type=content_type)
    # response['Content-Length'] = os.path.getsize(ef.name)
    response['Content-Disposition'] = f"attachment; filename={shared_document_image.filename}"
    return response


def download_document_wise_images(request, shared_document_id, encryption_key,):
    shared_document = get_object_or_404(
        SharedDocument, pk=shared_document_id)

    is_key_correct = pbkdf2_sha256.verify(
        encryption_key, shared_document.share_link.encryption_key_hash)

    if not is_key_correct:
        raise Http404
    key_string = hashlib.sha256(encryption_key.encode())
    byte_key = key_string.digest()

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for shared_document_image in shared_document.images.all():
            f = shared_document_image.image
            ef = EncryptedFile(f, key=byte_key)

            zip_file.writestr(shared_document_image.filename, ef.read())

        # for file_name, data in [('1.txt', io.BytesIO(b'111')), ('2.txt', io.BytesIO(b'222'))]:
        #     zip_file.writestr(file_name, data.getvalue())

    # for shared_document_image in shared_document.images.all():
    #     f = shared_document_image.image

    #     ef = EncryptedFile(f, key=byte_key)
    #     print(ef)

    #     wrapper = FileWrapper(ef)

    #     print(shared_document_image.filename)
    #     archive.writestr(shared_document_image.filename, ef.read())

    # content_type = mimetypes.guess_type(
    #     shared_document_image.filename)[0]
    for i in zip_file.infolist():
        print(i.filename, i.file_size)
    response = HttpResponse(
        zip_file, content_type="application/x-zip-compressed")
    response['Content-Disposition'] = f'attachment;filename={shared_document.title}.zip'
    # response['Content-Length'] = os.path.getsize(ef.name)
    # response['Content-Disposition'] = f"attachment; filename={shared_document_image.filename}"
    return response


class SharedDocumentDetail(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, share_link_id, shared_document_id, format=None):
        shared_document = get_object_or_404(
            SharedDocument, pk=shared_document_id, share_link__id=share_link_id)
        serializer = SharedDocumentSerializer(shared_document)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, share_link_id, shared_document_id, format=None):
        shared_document = get_object_or_404(
            SharedDocument, pk=shared_document_id, share_link__id=share_link_id)
        serializer = SharedDocumentSerializer(
            shared_document, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, share_link_id, shared_document_id, format=None):
        shared_document = get_object_or_404(
            SharedDocument, pk=shared_document_id, share_link__id=share_link_id)
        shared_document.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SharedDocumentImageList(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, share_link_id, shared_document_id, format=None):
        shared_document = get_object_or_404(
            SharedDocument, pk=shared_document_id, share_link__id=share_link_id)
        shared_document_images = shared_document.images.all()
        serializer = SharedDocumentImageSerializer(
            shared_document_images, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request,  share_link_id, shared_document_id, format=None):
        shared_document = get_object_or_404(
            SharedDocument, pk=shared_document_id, share_link__id=share_link_id)

        serializer = SharedDocumentImageSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(document=shared_document)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SharedDocumentImageDetail(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, share_link_id, shared_document_id, shared_document_image_id, format=None):
        shared_document_image = get_object_or_404(
            SharedDocumentImage, pk=shared_document_image_id, document__id=shared_document_id, document__share_link__id=share_link_id)
        serializer = SharedDocumentImageSerializer(shared_document_image)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, share_link_id, shared_document_id, shared_document_image_id, format=None):
        shared_document_image = get_object_or_404(
            SharedDocumentImage, pk=shared_document_image_id, document__id=shared_document_id, document__share_link__id=share_link_id)
        serializer = SharedDocumentImageSerializer(
            shared_document_image, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, share_link_id, shared_document_id, shared_document_image_id, format=None):
        shared_document_image = get_object_or_404(
            SharedDocument, pk=shared_document_image_id, document__id=shared_document_id, document__share_link__id=share_link_id)
        shared_document_image.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# @api_view(['GET'])
# def share_link_details_api(request, pk):
#     try:
#         share_link = ShareLink.objects.get(pk=pk)
#     except ShareLink.DoesNotExist():
#         return Response(status=status.HTTP_404_NOT_FOUND)
#     if request.method == 'GET':
#         serializer = ShareLinkSerializer(share_link)
#         return Response(serializer.data, status=status.HTTP_200_OK)


# @api_view(['PUT'])
# def share_link_update_api(request, pk):
#     try:
#         share_link = ShareLink.objects.get(pk=pk)
#     except ShareLink.DoesNotExist():
#         return Response(status=status.HTTP_404_NOT_FOUND)

#     if request.method == 'PUT':
#         serializer = ShareLinkSerializer(share_link, data=request.data)
#         data = {}
#         if serializer.is_valid():
#             serializer.save()
#             data['success'] = 'updated successfully'
#             return Response(data=data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# @api_view(['DELETE', ])
# def share_link_delete_api(request, pk):
#     try:
#         share_link = ShareLink.objects.get(pk=pk)
#     except ShareLink.DoesNotExist():
#         return Response(status=status.HTTP_404_NOT_FOUND)

#     if request.method == 'DELETE':
#         operation = share_link.delete()
#         data = {}
#         if operation:
#             data['success'] = 'delete successful'
#             return Response(data=data, status=status.HTTP_200_OK)
#         else:
#             data['failure'] = 'delete failed'
#             return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
