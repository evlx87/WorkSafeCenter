from django.db import models
from django.utils import timezone

from employees.models import Employee


# Create your models here.
class Category(models.Model): # Сначала категория
    CATEGORY_CHOICES = (
        ('FIRE', 'Пожарная безопасность'),
        ('ELECTRO', 'Электробезопасность'),
        ('HYGIENE', 'Гигиена и санитария'),
        ('HEIGHT', 'Работы на высоте'),
        ('OFFICE', 'Офисная работа'),
        ('OTHER', 'Прочее'),
    )

    name = models.CharField("Название категории", max_length=100, choices=CATEGORY_CHOICES)

    class Meta:
        verbose_name = "Категория документов"
        verbose_name_plural = "Категории документов"
    def __str__(self):
        return self.name


class Document(models.Model):
    DOCUMENT_TYPES = (
        ('FEDERAL', 'Нормативно-правовой акт (РФ)'),
        ('LOCAL', 'Локальный нормативный акт (Организация)'),
        ('INSTRUCTION', 'Инструкция по ОТ'),
        ('ORDER', 'Приказ/Распоряжение'),
        ('CERTIFICATE', 'Сертификат/Удостоверение'),
    )

    title = models.CharField(max_length=200, verbose_name="Название")
    document_type = models.CharField(
        max_length=20,
        choices=DOCUMENT_TYPES,
        verbose_name="Тип документа")
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Категория")
    file = models.FileField(
        upload_to='documents/',
        verbose_name="Файл",
        null=True,
        blank=True)
    external_link = models.URLField(
        verbose_name="Ссылка на ресурс",
        null=True,
        blank=True,
        help_text="Например, на Консультант+")
    # Поля для контроля сроков (важно для ЛНА и инструкций)
    end_date = models.DateField(
        verbose_name="Срок действия до",
        null=True,
        blank=True)
    # Оставляем связь с сотрудником для персональных документов
    employee = models.ForeignKey(
        Employee,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        verbose_name="Работник")
    upload_date = models.DateField(
        auto_now_add=True,
        verbose_name="Дата загрузки")

    class Meta:
        verbose_name = "Документ"
        verbose_name_plural = "Документы"

    def __str__(self):
        return self.title

    @property
    def is_overdue(self):
        if self.end_date:
            return self.end_date < timezone.now().date()
        return False
