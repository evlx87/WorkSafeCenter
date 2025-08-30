from django.db import models

from employees.models import Employee


# Create your models here.
class SafetyTraining(models.Model):
    TRAINING_TYPES = (
        ('INTRO', 'Вводный'),
        ('PRIMARY', 'Первичный'),
        ('REPEAT', 'Повторный'),
        ('UNSCHEDULED', 'Внеплановый'),
    )
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name="Работник")
    training_type = models.CharField(max_length=20, choices=TRAINING_TYPES, verbose_name="Тип инструктажа")
    training_date = models.DateField(verbose_name="Дата проведения")
    next_training_date = models.DateField(null=True, blank=True, verbose_name="Дата следующего инструктажа")
    instructor = models.CharField(max_length=200, verbose_name="Инструктор")

    class Meta:
        verbose_name = "Инструктаж"
        verbose_name_plural = "Инструктажи"