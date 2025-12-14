from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, UpdateView, DeleteView
from django.views.generic.detail import DetailView

from employees.models import Employee
from .forms import InstructionForm, TrainingForm, TrainingProgramForm
from .models import Instruction, Training, TrainingProgram


# 1. ГЛАВНАЯ СТРАНИЦА: СПИСОК ПРОГРАММ (TrainingProgram)
def training_program_list(request):
    """
    Отображает список всех программ обучения с подсчетом сотрудников,
    прошедших их, и сводными данными для панели управления.
    """
    programs = TrainingProgram.objects.all()

    # Логика фильтрации (взята из предыдущих шагов)
    search_query = request.GET.get('search_query')
    selected_type = request.GET.get('training_type')

    if search_query:
        programs = programs.filter(name__icontains=search_query)

    if selected_type:
        programs = programs.filter(training_type=selected_type)

    # *** КОРРЕКЦИЯ 1: ОПТИМИЗАЦИЯ N+1 QUERIES ***
    # Используем .annotate() для подсчета прохождений обучения (Training)
    # total_count будет доступен через program.total_count в шаблоне
    programs_with_counts = programs.annotate(
        total_count=Count('training')
    )

    # 2. Расчет общих сводных данных для карточек
    total_programs_count = programs.count()
    total_employees_count = Employee.objects.count()

    # Считаем сотрудников с просроченным ВНУТРЕННИМ инструктажем
    # (SafetyTraining)
    overdue_employees_count = Instruction.objects.filter(
        next_training_date__lt=timezone.now().date()).values('employee').annotate(
        count=Count('employee')).filter(
            count__gt=0).count()

    # 3. Формирование контекста
    context = {
        'programs': programs_with_counts,
        'total_programs_count': total_programs_count,
        'total_employees_count': total_employees_count,
        'overdue_employees_count': overdue_employees_count,
        'search_query': search_query,
        'selected_type': selected_type,
        # Передаем CHOICES для использования в фильтре шаблона
        'type_choices': TrainingProgram.TRAINING_TYPES,
    }

    return render(request, 'trainings/training_program_list.html', context)


# ----------------------------------------------------------------------
# 2. CRUD ДЛЯ ЗАПИСЕЙ О ПРОХОЖДЕНИИ ИНСТРУКТАЖА (SafetyTraining)
# ----------------------------------------------------------------------
class SafetyTrainingCreateView(CreateView):
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


class SafetyTrainingUpdateView(UpdateView):
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


class SafetyTrainingDeleteView(DeleteView):
    model = Instruction
    template_name = 'trainings/safety_training_confirm_delete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employee'] = self.object.employee
        return context

    def get_success_url(self):
        return reverse_lazy('employees:employee_detail', kwargs={
            'pk': self.object.employee.pk})


# ----------------------------------------------------------------------
# 3. CRUD ДЛЯ ЗАПИСЕЙ О ПРОХОЖДЕНИИ ОБУЧЕНИЯ (Training)
# ----------------------------------------------------------------------
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


# ----------------------------------------------------------------------
# 4. CRUD ДЛЯ ПРОГРАММ ОБУЧЕНИЯ (TrainingProgram)
# ----------------------------------------------------------------------
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
