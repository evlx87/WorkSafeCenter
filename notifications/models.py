from django.db import models

from employees.models import Employee


# Create your models here.
class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('MEDICAL', 'Медосмотр'),
        ('TRAINING', 'Инструктаж'),
    )
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name="Работник")
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, verbose_name="Тип уведомления")
    message = models.TextField(verbose_name="Сообщение")
    sent_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата отправки")
    is_sent = models.BooleanField(default=False, verbose_name="Отправлено")

    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"