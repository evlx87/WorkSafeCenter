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

    # Проверка размера файла (макс. 10 МБ)
    if value.size > 10 * 1024 * 1024:
        raise ValidationError('Размер файла не должен превышать 10 МБ')

    # Дополнительная проверка "магического числа" файла
    if ext == '.pdf':
        header = value.read(4)
        value.seek(0)
        if header != b'%PDF':
            raise ValidationError('Файл не является валидным PDF')
