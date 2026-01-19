from django.core.management.base import BaseCommand

from assessments.services import check_sout_deadlines


class Command(BaseCommand):
    help = 'Проверка сроков СОУТ и генерация уведомлений'

    def handle(self, *args, **options):
        check_sout_deadlines()
        self.stdout.write(self.style.SUCCESS(
            'Проверка СОУТ завершена успешно'))
