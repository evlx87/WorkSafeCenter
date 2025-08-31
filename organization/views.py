from django.shortcuts import render
from .models import Department, Position


# Create your views here.
def organization_info(request):
    departments = Department.objects.all()
    positions = Position.objects.all()
    return render(request, 'organization/organization_info.html', {
        'departments': departments,
        'positions': positions
    })