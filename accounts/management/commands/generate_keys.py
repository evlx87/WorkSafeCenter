import hashlib
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
            help='Имя пользователя для генерации ключа')
        parser.add_argument(
            '--output-dir',
            type=str,
            default=None,
            help='Директория для сохранения файла-ключа (по умолчанию: <BASE_DIR>/keys/)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Перезаписать существующий файл-ключ без подтверждения'
        )

    def _hash_token(self, token):
        """Хэширует токен для безопасного хранения в БД"""
        return hashlib.sha256(token.encode('utf-8')).hexdigest()

    def handle(self, *args, **options):
        username = options['username']
        output_dir = options['output_dir']
        force = options['force']

        # Проверяем существование пользователя
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(
                f'Пользователь "{username}" не найден в системе.')

        # Определяем директорию для сохранения
        if not output_dir:
            output_dir = os.path.join(settings.BASE_DIR, 'keys')
            self.stdout.write(
                self.style.WARNING(
                    f'Директория не указана. Используется папка по умолчанию: {output_dir}'))

        # Создаем директорию, если она не существует
        os.makedirs(output_dir, exist_ok=True)

        # Формируем путь к файлу
        key_filename = f"{username}.key"
        key_path = os.path.join(output_dir, key_filename)

        # Проверка существования файла
        if os.path.exists(key_path) and not force:
            confirm = input(
                f'Файл {key_path} уже существует. Перезаписать? (y/n): ')
            if confirm.lower() != 'y':
                raise CommandError('Операция отменена пользователем.')

        try:
            # Генерируем уникальный токен
            token = secrets.token_urlsafe(64)

            # Сохраняем файл-ключ
            with open(key_path, "w", encoding='utf-8') as f:
                f.write("# Файл-ключ для входа в WorkSafeCenter\n")
                f.write("# НЕ ПЕРЕДАВАЙТЕ ЭТОТ ФАЙЛ ДРУГИМ ЛИЦАМ!\n")
                f.write(f"# Username: {username}\n")
                f.write(f"KEY={token}\n")

            # Сохраняем ХЭШ токена в БД (безопасно!)
            token_hash = self._hash_token(token)
            profile, _ = UserProfile.objects.update_or_create(
                user=user,
                defaults={'auth_token_hash': token_hash}
            )

            self.stdout.write(self.style.SUCCESS(
                f'✅ Успешно: Файл-ключ для "{username}" создан.'
            ))
            self.stdout.write(f'📁 Файл сохранен: {key_path}')
            self.stdout.write(self.style.WARNING(
                '🔒 ВАЖНО: В базе данных сохранен ТОЛЬКО хэш токена для безопасности.'
            ))
            self.stdout.write(self.style.WARNING(
                '⚠️  Передайте файл пользователю ТОЛЬКО безопасным каналом (личная передача)!'
            ))

        except PermissionError as e:
            raise CommandError(
                f'Ошибка доступа к директории {output_dir}: {e}')
        except Exception as e:
            raise CommandError(f'Ошибка при генерации файла-ключа: {e}')
