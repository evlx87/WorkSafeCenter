from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from django.contrib.auth.backends import ModelBackend
from accounts.models import UserProfile


class CertificateAuthBackend(ModelBackend):
    def authenticate(
            self,
            request,
            username=None,
            password=None,
            cert_file=None,
            **kwargs):
        # 1. Стандартная проверка логина/пароля
        user = super().authenticate(request, username, password, **kwargs)
        if not user or not cert_file:
            return None

        try:
            # 2. Загружаем ТОЛЬКО публичный ключ из профиля пользователя
            profile = UserProfile.objects.get(user=user)
            public_key = serialization.load_pem_public_key(
                profile.public_key.encode('utf-8')
            )

            # 3. Читаем подпись из загруженного файла
            # Файл должен содержать ПОДПИСЬ (signature)
            signature = cert_file.read()

            # 4. Верифицируем подпись для стандартного вызова
            challenge = f"auth_challenge_{user.username}_{int(time.time())}".encode(
            )
            public_key.verify(
                signature,
                challenge,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return user

        except Exception as e:
            # Логируем ошибку для аудита (без раскрытия деталей)
            import logging
            logging.warning(f"Auth failed for {username}: {str(e)[:50]}")
            return None
