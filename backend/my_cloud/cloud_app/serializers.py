from rest_framework import serializers
from .models import File, Folder
import os
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import PermissionDenied
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils import timezone
import uuid
from cloud_app.utils.file_validators import validate_file_extension
from . import services

class FileListSerializer(serializers.ModelSerializer):
    full_path = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = File
        fields = [
            'id', 
            'original_name', 
            'size', 
            'upload_date', 
            'last_download_date', 
            'comment', 
            'full_path',
            'file_url',
            'public_link'
        ]
    
    def get_full_path(self, obj):
        return obj.get_full_path()
    
    def get_file_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.file_path.url)
        return None

class FileUploadSerializer(serializers.ModelSerializer):
    file = serializers.FileField(
        write_only=True,
        validators=[validate_file_extension],
        help_text=_("Файл для загрузки")
    )
    folder = serializers.PrimaryKeyRelatedField(
        queryset=Folder.objects.all(),
        required=False,
        allow_null=True,
        help_text=_("ID папки для загрузки файла")
    )
    
    class Meta:
        model = File
        fields = ['file', 'comment', 'folder']
    
    def validate(self, attrs):
        user = self.context['request'].user
        folder = attrs.get('folder')
        
        if folder and folder.owner != user:
            raise PermissionDenied(_("У вас нет прав на доступ к этой папке"))
        
        file = attrs['file']
        original_name = file.name

        if File.objects.filter(
            owner=user, 
            folder=folder, 
            original_name=original_name
        ).exists():
            raise ValidationError({
                "file": _("Файл с таким именем уже существует в указанной папке")
            })
        
        return attrs
    
    def create(self, validated_data):
        user = self.context['request'].user
        uploaded_file = validated_data['file']
        comment = validated_data.get('comment', '')
        folder = validated_data.get('folder')
        
        return services.create_file_record(
            user=user,
            uploaded_file=uploaded_file,
            comment=comment,
            folder=folder
        )

class FileDeleteSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=File.objects.all(),
        help_text=_("ID файла для удаления")
    )
    
    def validate_id(self, value):
        user = self.context['request'].user
        if value.owner != user:
            raise PermissionDenied(_("Вы не можете удалить этот файл"))
        return value
    
class FileRenameSerializer(serializers.ModelSerializer):
    new_name = serializers.CharField(
        max_length=255,
        help_text=_("Новое имя файла")
    )
    
    class Meta:
        model = File
        fields = ['id', 'new_name']
    
    def validate(self, attrs):
        user = self.context['request'].user
        instance = self.instance
        
        if instance.owner != user:
            raise PermissionDenied(_("Вы не можете переименовать этот файл"))
        
        new_name = attrs['new_name']
        
        if File.objects.filter(
            owner=user, 
            folder=instance.folder, 
            original_name=new_name
        ).exclude(id=instance.id).exists():
            raise ValidationError({
                "new_name": _("Файл с таким именем уже существует в этой папке")
            })
        
        return attrs
    
    def update(self, instance, validated_data):
        instance.original_name = validated_data['new_name']
        instance.save()
        return instance

class FileUpdateCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ['id', 'comment']
    
    def validate_id(self, value):
        user = self.context['request'].user
        if value.owner != user:
            raise PermissionDenied(_("Вы не можете изменить комментарий к этому файлу"))
        return value

class FileDownloadSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=File.objects.all(),
        help_text=_("ID файла для скачивания")
    )
    
    def validate_id(self, value):
        user = self.context['request'].user
        if value.owner != user:
            raise PermissionDenied(_("Вы не можете скачать этот файл"))
        
        value.update_download_date()
        return value

class FilePublicLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ['id', 'public_link']
        read_only_fields = ['public_link']
    
    def validate_id(self, value):
        user = self.context['request'].user
        if value.owner != user:
            raise PermissionDenied(_("Вы не можете получить публичную ссылку для этого файла"))
        return value
    
    def update(self, instance, validated_data):
        instance.public_link = uuid.uuid4()
        instance.save()
        return instance

class FileDownloadByLinkSerializer(serializers.Serializer):
    public_link = serializers.UUIDField(
        help_text=_("Публичная ссылка для скачивания файла")
    )
    
    def validate_public_link(self, value):
        try:
            file = File.objects.get(public_link=value)
            file.update_download_date()
            return file
        except File.DoesNotExist:
            raise ValidationError(_("Файл с такой публичной ссылкой не найден"))

class FolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Folder
        fields = ['id', 'name', 'parent', 'created_at']
    
    def validate(self, attrs):
        user = self.context['request'].user
        parent = attrs.get('parent')
        
        if parent and parent.owner != user:
            raise PermissionDenied(_("У вас нет прав на доступ к этой папке"))
        
        name = attrs['name']
        
        if Folder.objects.filter(
            owner=user, 
            parent=parent, 
            name=name
        ).exists():
            raise ValidationError({
                "name": _("Папка с таким именем уже существует в указанной родительской папке")
            })
        
        return attrs
    
    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)

class FolderWithFilesSerializer(FolderSerializer):
    files = FileListSerializer(many=True, read_only=True)
    children = serializers.SerializerMethodField()
    
    class Meta(FolderSerializer.Meta):
        fields = FolderSerializer.Meta.fields + ['files', 'children']
    
    def get_children(self, obj):
        return FolderWithFilesSerializer(
            obj.get_children(), 
            many=True, 
            context=self.context
        ).data