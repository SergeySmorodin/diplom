from django.core.exceptions import ValidationError
import logging


logger = logging.getLogger(__name__)

def validate_file_extension(uploaded_file):
    allowed_extensions = ['.txt', '.pdf', '.jpg', '.png', '.docx', '.xlsx']
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(f"Недопустимое расширение файла: {ext}")
    

