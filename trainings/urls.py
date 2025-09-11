from django.urls import path
from .views import TrainingCreateView, TrainingUpdateView, TrainingDeleteView, TrainingProgramListView, \
    TrainingProgramCreateView, TrainingProgramUpdateView, TrainingProgramDeleteView

app_name = 'trainings'

urlpatterns = [
    path('add/', TrainingCreateView.as_view(), name='training_create'),
    path('<int:pk>/update/', TrainingUpdateView.as_view(), name='training_update'),
    path('<int:pk>/delete/', TrainingDeleteView.as_view(), name='training_delete'),
    path('programs/', TrainingProgramListView.as_view(), name='program_list'),
    path('programs/add/', TrainingProgramCreateView.as_view(), name='program_create'),
    path('programs/<int:pk>/update/', TrainingProgramUpdateView.as_view(), name='program_update'),
    path('programs/<int:pk>/delete/', TrainingProgramDeleteView.as_view(), name='program_delete'),

]