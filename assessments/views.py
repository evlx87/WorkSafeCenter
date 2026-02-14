from datetime import timedelta

from django.db.models import Q
from django.http import HttpResponse
from django.urls.base import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, UpdateView
from django.views.generic import ListView
from django.views.generic import TemplateView

from assessments.models import Workplace, SOUTAssessment
from assessments.services import export_sout_plan_to_excel


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
    model = Workplace
    fields = ['number', 'position', 'site']
    template_name = 'assessments/workplace_form.html'
    success_url = reverse_lazy('assessments:workplace_list')


class SOUTUpdateView(UpdateView):
    model = SOUTAssessment
    fields = ['assessment_date', 'next_assessment_date', 'class_conditions', 'report_number', 'file']
    template_name = 'assessments/sout_form.html'

    def get_success_url(self):
        return reverse_lazy('assessments:workplace_list')


class SOUTPlanningListView(ListView):
    model = Workplace
    template_name = 'assessments/sout_planning.html'
    context_object_name = 'planning_workplaces'

    def get_queryset(self):
        today = timezone.now().date()
        # Порог "подходящего срока" (например, за 60 дней)
        warning_threshold = today + timedelta(days=60)

        # Фильтруем РМ:
        # 1. СОУТ никогда не проводилась (sout__isnull=True)
        # 2. Либо срок следующей СОУТ уже прошел или наступит скоро
        return Workplace.objects.filter(
            Q(sout__isnull=True) |
            Q(sout__next_assessment_date__lte=warning_threshold)
        ).select_related('sout', 'position', 'site')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['today'] = timezone.now().date()
        return context


class SOUTDashboardView(TemplateView):
    template_name = 'assessments/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_wp = Workplace.objects.all()

        # Считаем статистику программно (так как логика статуса в методе объекта)
        stats = {
            'total': all_wp.count(),
            'valid': 0,
            'warning': 0,
            'expired': 0,
            'not_conducted': 0
        }

        for wp in all_wp:
            stats[wp.sout_status] += 1

        context['stats'] = stats
        return context


def export_sout_excel_view(request):
    wb = export_sout_plan_to_excel()
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=sout_plan_{timezone.now().date()}.xlsx'
    wb.save(response)
    return response