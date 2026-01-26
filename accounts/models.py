from django.contrib.auth.models import User
from django.db import models


# Create your models here.
class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile')
    public_key = models.TextField("Публичный ключ (PEM format)")

    def __str__(self):
        return self.user.username
