from django.urls import path
from .views import TrainingCreateView, TrainingUpdateView, TrainingDeleteView, TrainingProgramListView, \
    TrainingProgramCreateView, TrainingProgramUpdateView, TrainingProgramDeleteView

app_name = 'trainings'

urlpatterns = [
    path('add/', TrainingCreateView.as_view(), name='training_create'),
    path('<int:pk>/update/', TrainingUpdateView.as_view(), name='training_update'),
    path('<int:pk>/delete/', TrainingDeleteView.as_view(), name='training_delete'),
]