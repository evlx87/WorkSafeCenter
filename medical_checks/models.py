from django.db import models

from employees.models import Employee


# Create your models here.
class MedicalCheck(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name="Работник")
    check_date = models.DateField(verbose_name="Дата осмотра")
    next_check_date = models.DateField(null=True, blank=True, verbose_name="Дата следующего осмотра")
    result = models.TextField(blank=True, verbose_name="Результаты осмотра")
    is_valid = models.BooleanField(default=True, verbose_name="Действителен")

    class Meta:
        verbose_name = "Медосмотр"
        verbose_name_plural = "Медосмотры"