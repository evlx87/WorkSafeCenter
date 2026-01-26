from django import forms


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
    certificate = forms.FileField(label="Файл закрытого ключа (.pem)")
