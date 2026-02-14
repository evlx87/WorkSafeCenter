import hashlib
import secrets

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

from accounts.models import UserProfile

UserModel = get_user_model()


class FileTokenBackend(ModelBackend):
    """Бэкенд аутентификации по файлу-ключу"""

    def authenticate(self, request, username=None, token_file=None, **kwargs):
        if not username or not token_file:
            return None

        try:
            user = UserModel.objects.get(username=username)
            profile = UserProfile.objects.get(user=user)

            if not profile.auth_token_hash:
                return None

            # Читаем токен из файла
            token_content = token_file.read().decode('utf-8')
            # Возвращаем указатель в начало для повторного использования
            token_file.seek(0)

            # Извлекаем токен из содержимого файла
            token = None
            for line in token_content.splitlines():
                if line.startswith('KEY='):
                    token = line.split('=', 1)[1].strip()
                    break

            if not token:
                return None

            # Сравниваем хэши (безопасное сравнение)
            input_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
            stored_hash = profile.auth_token_hash

            if secrets.compare_digest(input_hash, stored_hash):
                return user

        except (UserModel.DoesNotExist, UserProfile.DoesNotExist):
            return None

        return None
