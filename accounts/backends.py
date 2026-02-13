import secrets

from django.contrib.auth.backends import ModelBackend

from accounts.models import UserProfile


class CertificateAuthBackend(ModelBackend):
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

            # 5. Сравниваем токены (безопасное сравнение)
            if secrets.compare_digest(token, profile.auth_token_hash):
                return user
            else:
                return None

        except Exception as e:
            import logging
            logging.warning(f"Auth failed for {username}: {str(e)[:50]}")
            return None
