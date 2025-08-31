from django.shortcuts import render
from .models import Incident


# Create your views here.
def incident_list(request):
    incidents = Incident.objects.all()
    return render(request, 'incidents/incident_list.html', {'incidents': incidents})