from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import File, Folder
from .serializers import (
    FileListSerializer,
    FileUploadSerializer,
    FileRenameSerializer,
    FileUpdateCommentSerializer,
    FilePublicLinkSerializer,
    FolderSerializer,
    FolderWithFilesSerializer
)
from django.shortcuts import get_object_or_404
from django.http import FileResponse
import os
import logging
from . import services


logger = logging.getLogger(__name__)

class FolderViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = FolderSerializer
    
    def get_queryset(self):
        return Folder.objects.filter(owner=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return FolderWithFilesSerializer
        return super().get_serializer_class()
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class FileUploadView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FileUploadSerializer

class FileListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FileListSerializer
    
    def get_queryset(self):
        folder_id = self.request.query_params.get('folder')
        queryset = File.objects.filter(owner=self.request.user)
        
        if folder_id:
            queryset = queryset.filter(folder_id=folder_id)
        
        return queryset

class FileDownloadView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    queryset = File.objects.all()
    
    def get(self, request, *args, **kwargs):
        file_obj = self.get_object()
        if file_obj.owner != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        
        response = FileResponse(file_obj.file_path)
        response['Content-Disposition'] = f'attachment; filename="{file_obj.original_name}"'
        return response

class FileDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = File.objects.all()
    
    def perform_destroy(self, instance):
        if instance.owner != self.request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        instance.file_path.delete()
        instance.delete()


class FileDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = File.objects.all()
    
    def perform_destroy(self, instance):
        if instance.owner != self.request.user:
            raise PermissionDenied("Нет прав на удаление файла")

        file_path = os.path.join(settings.MEDIA_ROOT, instance.file_path.name)
        services.delete_file_from_storage(file_path)
        instance.delete()

class FileRenameView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = File.objects.all()
    serializer_class = FileRenameSerializer
    
    def get_object(self):
        obj = get_object_or_404(File, pk=self.kwargs['pk'])
        if obj.owner != self.request.user:
            raise PermissionDenied("У вас нет прав на переименование этого файла")
        return obj

class FileUpdateCommentView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = File.objects.all()
    serializer_class = FileUpdateCommentSerializer
    
    def get_object(self):
        obj = get_object_or_404(File, pk=self.kwargs['pk'])
        if obj.owner != self.request.user:
            raise PermissionDenied("У вас нет прав на обновление комментария к этому файлу")
        return obj

class FilePublicLinkView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = File.objects.all()
    serializer_class = FilePublicLinkSerializer
    
    def get_object(self):
        obj = get_object_or_404(File, pk=self.kwargs['pk'])
        if obj.owner != self.request.user:
            raise PermissionDenied("У вас нет прав на создание ссылки для этого файла")
        return obj

class FileDownloadByLinkView(generics.RetrieveAPIView):
    queryset = File.objects.all()
    lookup_field = 'public_link'
    lookup_url_kwarg = 'public_link'
    
    def get(self, request, *args, **kwargs):
        file_obj = self.get_object()
        response = FileResponse(file_obj.file_path)
        response['Content-Disposition'] = f'attachment; filename="{file_obj.original_name}"'
        return response