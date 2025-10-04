from django.urls import path
from .views import (
    MedicalCheckListView,
    MedicalCheckCreateView,
    MedicalCheckUpdateView,
    MedicalCheckDeleteView
)

app_name = 'medical_checks'

urlpatterns = [
    path('', MedicalCheckListView.as_view(), name='medical_check_list'),
    path('create/', MedicalCheckCreateView.as_view(), name='medical_check_create'),
    path('<int:pk>/update/', MedicalCheckUpdateView.as_view(), name='medical_check_update'),
    path('<int:pk>/delete/', MedicalCheckDeleteView.as_view(), name='medical_check_delete'),
]
