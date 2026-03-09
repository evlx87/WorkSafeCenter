from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, UpdateView, DeleteView
from django.views.generic.detail import DetailView
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView

from employees.models import Employee
from .forms import InstructionForm, TrainingForm, TrainingProgramForm, TrainingCenterForm, InternshipForm
from .models import Instruction, Training, TrainingProgram, TrainingCategory, TrainingCenter, Internship
from .services import check_employee_compliance


def training_program_list(request):
    """
    Отображает список всех программ обучения с подсчетом сотрудников,
    прошедших их, и сводными данными для панели управления.
    """
    programs = TrainingProgram.objects.all()
    search_query = request.GET.get('search_query')
    selected_type = request.GET.get('training_type')

    if search_query:
        programs = programs.filter(name__icontains=search_query)

    if selected_type:
        programs = programs.filter(category__code=selected_type)

    programs_with_counts = programs.annotate(
        total_count=Count('training')
    )

    total_programs_count = programs.count()
    total_employees_count = Employee.objects.count()
    overdue_employees_count = Instruction.objects.filter(
        next_training_date__lt=timezone.now().date()).values('employee').annotate(
        count=Count('employee')).filter(
            count__gt=0).count()

    context = {
        'programs': programs_with_counts,
        'total_programs_count': total_programs_count,
        'total_employees_count': total_employees_count,
        'overdue_employees_count': overdue_employees_count,
        'search_query': search_query,
        'selected_type': selected_type,
        'type_choices': TrainingCategory.CATEGORY_CHOICES,
    }

    return render(request, 'trainings/training_program_list.html', context)


class InstructionCreateView(CreateView):
    model = Instruction
    form_class = InstructionForm
    template_name = 'trainings/safety_training_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employee'] = get_object_or_404(
            Employee, pk=self.kwargs['employee_pk'])
        return context

    def form_valid(self, form):
        employee = get_object_or_404(Employee, pk=self.kwargs['employee_pk'])
        form.instance.employee = employee
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('employees:employee_detail', kwargs={
            'pk': self.kwargs['employee_pk']})


class InstructionUpdateView(UpdateView):
    model = Instruction
    form_class = InstructionForm
    template_name = 'trainings/safety_training_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employee'] = self.object.employee
        return context

    def get_success_url(self):
        return reverse_lazy('employees:employee_detail', kwargs={
            'pk': self.object.employee.pk})


class InstructionDeleteView(DeleteView):
    model = Instruction
    template_name = 'trainings/safety_training_confirm_delete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employee'] = self.object.employee
        return context

    def get_success_url(self):
        return reverse_lazy('employees:employee_detail', kwargs={
            'pk': self.object.employee.pk})


class TrainingCreateView(CreateView):
    model = Training
    form_class = TrainingForm
    template_name = 'trainings/training_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employee'] = get_object_or_404(
            Employee, pk=self.kwargs['employee_pk'])
        return context

    def form_valid(self, form):
        employee = get_object_or_404(Employee, pk=self.kwargs['employee_pk'])
        form.instance.employee = employee
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('employees:employee_detail', kwargs={
            'pk': self.kwargs['employee_pk']})


class TrainingUpdateView(UpdateView):
    model = Training
    form_class = TrainingForm
    template_name = 'trainings/training_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employee'] = self.object.employee
        return context

    def get_success_url(self):
        return reverse_lazy('employees:employee_detail', kwargs={
            'pk': self.object.employee.pk})


class TrainingDeleteView(DeleteView):
    model = Training
    template_name = 'trainings/training_confirm_delete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employee'] = self.object.employee
        return context

    def get_success_url(self):
        return reverse_lazy('employees:employee_detail', kwargs={
            'pk': self.object.employee.pk})


class TrainingProgramDetailView(DetailView):
    model = TrainingProgram
    template_name = 'trainings/program_detail.html'
    context_object_name = 'program'


class TrainingProgramCreateView(CreateView):
    model = TrainingProgram
    form_class = TrainingProgramForm
    template_name = 'trainings/training_program_form.html'
    success_url = reverse_lazy('trainings:training_program_list')


class TrainingProgramUpdateView(UpdateView):
    model = TrainingProgram
    form_class = TrainingProgramForm
    template_name = 'trainings/training_program_form.html'
    success_url = reverse_lazy('trainings:training_program_list')


class TrainingProgramDeleteView(DeleteView):
    model = TrainingProgram
    template_name = 'trainings/training_program_confirm_delete.html'
    success_url = reverse_lazy('trainings:training_program_list')


class TrainingCenterListView(ListView):
    """Список учебных центров"""
    model = TrainingCenter
    template_name = 'trainings/training_center_list.html'
    context_object_name = 'centers'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        is_active = self.request.GET.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active == 'true')
        return queryset


class TrainingCenterCreateView(CreateView):
    model = TrainingCenter
    form_class = TrainingCenterForm
    template_name = 'trainings/training_center_form.html'
    success_url = reverse_lazy('trainings:training_center_list')


class TrainingCenterUpdateView(UpdateView):
    model = TrainingCenter
    form_class = TrainingCenterForm
    template_name = 'trainings/training_center_form.html'
    success_url = reverse_lazy('trainings:training_center_list')


class InternshipListView(ListView):
    """Список стажировок"""
    model = Internship
    template_name = 'trainings/internship_list.html'
    context_object_name = 'internships'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'employee', 'workplace', 'supervisor'
        )
        is_completed = self.request.GET.get('is_completed')
        if is_completed is not None:
            queryset = queryset.filter(is_completed=is_completed == 'true')
        return queryset


class InternshipCreateView(CreateView):
    model = Internship
    form_class = InternshipForm
    template_name = 'trainings/internship_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employee'] = get_object_or_404(Employee, pk=self.kwargs['employee_pk'])
        return context

    def form_valid(self, form):
        employee = get_object_or_404(Employee, pk=self.kwargs['employee_pk'])
        form.instance.employee = employee
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('employees:employee_detail', kwargs={'pk': self.kwargs['employee_pk']})


class InternshipUpdateView(UpdateView):
    model = Internship
    form_class = InternshipForm
    template_name = 'trainings/internship_form.html'

    def get_success_url(self):
        return reverse_lazy('trainings:internship_list')


class ComplianceDashboardView(TemplateView):
    """Панель соответствия требованиям"""
    template_name = 'trainings/compliance_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()

        all_employees = Employee.objects.filter(is_active=True, termination_date__isnull=True)

        violations_count = 0
        warnings_count = 0
        compliant_count = 0

        for emp in all_employees:
            status = check_employee_compliance(emp)
            if status['compliant']:
                compliant_count += 1
            else:
                violations_count += len(status['expired_programs']) + len(status['expired_instructions'])
                warnings_count += len(status['missing_programs']) + len(status['missing_instructions'])

        context.update({
            'total_employees': all_employees.count(),
            'compliant_count': compliant_count,
            'violations_count': violations_count,
            'warnings_count': warnings_count,
            'compliance_rate': round(
                compliant_count / all_employees.count() * 100, 1
            ) if all_employees.count() > 0 else 0,
        })

        return context


class ComplianceReportView(TemplateView):
    """Отчет по соответствию конкретного сотрудника"""
    template_name = 'trainings/compliance_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee = get_object_or_404(Employee, pk=kwargs['employee_pk'])
        compliance_status = check_employee_compliance(employee)

        context.update({
            'employee': employee,
            'compliance': compliance_status,
            'today': timezone.now().date(),
        })

        return context