from django.db import models
from employees.models import Employee
from .validators import validate_pdf_extension


# Create your models here.
class Training(models.Model):
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='trainings',
        verbose_name="Работник"
    )
    program_name = models.CharField(
        max_length=255,
        verbose_name="Наименование программы обучения"
    )
    hours = models.PositiveIntegerField(
        verbose_name="Количество часов"
    )
    training_date = models.DateField(
        verbose_name="Дата прохождения"
    )
    frequency_months = models.PositiveIntegerField(
        verbose_name="Периодичность (в месяцах)",
        help_text="Через сколько месяцев необходимо повторное обучение."
    )
    document_scan = models.FileField(
        upload_to='training_documents/',
        validators=[validate_pdf_extension],
        verbose_name="Скан документа (.pdf)",
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = "Обучение"
        verbose_name_plural = "Обучения"
        ordering = ['-training_date']

    def __str__(self):
        return f"{self.program_name} - {self.employee}"
