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


class LoginAudit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField()
    timestamp = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField()
    user_agent = models.CharField(max_length=255, blank=True)
