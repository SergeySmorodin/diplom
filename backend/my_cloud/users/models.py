from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, password, **extra_fields):
        if not email:
            raise ValueError(_('Email должен быть указан'))
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email, password, **extra_fields):
        extra_fields.setdefault("is_admin", True)
        return self.create_user(username, email, password, **extra_fields)


class User(AbstractUser):
    objects = CustomUserManager()
    email = models.EmailField(_('Email'), unique=True, blank=False)
    full_name = models.CharField(_('Полное имя'), max_length=255, blank=True)
    is_admin = models.BooleanField(_('Администратор'), default=False)
    storage_path = models.CharField(
        _('Путь к хранилищу'), 
        max_length=255, 
        unique=True, 
        blank=True
    )    

    def save(self, *args, **kwargs):
        if not self.storage_path:
            self.storage_path = f'user_{self.username}'
        self.email = self.email.lower()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('Пользователь')
        verbose_name_plural = _('Пользователи')

    def __str__(self):
        return f'{self.username} ({self.email})'