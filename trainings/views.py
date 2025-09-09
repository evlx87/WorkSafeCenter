from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView
from .models import Training
from .forms import TrainingForm
from employees.models import Employee


# Create your views here.
class TrainingCreateView(CreateView):
    model = Training
    form_class = TrainingForm
    template_name = 'trainings/training_form.html'

    def form_valid(self, form):
        employee = get_object_or_404(Employee, pk=self.kwargs['employee_pk'])
        form.instance.employee = employee
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employee'] = get_object_or_404(
            Employee, pk=self.kwargs['employee_pk'])
        return context

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
