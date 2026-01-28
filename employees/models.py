from django.db import models
from encrypted_model_fields.fields import EncryptedCharField, EncryptedEmailField

# Create your models here.
class Employee(models.Model):
    first_name = models.CharField(
        max_length=100,
        verbose_name="Имя")
    last_name = models.CharField(
        max_length=100,
        verbose_name="Фамилия")
    middle_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Отчество")
    position = models.ForeignKey(
        'organization.Position',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Должность")
    department = models.ForeignKey(
        'organization.Department',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Отдел")
    workplace = models.ForeignKey(
        'assessments.Workplace',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Рабочее место")
    birth_date = models.DateField(
        verbose_name="Дата рождения")
    hire_date = models.DateField(
        verbose_name="Дата найма")
    medical_check_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Дата последнего медосмотра")
    safety_training_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Дата последнего инструктажа по охране труда")
    email = EncryptedEmailField(
        unique=True,
        blank=True,
        null=True,
        verbose_name="Email")
    phone = EncryptedCharField(
        max_length=20,
        blank=True,
        verbose_name="Телефон")
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен")
    is_executive = models.BooleanField(
        default=False,
        verbose_name="Руководящий состав",
        help_text="Отметьте, если сотрудник относится к высшему руководству (например, директор, заместитель директора)."
    )
    on_parental_leave = models.BooleanField(
        default=False,
        verbose_name="В декретном отпуске")
    is_safety_specialist = models.BooleanField(
        default=False,
        verbose_name="Специалист по охране труда")
    is_safety_committee_member = models.BooleanField(
        default=False,
        verbose_name="Член комиссии по охране труда")
    is_safety_committee_chair = models.BooleanField(
        default=False,
        verbose_name="Председатель комиссии по охране труда")
    is_acting_director = models.BooleanField(
        default=False,
        verbose_name="И.о. директора")
    termination_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Дата увольнения")
    termination_order_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Номер приказа об увольнении")
    is_pedagogical_staff = models.BooleanField(
        default=False,
        verbose_name="Педагогический работник",
        help_text="Требуется для назначения обучения по Первой помощи.")
    exempt_from_safety_instruction = models.BooleanField(
        default=False,
        verbose_name="Освобожден от первичного инструктажа",
        help_text="Если отмечено, сотруднику требуется только Вводный инструктаж.")
    is_pedagogical = models.BooleanField(
        "Педагогический работник",
        default=False)
    is_executive = models.BooleanField(
        "Руководитель",
        default=False)

    def save(self, *args, **kwargs):
        if self.termination_date:
            self.is_active = False
        else:
            self.is_active = True
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.last_name} {self.first_name} {self.middle_name}"

    class Meta:
        verbose_name = "Работник"
        verbose_name_plural = "Работники"
        ordering = ['last_name', 'first_name']
