from django.urls import path
from .views import training_program_list, TrainingProgramCreateView, TrainingProgramUpdateView, \
    TrainingProgramDeleteView, TrainingProgramDetailView, TrainingCreateView, TrainingUpdateView, \
    TrainingDeleteView, SafetyTrainingCreateView, SafetyTrainingUpdateView, SafetyTrainingDeleteView

app_name = 'trainings'


urlpatterns = [
    # 1. ОСНОВНАЯ СТРАНИЦА - Список всех программ
    path('', training_program_list, name='training_program_list'),

    # 2. CRUD ДЛЯ ПРОГРАММ ОБУЧЕНИЯ (Program CRUD)
    path('programs/create/', TrainingProgramCreateView.as_view(), name='program_create'),
    path('programs/<int:pk>/', TrainingProgramDetailView.as_view(), name='program_detail'),
    path('programs/<int:pk>/update/', TrainingProgramUpdateView.as_view(), name='program_update'),
    path('programs/<int:pk>/delete/', TrainingProgramDeleteView.as_view(), name='program_delete'),

    # 3. CRUD ДЛЯ ЗАПИСЕЙ О ПРОХОЖДЕНИИ ОБУЧЕНИЯ (Training CRUD)
    # Используем employee_pk для привязки к сотруднику
    path('employee/<int:employee_pk>/training/add/', TrainingCreateView.as_view(), name='training_create'),
    path('employee/<int:employee_pk>/training/<int:pk>/update/', TrainingUpdateView.as_view(), name='training_update'),
    path('employee/<int:employee_pk>/training/<int:pk>/delete/', TrainingDeleteView.as_view(), name='training_delete'),

    # 4. CRUD ДЛЯ ЗАПИСЕЙ О ПРОВЕДЕНИИ ИНСТРУКТАЖЕЙ (SafetyTraining CRUD)
    # Используем employee_pk для привязки к сотруднику
    path('employee/<int:employee_pk>/safety/add/', SafetyTrainingCreateView.as_view(), name='safety_training_create'),
    path('employee/<int:employee_pk>/safety/<int:pk>/update/', SafetyTrainingUpdateView.as_view(), name='safety_training_update'),
    path('employee/<int:employee_pk>/safety/<int:pk>/delete/', SafetyTrainingDeleteView.as_view(), name='safety_training_delete'),
]