from django.shortcuts import render
from .models import SafetyTraining


# Create your views here.
def safety_trainings_list(request):
    trainings = SafetyTraining.objects.all()
    return render(request, 'safety_trainings/safety_trainings_list.html', {'trainings': trainings})