from django.db import models
from django.db import models
from django.utils import timezone
from datetime import timedelta
from organization.models import Position, Site


# Create your models here.
class Workplace(models.Model):
    """Рабочее место — основа для СОУТ и Рисков"""
    number = models.CharField(
        "Индивидуальный номер РМ",
        max_length=50,
        unique=True)
    position = models.ForeignKey(
        Position,
        on_delete=models.CASCADE,
        verbose_name="Должность по штатному")
    site = models.ForeignKey(
        Site,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Площадка/Цех")

    class Meta:
        verbose_name = "Рабочее место"
        verbose_name_plural = "Рабочие места"

    def __str__(self):
        return f"РМ №{self.number} ({self.position.name})"

    def get_current_sout(self):
        """Возвращает последнюю проведенную оценку."""
        return self.sout_assessments.order_by('-assessment_date').first()

    @property
    def sout_status(self):
        """Определяет статус СОУТ для рабочего места."""
        current = self.get_current_sout()
        if not current:
            return 'not_conducted'  # Не проводилась

        today = timezone.now().date()
        if current.next_assessment_date <= today:
            return 'expired'  # Просрочена
        elif current.next_assessment_date <= today + timedelta(days=90):
            return 'warning'  # Срок подходит (за 3 месяца)
        return 'valid'  # Актуальна


class SOUTAssessment(models.Model):
    """Блок СОУТ"""
    CLASS_CHOICES = [
        ('1', '1 (Оптимальный)'),
        ('2', '2 (Допустимый)'),
        ('3.1', '3.1 (Вредный 1 ст.)'),
        ('3.2', '3.2 (Вредный 2 ст.)'),
        ('3.3', '3.3 (Вредный 3 ст.)'),
        ('3.4', '3.4 (Вредный 4 ст.)'),
        ('4', '4 (Опасный)'),
    ]

    workplace = models.OneToOneField(
        Workplace,
        on_delete=models.CASCADE,
        related_name='sout',
        verbose_name="Рабочее место")
    assessment_date = models.DateField("Дата проведения СОУТ")
    next_assessment_date = models.DateField("Дата следующей оценки")
    class_conditions = models.CharField(
        "Класс условий труда",
        max_length=5,
        choices=CLASS_CHOICES)
    report_number = models.CharField("Номер отчета", max_length=100)
    file = models.FileField(
        "Скан карты СОУТ",
        upload_to='sout/reports/',
        blank=True,
        null=True)

    def save(self, *args, **kwargs):
        # Автоматический расчет следующей даты (обычно через 5 лет),
        # если она не введена вручную
        if not self.next_assessment_date and self.assessment_date:
            self.next_assessment_date = self.assessment_date + timedelta(days=5 * 365)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Результат СОУТ"
        verbose_name_plural = "Результаты СОУТ"


class RiskAssessment(models.Model):
    """Блок Профессиональных рисков"""
    LEVEL_CHOICES = [
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
        ('critical', 'Критический'),
    ]

    workplace = models.ForeignKey(
        Workplace,
        on_delete=models.CASCADE,
        related_name='risks',
        verbose_name="Рабочее место")
    hazard_source = models.CharField("Источник опасности", max_length=255)
    event_description = models.TextField("Опасное событие")
    risk_level = models.CharField(
        "Уровень риска",
        max_length=10,
        choices=LEVEL_CHOICES)
    control_measures = models.TextField("Меры управления риском")
    last_update = models.DateField("Дата последней оценки", auto_now=True)

    class Meta:
        verbose_name = "Оценка риска"
        verbose_name_plural = "Оценка рисков"
