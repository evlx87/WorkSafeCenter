import os
import secrets

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from accounts.models import UserProfile


class Command(BaseCommand):
    help = 'Генерирует файл-ключ для двухфакторной аутентификации пользователя'

    def add_arguments(self, parser):
        parser.add_argument(
            'username',
            type=str,
            help='Имя пользователя для ключей'
        )

    def handle(self, *args, **options):
        username = options['username']

        # Проверяем существование пользователя
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(
                f'Пользователь "{username}" не найден в системе.')

        crt_dir = os.path.join(settings.BASE_DIR, 'accounts', 'crt')
        if not os.path.exists(crt_dir):
            os.makedirs(crt_dir)

        try:
            # 1. Генерируем уникальный токен
            token = secrets.token_urlsafe(64)

            # 2. Сохраняем файл-ключ
            key_path = os.path.join(
                crt_dir, f"{username}.key")
            with open(key_path, "w", encoding='utf-8') as f:
                f.write(f"# Файл-ключ для входа в WorkSafeCenter\n")
                f.write(f"# НЕ ПЕРЕДАВАЙТЕ ЭТОТ ФАЙЛ ДРУГИМ ЛИЦАМ!\n")
                f.write(f"# Username: {username}\n")
                f.write(f"KEY={token}\n")

            # 3. Сохраняем токен в БД
            profile, created = UserProfile.objects.update_or_create(
                user=user,
                defaults={'auth_token_hash': token}
            )

            self.stdout.write(self.style.SUCCESS(
                f'Успешно: Файл-ключ для "{username}" создан.'))
            self.stdout.write(f'Файл-ключ: {key_path}')
            self.stdout.write(self.style.WARNING(
                'ВАЖНО: Передайте файл пользователю безопасным способом!'))

        except Exception as e:
            raise CommandError(f'Ошибка при генерации файла-ключа: {e}')
