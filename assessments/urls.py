from django.urls import path

from assessments.views import WorkplaceListView, WorkplaceCreateView, WorkplaceUpdateView, SOUTUpdateView

app_name = 'assessments'


urlpatterns = [
    path('workplaces/', WorkplaceListView.as_view(), name='workplace_list'),
    path('workplaces/create/', WorkplaceCreateView.as_view(), name='workplace_create'),
    path('workplaces/<int:pk>/update/', WorkplaceUpdateView.as_view(), name='workplace_update'),
    path('workplaces/<int:pk>/sout/manage/', SOUTUpdateView.as_view(), name='sout_manage'),
]
