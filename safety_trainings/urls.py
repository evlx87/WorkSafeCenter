from django.urls import path
from .views import safety_trainings_list, SafetyTrainingCreateView, SafetyTrainingUpdateView, SafetyTrainingDeleteView

app_name = 'safety_trainings'

urlpatterns = [
    path('add/', SafetyTrainingCreateView.as_view(), name='safety_training_create'),
    path('<int:pk>/update/', SafetyTrainingUpdateView.as_view(), name='safety_training_update'),
    path('<int:pk>/delete/', SafetyTrainingDeleteView.as_view(), name='safety_training_delete'),
]