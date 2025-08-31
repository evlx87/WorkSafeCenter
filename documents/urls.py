from django.urls import path
from .views import documents_list

app_name = 'documents'

urlpatterns = [
    path('', documents_list, name='documents_list'),
]