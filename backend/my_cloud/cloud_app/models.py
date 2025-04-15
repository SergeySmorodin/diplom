import uuid
import os
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from mptt.models import MPTTModel, TreeForeignKey


def get_upload_path(instance, filename):
    path_components = []    
    if instance.folder:
        path_components = instance.folder.get_folder_path()    
    ext = os.path.splitext(filename)[1]
    unique_filename = f"{uuid.uuid4()}{ext}"    
    return os.path.join(
        settings.MEDIA_ROOT,
        str(instance.owner.id),
        *path_components,
        unique_filename
    )


class Folder(MPTTModel):
    name = models.CharField(
        _("Название папки"),
        max_length=255,
        help_text=_("Имя папки")
    )    
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name=_("Родительская папка")
    )    
    owner = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="folders",
        verbose_name=_("Владелец")
    )    
    created_at = models.DateTimeField(
        _("Дата создания"),
        auto_now_add=True
    )
        
    def get_folder_path(self):
        return [node.name for node in self.get_ancestors(include_self=True)]
    
    def __str__(self):
        return f"{self.name} ({self.owner})"
    
    class MPTTMeta:
        order_insertion_by = ['name']
    
    class Meta:
        verbose_name = _("Папка")
        verbose_name_plural = _("Папки")
        unique_together = ('owner', 'parent', 'name')


class File(models.Model):
    original_name = models.CharField(
        _("Оригинальное имя"),
        max_length=255,
        help_text=_("Исходное имя файла, загруженного пользователем")
    )

    size = models.PositiveIntegerField(
        _("Размер"),
        validators=[MinValueValidator(1)],
        help_text=_("Размер файла в байтах")
    )

    upload_date = models.DateTimeField(
        _("Дата загрузки"),
        auto_now_add=True,
        help_text=_("Дата и время, когда файл был загружен")
    )

    last_download_date = models.DateTimeField(
        _("Дата последнего скачивания"),
        blank=True,
        null=True,
        help_text=_("Дата и время последней загрузки файла")
    )

    comment = models.TextField(
        _("Комментарий"),
        blank=True,
        null=True,
        max_length=500,
        help_text=_("Комментарий к файлу (максимум 500 символов)")
    )

    file_path = models.FileField(
        _("Путь к файлу"),
        upload_to=get_upload_path,
        help_text=_("Путь к файлу на сервере")
    )

    public_link = models.UUIDField(
        _("Публичная ссылка"),
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text=_("Уникальная ссылка для внешнего доступа к файлу")
    )

    owner = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="files",
        verbose_name=_("Владелец"),
        help_text=_("Пользователь, которому принадлежит этот файл")
    )
    
    folder = models.ForeignKey(
        Folder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='files',
        verbose_name=_("Папка"),
        help_text=_("Папка, в которой находится файл")
    )
    
    def __str__(self):
        return f"{self.original_name} ({self.owner})"

    def save(self, *args, **kwargs):
        if not self.pk and self.file_path:
            self.size = self.file_path.size
        super().save(*args, **kwargs)

    def update_download_date(self):
        self.last_download_date = timezone.now()
        self.save(update_fields=['last_download_date'])
    
    def get_full_path(self):
        if not hasattr(self, '_cached_full_path'):
            if self.folder_id:
                self._cached_full_path = f"{'/'.join(self.folder.get_folder_path())}/{self.original_name}"
            else:
                self._cached_full_path = self.original_name
        return self._cached_full_path
    
    class Meta:
        verbose_name = _("Файл")
        verbose_name_plural = _("Файлы")
        ordering = ['-upload_date']
        constraints = [
            models.UniqueConstraint(
                fields=['owner', 'folder', 'original_name'],
                name='unique_file_name_per_folder',
                violation_error_message=_("Файл с таким именем уже существует в указанной папке")
            )
        ]