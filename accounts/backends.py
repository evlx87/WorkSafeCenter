import hashlib
import secrets

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

from accounts.models import UserProfile

UserModel = get_user_model()


class CertificateAuthBackend(ModelBackend):
    """Бэкенд аутентификации по файлу-ключу"""

    def authenticate(
            self,
            request,
            username=None,
            password=None,
            auth_file=None,
            **kwargs):
        # 1. Стандартная проверка логина/пароля
        user = super().authenticate(request, username, password, **kwargs)

        if not user or not auth_file:
            return None

        try:
            # 2. Читаем файл-ключ
            file_content = auth_file.read().decode('utf-8')
            auth_file.seek(0)  # Возвращаем указатель в начало

            # 3. Извлекаем токен из файла (формат: KEY=token_value)
            token = None
            for line in file_content.split('\n'):
                if line.startswith('KEY='):
                    token = line.split('=', 1)[1].strip()
                    break

            if not token:
                return None

            # 4. Получаем хэш токена из БД
            profile = UserProfile.objects.get(user=user)

            if not profile.auth_token_hash:
                return None

            # 5. Сравниваем хэши (безопасное сравнение)
            input_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
            stored_hash = profile.auth_token_hash

            if secrets.compare_digest(input_hash, stored_hash):
                return user
            else:
                return None

        except Exception as e:
            import logging
            logging.warning(f"Auth failed for {username}: {str(e)[:50]}")
            return None
