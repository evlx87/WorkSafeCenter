from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from assessments.models import SOUTAssessment
from medical_checks.models import MedicalCheck
from notifications.models import Notification
from trainings.models import Instruction


class Command(BaseCommand):
    help = 'Генерирует уведомления о приближающихся медосмотрах и инструктажах.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS(
            'Начинаем генерацию уведомлений...'))

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

            notification, created = Notification.objects.get_or_create(
                employee=check.employee,
                notification_type='MEDICAL',
                message=message,
                defaults={'is_sent': False}
            )
            if created:
                created_count += 1
                self.stdout.write(
                    f'  - Создано уведомление о медосмотре для {check.employee}.')

        # --- 2. Проверка предстоящих инструктажей ---
        upcoming_trainings = Instruction.objects.filter(
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
                    training.instruction_type.name}) " f"для сотрудника {
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

        # --- 3. Проверка СОУТ ---
        souts_to_renew = SOUTAssessment.objects.filter(
            next_assessment_date__lte=danger_zone
        ).select_related('workplace')

        for sout in souts_to_renew:
            message = (
                f"Требуется плановая СОУТ для РМ №{sout.workplace.number}. "
                f"Срок до {sout.next_assessment_date.strftime('%d.%m.%Y')}"
            )

            # Создаем уведомление без привязки к сотруднику (общее уведомление)
            notification, created = Notification.objects.get_or_create(
                notification_type='OTHER',
                message=message,
                defaults={'is_sent': False}
            )
            if created:
                created_count += 1
                self.stdout.write(
                    f'  - Создано уведомление о СОУТ для РМ №{sout.workplace.number}.')

        self.stdout.write(
            self.style.SUCCESS(
                f'Генерация завершена. Создано {created_count} новых уведомлений.'))
