from django.urls import path
from .views import (
    IncidentListView,
    IncidentCreateView,
    IncidentUpdateView,
    IncidentDeleteView
)

app_name = 'incidents'

urlpatterns = [
    path('', IncidentListView.as_view(), name='incident_list'),
    path('create/', IncidentCreateView.as_view(), name='incident_create'),
    path('<int:pk>/update/', IncidentUpdateView.as_view(), name='incident_update'),
    path('<int:pk>/delete/', IncidentDeleteView.as_view(), name='incident_delete'),
]
