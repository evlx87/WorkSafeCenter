from django.shortcuts import render
from django.urls.base import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView

from assessments.models import Workplace, SOUTAssessment


# Create your views here.
class WorkplaceListView(ListView):
    model = Workplace
    template_name = 'assessments/workplace_list.html'
    context_object_name = 'workplaces'


class WorkplaceCreateView(CreateView):
    model = Workplace
    fields = ['number', 'position', 'site']
    template_name = 'assessments/workplace_form.html'
    success_url = reverse_lazy('assessments:workplace_list')


class WorkplaceUpdateView(UpdateView):
    pass


class SOUTUpdateView(UpdateView):
    model = SOUTAssessment
    fields = ['assessment_date', 'next_assessment_date', 'class_conditions', 'report_number', 'file']
    template_name = 'assessments/sout_form.html'

    def get_success_url(self):
        return reverse_lazy('assessments:workplace_list')