import hashlib

from django.core.management.base import BaseCommand

from accounts.models import UserProfile


class Command(BaseCommand):
    help = 'Хэширует существующие токены аутентификации в базе данных'

    def handle(self, *args, **options):
        profiles = UserProfile.objects.exclude(
            auth_token_hash__isnull=True).exclude(
            auth_token_hash='')

        migrated = 0
        skipped = 0

        for profile in profiles:
            token = profile.auth_token_hash.strip()

            # Пропускаем уже захэшированные токены (проверяем длину SHA-256)
            if len(token) == 64 and all(
                    c in '0123456789abcdef' for c in token.lower()):
                skipped += 1
                continue

            # Хэшируем токен
            token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
            profile.auth_token_hash = token_hash
            profile.save()
            migrated += 1
            self.stdout.write(
                f'✅ Хэширован токен для пользователя: {
                    profile.user.username}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Миграция завершена: {migrated} токенов обработано, {skipped} пропущено (уже хэшированы)'))
