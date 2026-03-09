from dateutil.relativedelta import relativedelta
from django.db import models
from django.utils import timezone

from .validators import validate_pdf_or_image


# Create your models here.
class TrainingCategory(models.Model):
    """Единый справочник категорий обучения"""
    # Основные категории
    SAFETY = 'SAFETY'
    FIRE = 'FIRE'
    FIRST_AID = 'FIRST_AID'
    ELECTRICAL = 'ELECTRICAL'
    CIVIL_DEFENSE = 'CIVIL_DEFENSE'  # Гражданская оборона
    ROAD_SAFETY = 'ROAD_SAFETY'  # Безопасность дорожного движения
    WORKING_HEIGHT = 'WORKING_HEIGHT'
    ANTITERROR = 'ANTITERROR'
    ENVIRONMENTAL = 'ENVIRONMENTAL'  # Экологическая безопасность
    OTHER = 'OTHER'

    CATEGORY_CHOICES = [
        (SAFETY, 'Охрана труда'),
        (FIRE, 'Пожарная безопасность'),
        (FIRST_AID, 'Первая помощь'),
        (ELECTRICAL, 'Электробезопасность'),
        (CIVIL_DEFENSE, 'Гражданская оборона'),
        (ROAD_SAFETY, 'Безопасность дорожного движения'),
        (WORKING_HEIGHT, 'Работы на высоте'),
        (ANTITERROR, 'Антитеррористическая защищенность'),
        (ENVIRONMENTAL, 'Экологическая безопасность'),
        (OTHER, 'Другое'),
    ]

    code = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        unique=True,
        verbose_name="Код категории"
    )
    name = models.CharField(
        max_length=200,
        verbose_name="Название категории"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Описание"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активна"
    )

    class Meta:
        verbose_name = "Категория обучения"
        verbose_name_plural = "Категории обучения"
        ordering = ['name']

    def __str__(self):
        return self.name


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


class TrainingCenter(models.Model):
    """Внутренний реестр учебных центров, где обучались сотрудники"""
    name = models.CharField(max_length=255,
                            verbose_name="Название учебного центра")
    inn = models.CharField(max_length=12, blank=True, verbose_name="ИНН")
    address = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Адрес")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    email = models.EmailField(blank=True, verbose_name="Email")
    website = models.URLField(blank=True, verbose_name="Сайт")
    license_number = models.CharField(
        max_length=100, blank=True, verbose_name="Лицензия №")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Учебный центр"
        verbose_name_plural = "Учебные центры"
        ordering = ['name']

    def __str__(self):
        return self.name


class Internship(models.Model):
    """Стажировка на рабочем месте (только для рабочих профессий)"""
    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='internships',
        verbose_name="Сотрудник"
    )
    workplace = models.ForeignKey(
        'assessments.Workplace',
        on_delete=models.PROTECT,
        verbose_name="Рабочее место"
    )
    supervisor = models.ForeignKey(
        'employees.Employee',
        on_delete=models.PROTECT,
        related_name='supervised_internships',
        verbose_name="Руководитель стажировки",
        limit_choices_to={'is_executive': True}
    )
    start_date = models.DateField(verbose_name="Дата начала")
    end_date = models.DateField(verbose_name="Дата окончания")
    duration_days = models.PositiveIntegerField(
        verbose_name="Продолжительность (дней)")
    program_description = models.TextField(verbose_name="Программа стажировки")
    is_completed = models.BooleanField(default=False, verbose_name="Завершена")
    final_assessment = models.TextField(verbose_name="Итоговая оценка")
    document_scan = models.FileField(
        upload_to='internships/',
        null=True,
        blank=True,
        verbose_name="Скан документа о стажировке",
        validators=[validate_pdf_or_image]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Стажировка"
        verbose_name_plural = "Стажировки"
        ordering = ['-start_date']

    def __str__(self):
        return f"Стажировка {
            self.employee} ({
            self.start_date} - {
            self.end_date})"

    def clean(self):
        from django.core.exceptions import ValidationError
        # Проверка: только для рабочих профессий
        if self.employee.position and 'рабоч' in self.employee.position.name.lower():
            pass  # OK
        else:
            # Можно добавить предупреждение, но не блокировать
            pass

        # Проверка дат
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError(
                'Дата окончания не может быть раньше даты начала')


class TrainingProgram(models.Model):
    """Программа обучения"""
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name="Наименование программы")
    category = models.ForeignKey(
        TrainingCategory,
        on_delete=models.PROTECT,
        verbose_name="Категория")
    hours = models.PositiveIntegerField(
        verbose_name="Количество часов")
    frequency_months = models.PositiveIntegerField(
        default=0,
        verbose_name="Периодичность (в месяцах)",
        help_text="0 - если повторное обучение не требуется")
    is_mandatory = models.BooleanField(
        default=False,
        verbose_name="Обязательна для всех сотрудников")
    target_positions = models.ManyToManyField(
        'organization.Position',
        blank=True,
        verbose_name="Целевые должности",
        help_text="Если не обязательна для всех, укажите для каких должностей")
    description = models.TextField(
        blank=True,
        verbose_name="Описание программы")

    class Meta:
        verbose_name = "Программа обучения"
        verbose_name_plural = "Программы обучения"
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} ({self.category.name})"


