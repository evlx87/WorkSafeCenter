from django.db import models


class Department(models.Model):
    name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name="Название отдела")
    description = models.TextField(
        blank=True,
        verbose_name="Описание")
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        verbose_name="Вышестоящий отдел"
    )
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
    description = models.TextField(
        blank=True,
        verbose_name="Описание")
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
    name_full = models.CharField(
        max_length=255,
        verbose_name="Полное наименование организации (по Уставу)"
    )
    inn = models.CharField(
        max_length=12,
        verbose_name="ИНН",
        unique=True,
        blank=True
    )
    kpp = models.CharField(
        max_length=9,
        verbose_name="КПП",
        blank=True,
        default=""
    )
    ogrn = models.CharField(
        max_length=15,
        verbose_name="ОГРН",
        unique=True,
        blank=True
    )
    address_legal = models.CharField(
        max_length=255,
        verbose_name="Юридический адрес",
        blank=True
    )
    director = models.ForeignKey(
        'employees.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='directed_organization',
        verbose_name="Руководитель (ФИО)"
    )
    director_position = models.CharField(
        max_length=100,
        default="Директор",
        verbose_name="Должность руководителя (напр., И.О. Директора)"
    )
    safety_specialist = models.ForeignKey(
        'employees.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='safety_specialist_for',
        verbose_name="Специалист по охране труда (ФИО)"
    )
    safety_committee_members = models.ManyToManyField(
        'employees.Employee',
        related_name='safety_committee_membership',
        verbose_name="Состав комиссии по охране труда",
        blank=True
    )
    contact_phone = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="Контактный телефон"
    )

    def get_effective_director(self):
        """
        Возвращает назначенного директора. Если его нет, ищет И.о. директора.
        """
        # 1. Если директор явно назначен в этой модели
        if self.director:
            return self.director

        # 2. Ищем сотрудника со статусом "И.о. директора"
        from employees.models import Employee  # Локальный импорт для избежания цикла

        acting_director = Employee.objects.filter(
            is_acting_director=True,
            is_active=True  # Важно: только активные
        ).first()

        return acting_director

    def get_effective_safety_specialist(self):
        """
        Возвращает назначенного специалиста по ОТ. Если его нет, ищет по статусу.
        """
        if self.safety_specialist:
            return self.safety_specialist

        from employees.models import Employee

        specialist = Employee.objects.filter(
            is_safety_specialist=True,
            is_active=True
        ).first()

        return specialist

    def get_committee_members_including_chair(self):
        """
        Возвращает всех членов комиссии, включая председателя, из M2M и по статусу.
        """
        from employees.models import Employee

        # 1. Получаем членов, назначенных через M2M поле (если есть)
        members = list(self.safety_committee_members.filter(is_active=True))

        # 2. Ищем членов по статусам, если M2M поле пусто (или для дополнения)
        if not members:
            # Ищем всех, кто является членом или председателем
            committee_members_by_status = Employee.objects.filter(
                is_active=True
            ).filter(
                models.Q(is_safety_committee_member=True) |
                models.Q(is_safety_committee_chair=True)
            ).order_by('is_safety_committee_chair', 'last_name')

            return list(committee_members_by_status)

        return members

    class Meta:
        verbose_name = "Информация по ОТ организации"
        verbose_name_plural = "Информация по ОТ организаций"

    def __str__(self):
        return self.name_full

    @classmethod
    def load_organization(cls):
        """Получает или создает единственную запись организации (для синглтона)."""
        obj, created = cls.objects.get_or_create(
            pk=1,
            defaults={'name_full': 'Название организации'}
        )
        return obj


class Site(models.Model):
    organization = models.ForeignKey(
        OrganizationSafetyInfo,
        on_delete=models.CASCADE,
        verbose_name="Организация",
        related_name="sites")
    name = models.CharField(
        max_length=200,
        verbose_name="Название площадки")
    address = models.CharField(
        max_length=255,
        verbose_name="Адрес площадки")
    ot_responsible_name = models.CharField(
        max_length=200,
        verbose_name="ФИО ответственного за ОТ на площадке")

    class Meta:
        verbose_name = "Площадка"
        verbose_name_plural = "Площадки"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.address})"
