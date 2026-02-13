from django.core.exceptions import ValidationError
import os


def validate_pdf_or_image(value):
    """Разрешаем ТОЛЬКО безопасные форматы: PDF, JPG, PNG"""
    ext = os.path.splitext(value.name)[1].lower()
    valid_extensions = ['.pdf', '.jpg', '.jpeg', '.png']

    if ext not in valid_extensions:
        raise ValidationError(
            f'Недопустимый формат файла. Разрешены: {
                ", ".join(valid_extensions)}')

    # Дополнительная проверка "магического числа" файла
    if ext == '.pdf' and value.read(4) != b'%PDF':
        raise ValidationError('Файл не является валидным PDF')
    value.seek(0)  # Возвращаем указатель в начало
