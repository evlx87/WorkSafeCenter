from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView

from organization.models import Department
from trainings.services import check_employee_compliance
from .forms import EmployeeForm
from .models import Employee


# Create your views here.
class EmployeeListView(LoginRequiredMixin, ListView):
    model = Employee
    template_name = 'employees/employee_list.html'
    context_object_name = 'employees'

    def get_queryset(self):
        queryset = super().get_queryset().select_related('position', 'department')
        search_query = self.request.GET.get('search_query', '')
        department_id = self.request.GET.get('department', '')

        if search_query:
            queryset = queryset.filter(last_name__icontains=search_query)

        if department_id:
            queryset = queryset.filter(department_id=department_id)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Передаем в шаблон все отделы для выпадающего списка
        context['departments'] = Department.objects.all()
        # Передаем текущие значения фильтров, чтобы форма "помнила" их
        context['search_query'] = self.request.GET.get('search_query', '')
        context['selected_department'] = self.request.GET.get('department', '')
        return context


class EmployeeDetailView(DetailView):
    model = Employee
    template_name = 'employees/employee_detail.html'
    context_object_name = 'employee'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Получаем статус соблюдения требований
        compliance_status = check_employee_compliance(self.object)

        context['compliance'] = compliance_status
        context['today'] = timezone.now().date()
        # Просто флаг, есть ли проблемы, для отображения блока предупреждения
        context['has_compliance_issues'] = any([
            compliance_status['missing_programs'],
            compliance_status['missing_instructions'],
            compliance_status['expired_programs'],
            compliance_status['expired_instructions']
        ])

        return context


class EmployeeCreateView(CreateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'employees/employee_form.html'
    success_url = reverse_lazy('employees:employee_list')


class EmployeeUpdateView(UpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'employees/employee_form.html'
    success_url = reverse_lazy('employees:employee_list')


class EmployeeDeleteView(DeleteView):
    model = Employee
    template_name = 'employees/employee_confirm_delete.html'
    success_url = reverse_lazy('employees:employee_list')
