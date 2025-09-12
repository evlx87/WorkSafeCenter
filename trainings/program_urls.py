from django.urls import path

from .views import TrainingProgramListView, TrainingProgramCreateView, TrainingProgramUpdateView, \
    TrainingProgramDeleteView

app_name = 'programs'

urlpatterns = [
    path('', TrainingProgramListView.as_view(), name='program_list'),
    path('add/', TrainingProgramCreateView.as_view(), name='program_create'),
    path('<int:pk>/update/', TrainingProgramUpdateView.as_view(), name='program_update'),
    path('<int:pk>/delete/', TrainingProgramDeleteView.as_view(), name='program_delete'),
]
