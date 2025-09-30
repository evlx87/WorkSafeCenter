from dateutil.relativedelta import relativedelta
from django.db import models

from employees.models import Employee


# Create your models here.
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

    def save(self, *args, **kwargs):
        # Автоматический расчет даты следующего инструктажа
        self.next_training_date = None  # Сбрасываем дату по умолчанию

        # Инструктаж по электробезопасности - 1 раз в год
        if self.category == 'ELECTRICAL':
            self.next_training_date = self.training_date + \
                relativedelta(years=1)

        # Первичный/повторный по охране труда и пожарной безопасности - 1 раз в
        # 6 месяцев
        elif self.category in ['SAFETY', 'FIRE'] and self.training_type in ['PRIMARY', 'REPEAT']:
            self.next_training_date = self.training_date + \
                relativedelta(months=6)

        # Для вводных, внеплановых и целевых следующий инструктаж не
        # назначается автоматически

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Инструктаж"
        verbose_name_plural = "Инструктажи"
