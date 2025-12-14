from django.utils import timezone

from dateutil.relativedelta import relativedelta
from django.db import models

from documents.models import Document
from employees.models import Employee
from .validators import validate_pdf_extension


# Create your models here.
class TrainingProgram(models.Model):
    TRAINING_TYPES = (
        ('SAFETY', 'Охрана труда'),
        ('FIRE', 'Пожарная безопасность'),
        ('FIRST_AID', 'Первая помощь'),
        ('WORKING_HEIGHT', 'Работы на высоте'),
        ('OTHER', 'Другое'),
    )
    training_type = models.CharField(
        max_length=20,
        choices=TRAINING_TYPES,
        verbose_name="Вид обучения",
        default='SAFETY'
    )
    is_mandatory = models.BooleanField(
        default=True,
        verbose_name="Обязательность для всех",
        help_text="Если не обязательна, применяется только к указанным должностям.")
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
        default=0)

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

class SafetyTraining(models.Model):
    TRAINING_CATEGORIES = (
        ('SAFETY', 'Охрана труда'),
        ('ELECTRICAL', 'Электробезопасность'),
        ('FIRE', 'Пожарная безопасность'),
    )

    TRAINING_TYPES = (
        ('INTRO', 'Вводный'),
        ('PRIMARY', 'Первичный'),
        ('REPEAT', 'Повторный'),
        ('UNSCHEDULED', 'Внеплановый'),
        ('TARGETED', 'Целевой'),
    )

    category = models.CharField(
        max_length=20,
        choices=TRAINING_CATEGORIES,
        verbose_name="Категория инструктажа",
        default='SAFETY'
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        verbose_name="Работник")
    training_type = models.CharField(
        max_length=20,
        choices=TRAINING_TYPES,
        verbose_name="Тип инструктажа")
    training_date = models.DateField(
        verbose_name="Дата проведения")
    next_training_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Дата следующего инструктажа")
    instructor = models.CharField(
        max_length=200,
        verbose_name="Инструктор")
    local_act_details = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Основание для проведения (приказ, распоряжение)"
    )
    basis_document = models.ForeignKey(
        Document,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Документ-основание",
        help_text="Приказ, распоряжение или другой документ, на основании которого проводится инструктаж"
    )

    def calculate_next_training_date(self):
        """Рассчитывает дату следующего инструктажа на основе категории и типа."""
        # По умолчанию сбрасываем дату
        next_date = None

        # Инструктаж по электробезопасности - 1 раз в год
        if self.category == 'ELECTRICAL':
            next_date = self.training_date + relativedelta(years=1)

        # Первичный/повторный по охране труда и пожарной безопасности - 1 раз в 6 месяцев
        elif self.category in ['SAFETY', 'FIRE'] and self.training_type in ['PRIMARY', 'REPEAT']:
            next_date = self.training_date + relativedelta(months=6)

        # Для вводных, внеплановых, целевых - обычно бессрочно (None)
        # Если нужна другая логика, добавьте ее сюда

        return next_date

    @property
    def is_overdue(self):
        """Проверяет, просрочен ли инструктаж."""
        if self.next_training_date:
            return self.next_training_date < timezone.now().date()
        return False

    def save(self, *args, **kwargs):
        self.next_training_date = self.calculate_next_training_date()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Инструктаж"
        verbose_name_plural = "Инструктажи"