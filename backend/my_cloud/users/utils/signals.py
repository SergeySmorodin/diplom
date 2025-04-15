import logging
from django.contrib.sessions.models import Session
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Session)
def log_session_start(sender, instance, created, **kwargs):
    if created:
        user_id = instance.get_decoded().get('_auth_user_id', 'не аутентифицирован')
        logger.info(f"Сессия начата: {instance.session_key}, Пользователь: {user_id}")

@receiver(post_delete, sender=Session)
def log_session_end(sender, instance, **kwargs):
    user_id = instance.get_decoded().get('_auth_user_id', 'не аутентифицирован')
    logger.info(f"Сессия завершена: {instance.session_key}, Пользователь: {user_id}")