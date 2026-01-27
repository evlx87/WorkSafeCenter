from django.shortcuts import redirect
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch


class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Пытаемся определить URL страницы входа
        try:
            # Сначала пробуем с пространством имен, как в вашем urls.py
            login_url = reverse('accounts:login')
        except NoReverseMatch:
            try:
                # Если не вышло, пробуем без него
                login_url = reverse('login')
            except NoReverseMatch:
                # Крайний случай, если маршруты еще не прогружены
                login_url = '/accounts/login/'

        # 2. Список исключений (админка, статика и сама страница логина)
        if (request.user.is_authenticated or
            request.path == login_url or
            request.path.startswith('/admin/') or
                request.path.startswith('/static/')):
            return self.get_response(request)

        # 3. Редирект всех остальных на логин
        return redirect(login_url)
