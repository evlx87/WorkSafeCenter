import io
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User

from accounts.models import UserProfile


class CertificateAuthBackend(ModelBackend):
    def authenticate(
            self,
            request,
            username=None,
            password=None,
            cert_file=None,
            **kwargs):
        # 1. Проверяем логин и пароль стандартным способом
        user = super().authenticate(request, username, password, **kwargs)
        if not user or not cert_file:
            return None

        try:
            # 2. Получаем профиль с публичным ключом
            profile = UserProfile.objects.get(user=user)
            public_key = serialization.load_pem_public_key(
                profile.public_key.encode())

            # 3. Читаем загруженный закрытый ключ (в памяти, не сохраняя на
            # диск)
            private_key_content = cert_file.read()
            private_key = serialization.load_pem_private_key(
                private_key_content, password=None)

            # 4. Проверка: подписываем данные закрытым ключом и сверяем
            # публичным
            challenge = b"verification_token"
            signature = private_key.sign(
                challenge,
                padding.PSS(
                    mgf=padding.MGF1(
                        hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256())

            public_key.verify(
                signature,
                challenge,
                padding.PSS(
                    mgf=padding.MGF1(
                        hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256())
            return user  # Все проверки пройдены
        except Exception:
            return None
