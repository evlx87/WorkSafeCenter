from django.db import models

from employees.models import Employee


# Create your models here.
class Incident(models.Model):
    INCIDENT_TYPES = (
        ('ACCIDENT', 'Несчастный случай'),
        ('VIOLATION', 'Нарушение'),
        ('NEAR_MISS', 'Потенциальный инцидент'),
    )
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name="Работник")
    incident_type = models.CharField(max_length=20, choices=INCIDENT_TYPES, verbose_name="Тип инцидента")
    incident_date = models.DateTimeField(verbose_name="Дата и время")
    description = models.TextField(verbose_name="Описание")
    actions_taken = models.TextField(blank=True, verbose_name="Принятые меры")

    class Meta:
        verbose_name = "Инцидент"
        verbose_name_plural = "Инциденты"