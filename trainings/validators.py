from django.core.exceptions import ValidationError
import os


def validate_pdf_extension(value):
    ext = os.path.splitext(value.name)[1]  # [0] returns path+filename
    valid_extensions = ['.pdf']
    if not ext.lower() in valid_extensions:
        raise ValidationError(
            'Неподдерживаемый тип файла. Разрешены только .pdf файлы.')
