from django.shortcuts import render
from .models import Notification


# Create your views here.
def notification_list(request):
    notifications = Notification.objects.all()
    return render(request, 'notifications/notification_list.html', {'notifications': notifications})