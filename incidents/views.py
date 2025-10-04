from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Incident
from .forms import IncidentForm

class IncidentListView(ListView):
    model = Incident
    template_name = 'incidents/incident_list.html'
    context_object_name = 'incidents'
    ordering = ['-incident_date']

class IncidentCreateView(CreateView):
    model = Incident
    form_class = IncidentForm
    template_name = 'incidents/incident_form.html'
    success_url = reverse_lazy('incidents:incident_list')

class IncidentUpdateView(UpdateView):
    model = Incident
    form_class = IncidentForm
    template_name = 'incidents/incident_form.html'
    success_url = reverse_lazy('incidents:incident_list')

class IncidentDeleteView(DeleteView):
    model = Incident
    template_name = 'incidents/incident_confirm_delete.html'
    success_url = reverse_lazy('incidents:incident_list')