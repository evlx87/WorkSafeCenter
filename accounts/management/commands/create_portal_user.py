from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from accounts.models import UserProfile
import getpass


class Command(BaseCommand):
    help = 'Создает пользователя портала и привязывает его к группам доступа'

    def handle(self, *args, **options):
        username = input('Введите логин: ')
        password = getpass.getpass('Введите пароль: ')

        # Создаем пользователя
        user, created = User.objects.get_or_create(username=username)
        user.set_password(password)
        user.is_staff = True  # Чтобы мог зайти в админку, если нужно
        user.save()

        # Создаем профиль, если его нет
        UserProfile.objects.get_or_create(user=user)

        self.stdout.write(
            self.style.SUCCESS(
                f'Пользователь {username} успешно создан.'))
        self.stdout.write(
            'Теперь вы можете настроить его права и сгенерировать ключи в админке.')
