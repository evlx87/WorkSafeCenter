from django.db import models
from django.utils import timezone
from encrypted_model_fields.fields import EncryptedTextField

from employees.models import Employee


# Create your models here.
class MedicalCheck(models.Model):
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        verbose_name="Работник")
    check_date = models.DateField(verbose_name="Дата осмотра")
    next_check_date = models.DateField(
        null=True, blank=True, verbose_name="Дата следующего осмотра")
    result = EncryptedTextField(blank=True, verbose_name="Результаты осмотра")
    is_valid = models.BooleanField(default=True, verbose_name="Действителен")

    class Meta:
        verbose_name = "Медосмотр"
        verbose_name_plural = "Медосмотры"

    @property
    def is_overdue(self):
        """Проверяет, просрочен ли медосмотр."""
        if self.next_check_date:
            return self.next_check_date < timezone.now().date()
        return False

    @property
    def days_to_expire(self):
        """Количество дней до истечения срока."""
        if self.next_check_date:
            return (self.next_check_date - timezone.now().date()).days
        return None
