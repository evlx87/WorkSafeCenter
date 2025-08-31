from django.db import models

from organization.models import Department, Position


# Create your models here.
class Employee(models.Model):
    first_name = models.CharField(max_length=100, verbose_name="Имя")
    last_name = models.CharField(max_length=100, verbose_name="Фамилия")
    middle_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Отчество")
    position = models.ForeignKey(
        Position,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Должность")
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Отдел")
    birth_date = models.DateField(verbose_name="Дата рождения")
    hire_date = models.DateField(verbose_name="Дата найма")
    medical_check_date = models.DateField(
        null=True, blank=True, verbose_name="Дата последнего медосмотра")
    safety_training_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Дата последнего инструктажа по охране труда")
    email = models.EmailField(unique=True, verbose_name="Email")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    def __str__(self):
        return f"{self.last_name} {self.first_name} {self.middle_name}"

    class Meta:
        verbose_name = "Работник"
        verbose_name_plural = "Работники"
        ordering = ['last_name', 'first_name']
