import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from accounts.models import UserProfile
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


class Command(BaseCommand):
    help = 'Генерирует пару ключей (RSA) для авторизации пользователя'

    def add_arguments(self, parser):
        parser.add_argument(
            'username',
            type=str,
            help='Имя пользователя для ключей')

    def handle(self, *args, **options):
        username = options['username']

        # Проверяем существование пользователя перед генерацией
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(
                f'Пользователь "{username}" не найден в системе.')

        crt_dir = os.path.join(settings.BASE_DIR, 'accounts', 'crt')
        if not os.path.exists(crt_dir):
            os.makedirs(crt_dir)

        try:
            # 1. Генерируем ключи
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )

            # Формируем байты ключей
            priv_bytes = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            )

            public_key = private_key.public_key()
            pub_bytes = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )

            # 2. Сохраняем файлы на диск (как и было)
            priv_path = os.path.join(crt_dir, f"{username}_private.pem")
            pub_path = os.path.join(crt_dir, f"{username}_public.pem")

            with open(priv_path, "wb") as f:
                f.write(priv_bytes)

            with open(pub_path, "wb") as f:
                f.write(pub_bytes)

            # 3. Привязываем публичный ключ к профилю пользователя
            # Используем update_or_create на случай, если ключ обновляется
            profile, created = UserProfile.objects.update_or_create(
                user=user,
                defaults={'public_key': pub_bytes.decode('utf-8')}
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f'Успешно: Ключи для "{username}" созданы и привязаны к профилю.'))
            self.stdout.write(f'Закрытый ключ: {priv_path}')
            self.stdout.write(
                f'Публичный ключ сохранен в БД и в файл: {pub_path}')

        except Exception as e:
            raise CommandError(
                f'Ошибка при генерации или сохранении ключей: {e}')
