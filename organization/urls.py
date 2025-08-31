from django.urls import path
from .views import organization_info

app_name = 'organization'

urlpatterns = [
    path('', organization_info, name='organization_info'),
]