import uuid
import os
from django.conf import settings
from .models import File
import logging


logger = logging.getLogger(__name__)

def generate_unique_filename(original_name):
    ext = os.path.splitext(original_name)[1]
    return f"{uuid.uuid4()}{ext}"

def save_file_to_storage(uploaded_file, user_id=None):
    unique_name = generate_unique_filename(uploaded_file.name)
    storage_path = f"user_{user_id}/{unique_name}" if user_id else unique_name
    full_path = os.path.join(settings.MEDIA_ROOT, storage_path)
    
    os.makedirs(os.dirname(full_path), exist_ok=True)
    with open(full_path, 'wb+') as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)
    
    return storage_path

def create_file_record(user, uploaded_file, comment="", folder=None):
    storage_path = save_file_to_storage(uploaded_file, user.id)
    return File.objects.create(
        original_name=uploaded_file.name,
        file_path=storage_path,
        size=uploaded_file.size,
        comment=comment,
        public_link=uuid.uuid4(),
        owner=user,
        folder=folder
    )

def delete_file_from_storage(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
    else:
        logger.warning(f"Файл {file_path} не найден при удалении.")