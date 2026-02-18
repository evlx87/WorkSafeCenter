from io import BytesIO

from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.http.response import HttpResponse
from django.shortcuts import redirect
from django.urls import path

from accounts.models import UserProfile


# Register your models here.
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user']
    search_fields = ['user__username']


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    readonly_fields = ('public_key',)


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    change_form_template = 'admin/accounts/userprofile/change_form.html'

    # Добавляем кастомный URL для обработки генерации ключей
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:user_id>/generate-keys/',
                 self.admin_site.admin_view(self.generate_keys_view),
                 name='user-generate-keys'),
        ]
        return custom_urls + urls

    def generate_keys_view(self, request, user_id):
        user = User.objects.get(pk=user_id)
        try:
            # Генерируем токен в памяти
            import hashlib
            import secrets

            token = secrets.token_urlsafe(64)
            token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()

            # Сохраняем хэш в БД
            profile, _ = UserProfile.objects.update_or_create(
                user=user,
                defaults={'auth_token_hash': token_hash}
            )

            # Создаем файл-ключ в памяти
            file_content = BytesIO()
            file_content.write(
                f"# Файл-ключ для входа в WorkSafeCenter\n".encode('utf-8'))
            file_content.write(
                f"# НЕ ПЕРЕДАВАЙТЕ ЭТОТ ФАЙЛ ДРУГИМ ЛИЦАМ!\n".encode('utf-8'))
            file_content.write(
                f"# Username: {
                    user.username}\n".encode('utf-8'))
            file_content.write(f"KEY={token}\n".encode('utf-8'))
            file_content.seek(0)

            # Отправляем файл пользователю
            response = HttpResponse(
                file_content.getvalue(),
                content_type='application/octet-stream'
            )
            response['Content-Disposition'] = f'attachment; filename="{
                user.username}.key"'

            messages.success(
                request, f"Ключи для {
                    user.username} успешно созданы и скачаны.")
            return response

        except Exception as e:
            messages.error(request, f"Ошибка при генерации: {e}")
            return redirect('admin:auth_user_change', user_id)


# Перерегистрируем стандартного пользователя на нашего кастомного
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
