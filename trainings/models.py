from dateutil.relativedelta import relativedelta
from django.db import models
from django.utils import timezone

from documents.models import Document
from employees.models import Employee
from .validators import validate_pdf_or_image


# Create your models here.
class InstructionType(models.Model):
    CATEGORY_CHOICES = (
        ('SAFETY', 'Охрана труда'),
        ('ELECTRICAL', 'Электробезопасность'),
        ('FIRE', 'Пожарная безопасность'),
        ('OTHER', 'Другое'),
    )

    name = models.CharField(
        max_length=150,
        unique=True,
        verbose_name="Полное наименование типа инструктажа",
        help_text="Например: 'Первичный по охране труда', 'Повторный по электробезопасности'"
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        verbose_name="Категория"
    )
    type_name = models.CharField(
        max_length=50,
        verbose_name="Тип (Вводный, Повторный и т.д.)",
        help_text="Используется для подробного описания в отчетах."
    )
    frequency_months = models.PositiveIntegerField(
        default=0,
        verbose_name="Периодичность повтора (в месяцах)",
        help_text="0 - если повтор не требуется (Вводный, Внеплановый, Целевой).")

    class Meta:
        verbose_name = "Тип инструктажа"
        verbose_name_plural = "Типы инструктажей"
        unique_together = ('category', 'type_name')
        ordering = ['category', 'type_name']

    def __str__(self):
        return self.name


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
    DOCUMENT_TYPES = [
        ('PROTOCOL', 'Протокол проверки знаний'),
        ('CERT_QUAL', 'Удостоверение о повышении квалификации'),
        ('CERT_COMPL', 'Сертификат о повышении квалификации'),
        ('DIPLOMA', 'Диплом о профессиональной переподготовке'),
    ]

    TRAINING_CATEGORY = [
        ('SAFETY', 'Охрана труда'),
        ('FIRE', 'Пожарная безопасность'),
        ('FIRST_AID', 'Первая помощь'),
        ('ELECTRICAL', 'Электробезопасность'),
        ('ANTITERROR', 'Антитеррористическая защищенность'),
        ('OTHER', 'Другое'),
    ]

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
        validators=[validate_pdf_or_image],
        verbose_name="Скан документа (PDF/JPG/PNG)",
        null=True,
        blank=True
    )
    document_type = models.CharField(
        max_length=20,
        choices=DOCUMENT_TYPES,
        verbose_name="Тип документа",
        null=True,
        blank=True
    )

    program_name_in_document = models.CharField(
        max_length=255,
        verbose_name="Название программы в документе",
        blank=True,
        help_text="Как программа называется в удостоверении/сертификате"
    )
    document_number = models.CharField(
        max_length=100,
        verbose_name="Номер документа",
        blank=True
    )

    training_category = models.CharField(
        max_length=20,
        choices=TRAINING_CATEGORY,
        verbose_name="Категория обучения",
        default='OTHER'
    )

    class Meta:
        verbose_name = "Обучение"
        verbose_name_plural = "Обучения"
        ordering = ['-training_date']

    def __str__(self):
        return f"{self.program.name} - {self.employee}"


class Instruction(models.Model):
    instruction_type = models.ForeignKey(
        InstructionType,
        on_delete=models.PROTECT,
        related_name='instructions',
        verbose_name="Тип инструктажа"
    )

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='instructions',
        verbose_name="Работник")

    training_date = models.DateField(
        verbose_name="Дата проведения")

    next_training_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Дата следующего инструктажа")

    instructor = models.CharField(
        max_length=200,
        verbose_name="Инструктор")

    basis_document = models.ForeignKey(
        Document,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Документ-основание",
        help_text="Приказ, распоряжение или другой документ, на основании которого проводится инструктаж"
    )

    def calculate_next_training_date(self):
        """
        Рассчитывает дату следующего инструктажа, используя
        frequency_months из связанного InstructionType.
        """
        frequency = self.instruction_type.frequency_months

        if frequency > 0:
            return self.training_date + relativedelta(months=frequency)

        return None

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
        ordering = ['-training_date']

    def __str__(self):
        return f"{self.instruction_type.name} - {self.employee}"


# trainings/models.py
class ProgramNameMapping(models.Model):
    """Сопоставление разных названий программ к стандартной программе"""

    variant_name = models.CharField(
        max_length=255,
        verbose_name="Вариант названия программы",
        help_text="Как программа называется в документе"
    )

    standard_program = models.ForeignKey(
        TrainingProgram,
        on_delete=models.CASCADE,
        verbose_name="Стандартная программа",
        null=True,
        blank=True
    )

    training_category = models.CharField(
        max_length=20,
        choices=Training.TRAINING_CATEGORY,
        verbose_name="Категория обучения"
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Сопоставление названий программ"
        verbose_name_plural = "Сопоставления названий программ"
        unique_together = ['variant_name', 'training_category']

    def __str__(self):
        return f'"{
            self.variant_name}" → {
            self.get_training_category_display()}'
