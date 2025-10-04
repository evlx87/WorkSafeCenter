from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import MedicalCheck
from .forms import MedicalCheckForm

class MedicalCheckListView(ListView):
    model = MedicalCheck
    template_name = 'medical_checks/medical_check_list.html'
    context_object_name = 'medical_checks'
    ordering = ['-check_date']

class MedicalCheckCreateView(CreateView):
    model = MedicalCheck
    form_class = MedicalCheckForm
    template_name = 'medical_checks/medical_check_form.html'
    success_url = reverse_lazy('medical_checks:medical_check_list')

class MedicalCheckUpdateView(UpdateView):
    model = MedicalCheck
    form_class = MedicalCheckForm
    template_name = 'medical_checks/medical_check_form.html'
    success_url = reverse_lazy('medical_checks:medical_check_list')

class MedicalCheckDeleteView(DeleteView):
    model = MedicalCheck
    template_name = 'medical_checks/medical_check_confirm_delete.html'
    success_url = reverse_lazy('medical_checks:medical_check_list')