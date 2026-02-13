from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect

from accounts.forms import LoginForm


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST, request.FILES)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
                auth_file=request.FILES.get('auth_file')
            )
            if user:
                login(request, user)
                return redirect('index')
            else:
                form.add_error(None, "Ошибка: неверные данные или файл-ключ")
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})
