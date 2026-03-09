from django.urls import path

from .views import training_program_list, TrainingProgramCreateView, TrainingProgramUpdateView, \
    TrainingProgramDeleteView, TrainingProgramDetailView, TrainingCreateView, TrainingUpdateView, \
    TrainingDeleteView, InstructionCreateView, InstructionUpdateView, InstructionDeleteView, TrainingCenterListView, \
    TrainingCenterCreateView, TrainingCenterUpdateView, InternshipListView, InternshipCreateView, InternshipUpdateView

app_name = 'trainings'

urlpatterns = [
    # Программы обучения
    path('', training_program_list, name='training_program_list'),
    path('programs/create/', TrainingProgramCreateView.as_view(), name='program_create'),
    path('programs/<int:pk>/', TrainingProgramDetailView.as_view(), name='program_detail'),
    path('programs/<int:pk>/update/', TrainingProgramUpdateView.as_view(), name='program_update'),
    path('programs/<int:pk>/delete/', TrainingProgramDeleteView.as_view(), name='program_delete'),

    # Записи об обучении
    path('employee/<int:employee_pk>/training/add/', TrainingCreateView.as_view(), name='training_create'),
    path('employee/<int:employee_pk>/training/<int:pk>/update/', TrainingUpdateView.as_view(), name='training_update'),
    path('employee/<int:employee_pk>/training/<int:pk>/delete/', TrainingDeleteView.as_view(), name='training_delete'),

    # Инструктажи
    path('employee/<int:employee_pk>/instruction/add/', InstructionCreateView.as_view(), name='safety_training_create'),
    path('employee/<int:employee_pk>/instruction/<int:pk>/update/', InstructionUpdateView.as_view(),
         name='safety_training_update'),
    path('employee/<int:employee_pk>/instruction/<int:pk>/delete/', InstructionDeleteView.as_view(),
         name='safety_training_delete'),

    # Учебные центры
    path('centers/', TrainingCenterListView.as_view(), name='training_center_list'),
    path('centers/create/', TrainingCenterCreateView.as_view(), name='training_center_create'),
    path('centers/<int:pk>/update/', TrainingCenterUpdateView.as_view(), name='training_center_update'),

    # Стажировки
    path('internships/', InternshipListView.as_view(), name='internship_list'),
    path('employee/<int:employee_pk>/internship/add/', InternshipCreateView.as_view(), name='internship_create'),
    path('internships/<int:pk>/update/', InternshipUpdateView.as_view(), name='internship_update'),
]
