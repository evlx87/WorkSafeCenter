from django.db import models

# Create your models here.


class Department(models.Model):
    name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name="Название отдела")
    description = models.TextField(blank=True, verbose_name="Описание")
    head = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Руководитель")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Отдел"
        verbose_name_plural = "Отделы"
        ordering = ['name']


class Position(models.Model):
    name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name="Название должности")
    description = models.TextField(blank=True, verbose_name="Описание")
    department = models.ForeignKey(
        Department,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="Отдел")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Должность"
        verbose_name_plural = "Должности"
        ordering = ['name']
