from django.db import models

from employees.models import Employee


# Create your models here.
class Document(models.Model):
    DOCUMENT_TYPES = (
        ('INSTRUCTION', 'Инструкция'),
        ('ORDER', 'Приказ'),
        ('CERTIFICATE', 'Сертификат'),
    )
    title = models.CharField(max_length=200, verbose_name="Название")
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES, verbose_name="Тип документа")
    file = models.FileField(upload_to='documents/', verbose_name="Файл")
    upload_date = models.DateField(auto_now_add=True, verbose_name="Дата загрузки")
    employee = models.ForeignKey(Employee, null=True, blank=True, on_delete=models.CASCADE, verbose_name="Работник")

    class Meta:
        verbose_name = "Документ"
        verbose_name_plural = "Документы"