class ElectricalSafetyGroup(models.Model):
    """Группы по электробезопасности"""

    GROUP_CHOICES = [
        (1, 'I группа'),
        (2, 'II группа'),
        (3, 'III группа'),
        (4, 'IV группа'),
        (5, 'V группа'),
    ]

    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        verbose_name="Сотрудник"
    )
    group_number = models.PositiveSmallIntegerField(
        choices=GROUP_CHOICES,
        verbose_name="Группа по электробезопасности"
    )
    assignment_date = models.DateField(
        verbose_name="Дата присвоения группы"
    )
    valid_until = models.DateField(
        verbose_name="Действительна до",
        null=True,
        blank=True
    )
    document_number = models.CharField(
        max_length=100,
        verbose_name="Номер протокола/удостоверения",
        blank=True
    )
    document_scan = models.FileField(
        upload_to='electrical_safety/',
        null=True,
        blank=True,
        verbose_name="Скан документа"
    )

    class Meta:
        verbose_name = "Группа по электробезопасности"
        verbose_name_plural = "Группы по электробезопасности"
        ordering = ['-assignment_date']
        unique_together = ['employee', 'group_number']

    def __str__(self):
        return f"{self.employee} - {self.get_group_number_display()}"


class Training(models.Model):
    """Запись о прохождении обучения сотрудником"""

    DOCUMENT_TYPES = [
        ('PROTOCOL', 'Протокол проверки знаний'),
        ('CERT_QUAL', 'Удостоверение о повышении квалификации'),
        ('CERT_COMPL', 'Сертификат о повышении квалификации'),
        ('DIPLOMA', 'Диплом о профессиональной переподготовке'),
    ]

    employee = models.ForeignKey(
        'employees.Employee',
        on_delete=models.CASCADE,
        related_name='trainings',
        verbose_name="Сотрудник"
    )
    program = models.ForeignKey(
        TrainingProgram,
        on_delete=models.PROTECT,
        verbose_name="Программа обучения"
    )
    raw_program_name = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="Название программы в документе",
        help_text="Отображается в карточке сотрудника для исторической точности")
    training_date = models.DateField(
        verbose_name="Дата прохождения"
    )
    next_training_date = models.DateField(
        verbose_name="Следующее обучение",
        null=True,
        blank=True,
        editable=False
    )
    document_type = models.CharField(
        max_length=20,
        choices=DOCUMENT_TYPES,
        verbose_name="Тип документа",
        null=True,
        blank=True
    )
    document_number = models.CharField(
        max_length=100,
        verbose_name="Номер документа",
        blank=True
    )
    document_scan = models.FileField(
        upload_to='training_documents/',
        null=True,
        blank=True,
        verbose_name="Скан документа"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Примечания"
    )
    training_center = models.ForeignKey(
        TrainingCenter,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Учебный центр"
    )

    # Для электробезопасности - группа по Приказу 811
    electrical_safety_group = models.CharField(
        max_length=10,
        blank=True,
        verbose_name="Группа по электробезопасности",
        choices=[
            ('I', 'I группа'),
            ('II', 'II группа'),
            ('III', 'III группа'),
            ('IV', 'IV группа'),
            ('V', 'V группа'),
        ]
    )

    class Meta:
        verbose_name = "Обучение"
        verbose_name_plural = "Обучения"
        ordering = ['-training_date']

    def __str__(self):
        return f"{self.employee} - {self.raw_program_name or self.program.name}"

    def save(self, *args, **kwargs):
        # Автоматический расчет даты следующего обучения
        if self.program.frequency_months > 0:
            from dateutil.relativedelta import relativedelta
            self.next_training_date = self.training_date + relativedelta(
                months=self.program.frequency_months
            )
        super().save(*args, **kwargs)


class Instruction(models.Model):
    instruction_type = models.ForeignKey(
        InstructionType,
        on_delete=models.PROTECT,
        related_name='instructions',
        verbose_name="Тип инструктажа"
    )

    employee = models.ForeignKey(
        'employees.Employee',
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
        'documents.Document',
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


class ProgramNameMapping(models.Model):
    """Сопоставление разных названий программ к стандартной программе"""

    variant_name = models.CharField(
        max_length=255,
        verbose_name="Вариант названия программы",
        help_text="Как программа называется в документе"
    )

    standard_program = models.ForeignKey(
        'TrainingProgram',
        on_delete=models.CASCADE,
        verbose_name="Стандартная программа",
        null=True,
        blank=True
    )

    training_category = models.CharField(
        max_length=20,
        choices=TrainingCategory.CATEGORY_CHOICES,
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
