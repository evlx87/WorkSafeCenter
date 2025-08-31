from django.shortcuts import render
from .models import MedicalCheck


# Create your views here.
def medical_check_list(request):
    medical_checks = MedicalCheck.objects.all()
    return render(request, 'medical_checks/medical_check_list.html', {'medical_checks': medical_checks})