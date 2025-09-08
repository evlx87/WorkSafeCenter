from django.db import models


class Department(models.Model):
    name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name="Название отдела")
    description = models.TextField(blank=True, verbose_name="Описание")
    # Замените 'Employee' на строку 'employees.Employee'
    head = models.ForeignKey(
        'employees.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Руководитель",
        related_name='headed_department',
        limit_choices_to={'is_active': True}
    )

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


class OrganizationSafetyInfo(models.Model):
    school_name = models.CharField(
        max_length=200, verbose_name="Название школы")
    director_name = models.CharField(
        max_length=200, verbose_name="ФИО директора")
    ot_specialist_name = models.CharField(
        max_length=200, verbose_name="ФИО специалиста по охране труда")

    class Meta:
        verbose_name = "Информация по охране труда организации"
        verbose_name_plural = "Информация по охране труда организаций"

    def __str__(self):
        return self.school_name


class Site(models.Model):
    organization = models.ForeignKey(
        OrganizationSafetyInfo,
        on_delete=models.CASCADE,
        verbose_name="Организация",
        related_name="sites")
    name = models.CharField(max_length=200, verbose_name="Название площадки")
    address = models.CharField(max_length=255, verbose_name="Адрес площадки")
    ot_responsible_name = models.CharField(
        max_length=200, verbose_name="ФИО ответственного за ОТ на площадке")

    class Meta:
        verbose_name = "Площадка"
        verbose_name_plural = "Площадки"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.address})"
