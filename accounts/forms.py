from django import forms


class LoginForm(forms.Form):
    username = forms.CharField(label="Логин")
    password = forms.CharField(
        widget=forms.PasswordInput,
        label="Пароль"
    )
    auth_file = forms.FileField(
        label="Файл-ключ (.key)",
        help_text="Загрузите ваш персональный файл-ключ для входа",
        required=True
    )
