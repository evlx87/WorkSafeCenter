from django.shortcuts import redirect
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch


class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Пытаемся определить URL страницы входа
        try:
            login_url = reverse('accounts:login')
        except NoReverseMatch:
            try:
                login_url = reverse('login')
            except NoReverseMatch:
                login_url = '/accounts/login/'

        # 2. Список исключений (админка, статика и сама страница логина)
        if (request.user.is_authenticated or request.path == login_url or request.path.startswith(
                '/admin/') or request.path.startswith('/static/') or request.path.startswith('/media/')):
            return self.get_response(request)

        # 3. Редирект всех остальных на логин
        return redirect(f'{login_url}?next={request.path}')
