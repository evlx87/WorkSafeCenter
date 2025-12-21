from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from medical_checks.models import MedicalCheck
from notifications.models import Notification
from safety_trainings.models import SafetyTraining


class Command(BaseCommand):
    help = 'Генерирует уведомления о приближающихся медосмотрах и инструктажах.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS(
            'Начинаем генерацию уведомлений...'))

        # Определяем временной горизонт для уведомлений (например, за 30 дней)
        notification_period_days = 30
        today = timezone.now().date()
        future_date = today + timedelta(days=notification_period_days)
        danger_zone = today + timedelta(days=60)

        created_count = 0

        # --- 1. Проверка предстоящих медосмотров ---
        upcoming_checks = MedicalCheck.objects.filter(
            next_check_date__gte=today,
            next_check_date__lte=future_date,
            employee__is_active=True
        ).select_related('employee')

        self.stdout.write(
            f'Найдено {
                upcoming_checks.count()} приближающихся медосмотров.')

        for check in upcoming_checks:
            message = (
                f"Приближается срок очередного медосмотра для сотрудника {
                    check.employee}. " f"Дата следующего осмотра: {
                    check.next_check_date.strftime('%d.%m.%Y')}.")

            # Используем get_or_create, чтобы не создавать дубликаты
            # уведомлений
            notification, created = Notification.objects.get_or_create(
                employee=check.employee,
                notification_type='MEDICAL',
                message=message,
                # is_sent по умолчанию False, но для ясности укажем
                defaults={'is_sent': False}
            )

            if created:
                created_count += 1
                self.stdout.write(
                    f'  - Создано уведомление о медосмотре для {check.employee}.')

        # --- 2. Проверка предстоящих инструктажей ---
        upcoming_trainings = SafetyTraining.objects.filter(
            next_training_date__gte=today,
            next_training_date__lte=future_date,
            employee__is_active=True
        ).select_related('employee')

        self.stdout.write(
            f'Найдено {
                upcoming_trainings.count()} приближающихся инструктажей.')

        for training in upcoming_trainings:
            message = (
                f"Приближается срок очередного инструктажа ({
                    training.get_category_display()}) " f"для сотрудника {
                    training.employee}. " f"Дата следующего инструктажа: {
                    training.next_training_date.strftime('%d.%m.%Y')}.")

            notification, created = Notification.objects.get_or_create(
                employee=training.employee,
                notification_type='TRAINING',
                message=message,
                defaults={'is_sent': False}
            )

            if created:
                created_count += 1
                self.stdout.write(
                    f'  - Создано уведомление об инструктаже для {training.employee}.')

        souts_to_renew = SOUTAssessment.objects.filter(
            next_assessment_date__lte=danger_zone)

        for sout in souts_to_renew:
            Notification.objects.get_or_create(
                message=f"Требуется плановая СОУТ для РМ №{
                    sout.workplace.number}. Срок до {
                    sout.next_assessment_date}",
                # ... остальные поля ...
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nГенерация завершена. Создано {created_count} новых уведомлений.'))
