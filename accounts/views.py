from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login

from accounts.forms import LoginForm


# Create your views here.
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST, request.FILES)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
                cert_file=request.FILES['certificate']
            )
            if user:
                login(request, user)
                return redirect('index')  # На главную страницу
            else:
                form.add_error(None, "Ошибка: неверные данные или ключ")
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})
