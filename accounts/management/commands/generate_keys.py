import os
import sys
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


def generate_user_keys(username):
    # Путь к папке для публичных ключей внутри приложения accounts
    public_keys_dir = os.path.join('../..', 'crt')

    # Создаем директорию, если она не существует
    if not os.path.exists(public_keys_dir):
        os.makedirs(public_keys_dir)
        print(f"Создана директория: {public_keys_dir}")

    # 1. Генерируем новый закрытый ключ
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )

    # Имена файлов
    private_key_file = f"{username}_private.pem"
    public_key_file = os.path.join(public_keys_dir, f"{username}_public.pem")

    # 2. Сохраняем ЗАКРЫТЫЙ ключ (этот файл отдаем пользователю)
    with open(private_key_file, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))

    # 3. Сохраняем ПУБЛИЧНЫЙ ключ (в папку accounts/crt/ для сервера)
    public_key = private_key.public_key()
    with open(public_key_file, "wb") as f:
        # ИСПРАВЛЕНО: используем метод public_bytes вместо bytes
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))

    print("-" * 40)
    print(f"Ключи для пользователя '{username}' успешно созданы!")
    print(f"Закрытый ключ (для входа): {private_key_file}")
    print(f"Публичный ключ (на сервере): {public_key_file}")
    print("-" * 40)
    print("ИНСТРУКЦИЯ:")
    print(f"1. Откройте файл {public_key_file} через Блокнот.")
    print(f"2. Скопируйте текст и вставьте его в профиль пользователя {username} в админке.")
    print("-" * 40)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Ошибка: Нужно указать имя пользователя.")
        print("Пример: python generate_keys.py evlx")
    else:
        user_name = sys.argv[1]
        generate_user_keys(user_name)