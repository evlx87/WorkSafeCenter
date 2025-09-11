from django.db import models

from employees.models import Employee
from .validators import validate_pdf_extension


# Create your models here.
class TrainingProgram(models.Model):
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name="Наименование программы"
    )
    hours = models.PositiveIntegerField(
        verbose_name="Количество часов"
    )
    frequency_months = models.PositiveIntegerField(
        verbose_name="Периодичность (в месяцах)",
        help_text="Через сколько месяцев необходимо повторное обучение. 0 - если не требуется.",
        default=0
    )

    class Meta:
        verbose_name = "Программа обучения"
        verbose_name_plural = "Программы обучения"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.hours} ч.)"


class Training(models.Model):
    program = models.ForeignKey(
        TrainingProgram,
        on_delete=models.PROTECT,
        verbose_name="Программа обучения"
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='trainings',
        verbose_name="Работник"
    )
    training_date = models.DateField(
        verbose_name="Дата прохождения"
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
        return f"{self.program.name} - {self.employee}"
