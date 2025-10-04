from dateutil.relativedelta import relativedelta
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, UpdateView, DeleteView

from employees.models import Employee
from trainings.models import Training, TrainingProgram
from .forms import SafetyTrainingForm
from .models import SafetyTraining
from django.db.models import Count


# Create your views here.
def safety_trainings_list(request):
    programs = TrainingProgram.objects.all()
    summary_data = []
    today = timezone.now().date()
    four_months_later = today + relativedelta(months=4)

    for program in programs:
        trainings_for_program = Training.objects.filter(program=program)
        total_count = trainings_for_program.count()
        approaching_count = 0

        if program.frequency_months > 0:
            for training in trainings_for_program:
                expiration_date = training.training_date + \
                    relativedelta(months=program.frequency_months)
                if today < expiration_date <= four_months_later:
                    approaching_count += 1

        if total_count > 0:
            summary_data.append({
                'name': program.name,
                'hours': program.hours,
                'total_count': total_count,
                'approaching_count': approaching_count,
            })

    safety_summary_query = SafetyTraining.objects \
        .values('category', 'training_type') \
        .annotate(employee_count=Count('id')) \
        .order_by('category', 'training_type')

    # Преобразуем для удобного отображения в шаблоне
    category_map = dict(SafetyTraining.TRAINING_CATEGORIES)
    type_map = dict(SafetyTraining.TRAINING_TYPES)

    safety_summary = [
        {
            'category': category_map.get(item['category']),
            'type': type_map.get(item['training_type']),
            'count': item['employee_count']
        }
        for item in safety_summary_query
    ]

    # Добавляем новые данные в контекст
    context = {
        'summary_data': summary_data,
        'safety_summary': safety_summary,
    }

    return render(
        request, 'safety_trainings/safety_trainings_list.html', context)


class SafetyTrainingCreateView(CreateView):
    model = SafetyTraining
    form_class = SafetyTrainingForm
    template_name = 'safety_trainings/safetytraining_form.html'

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
    model = SafetyTraining
    form_class = SafetyTrainingForm
    template_name = 'safety_trainings/safetytraining_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employee'] = self.object.employee
        return context

    def get_success_url(self):
        return reverse_lazy('employees:employee_detail', kwargs={
                            'pk': self.object.employee.pk})


class SafetyTrainingDeleteView(DeleteView):
    model = SafetyTraining
    template_name = 'safety_trainings/safetytraining_confirm_delete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employee'] = self.object.employee
        return context

    def get_success_url(self):
        return reverse_lazy('employees:employee_detail', kwargs={
                            'pk': self.object.employee.pk})
