from django.urls import path
from .views import EmployeeListView, EmployeeCreateView, EmployeeUpdateView, EmployeeDeleteView

app_name = 'employees'

urlpatterns = [
    path('', EmployeeListView.as_view(), name='employee_list'),
    path('create/', EmployeeCreateView.as_view(), name='employee_create'),
    path('<int:pk>/update/', EmployeeUpdateView.as_view(), name='employee_update'),
    path('<int:pk>/delete/', EmployeeDeleteView.as_view(), name='employee_delete'),
]
