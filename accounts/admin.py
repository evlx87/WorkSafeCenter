from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.core.management import call_command
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
            # Вызываем вашу команду generate_keys
            call_command('generate_keys', user.username)
            messages.success(
                request, f"Ключи для {
                    user.username} успешно созданы. Закрытый ключ сохранен в корне проекта.")
        except Exception as e:
            messages.error(request, f"Ошибка при генерации: {e}")

        return redirect('admin:auth_user_change', user_id)


# Перерегистрируем стандартного пользователя на нашего кастомного
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
