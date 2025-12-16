from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from .forms import DepartmentForm, PositionForm, OrganizationSafetyInfoForm, SiteForm
from .models import Department, Position, OrganizationSafetyInfo, Site


# Create your views here.
def organization_info(request):
    departments = Department.objects.all()
    positions = Position.objects.all()
    safety_info = OrganizationSafetyInfo.objects.first()
    sites = Site.objects.all() if safety_info else []
    return render(request, 'organization/organization_info.html', {
        'departments': departments,
        'positions': positions,
        'safety_info': safety_info,
        'sites': sites
    })


class DepartmentCreateView(CreateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'organization/department_form.html'
    success_url = reverse_lazy('organization:organization_info')


class DepartmentUpdateView(UpdateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'organization/department_form.html'
    success_url = reverse_lazy('organization:organization_info')


class DepartmentDeleteView(DeleteView):
    model = Department
    success_url = reverse_lazy('organization:organization_info')


class PositionCreateView(CreateView):
    model = Position
    form_class = PositionForm
    template_name = 'organization/position_form.html'
    success_url = reverse_lazy('organization:organization_info')


class PositionUpdateView(UpdateView):
    model = Position
    form_class = PositionForm
    template_name = 'organization/position_form.html'
    success_url = reverse_lazy('organization:organization_info')


class PositionDeleteView(DeleteView):
    model = Position
    success_url = reverse_lazy('organization:organization_info')


def safety_info_edit(request):
    # Используем метод, который гарантированно вернет или создаст единственную
    # запись
    safety_info = OrganizationSafetyInfo.load_organization()

    if request.method == 'POST':
        form = OrganizationSafetyInfoForm(
            request.POST, request.FILES, instance=safety_info)
        if form.is_valid():
            form.save()
            return redirect('organization:organization_info')
    else:
        form = OrganizationSafetyInfoForm(instance=safety_info)

    return render(request,
                  'organization/safety_info_form.html',
                  {'form': form,
                   'safety_info': safety_info})  # Передаем safety_info для удобства


class SiteCreateView(CreateView):
    model = Site
    form_class = SiteForm
    template_name = 'organization/site_form.html'
    success_url = reverse_lazy('organization:organization_info')

    def form_valid(self, form):
        # Автоматически привязываем площадку к организации
        safety_info = OrganizationSafetyInfo.objects.first()
        if safety_info:
            form.instance.organization = safety_info
        return super().form_valid(form)


class SiteUpdateView(UpdateView):
    model = Site
    form_class = SiteForm
    template_name = 'organization/site_form.html'
    success_url = reverse_lazy('organization:organization_info')


class SiteDeleteView(DeleteView):
    model = Site
    success_url = reverse_lazy('organization:organization_info')
