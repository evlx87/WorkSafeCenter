import os
from django.core.management.base import BaseCommand, CommandError
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


class Command(BaseCommand):
    help = 'Генерирует пару ключей (RSA) для авторизации пользователя'

    def add_arguments(self, parser):
        # Добавляем обязательный аргумент - имя пользователя
        parser.add_argument(
            'username',
            type=str,
            help='Имя пользователя для ключей')

    def handle(self, *args, **options):
        username = options['username']

        # Путь к папке для публичных ключей (теперь мы можем использовать
        # структуру проекта)
        crt_dir = os.path.join('accounts', 'crt')
        if not os.path.exists(crt_dir):
            os.makedirs(crt_dir)

        try:
            # Генерируем ключ
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )

            # Пути к файлам
            priv_filename = f"{username}_private.pem"
            pub_filename = os.path.join(crt_dir, f"{username}_public.pem")

            # Сохранение закрытого ключа
            with open(priv_filename, "wb") as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption()
                ))

            # Сохранение публичного ключа
            public_key = private_key.public_key()
            with open(pub_filename, "wb") as f:
                f.write(public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ))

            self.stdout.write(
                self.style.SUCCESS(
                    f'Успешно: Ключи для "{username}" созданы.'))
            self.stdout.write(f'Закрытый ключ: {priv_filename}')
            self.stdout.write(f'Публичный ключ сохранен в: {pub_filename}')

        except Exception as e:
            raise CommandError(f'Ошибка при генерации ключей: {e}')
