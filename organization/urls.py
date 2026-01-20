from django.urls import path

from .views import organization_info, DepartmentCreateView, DepartmentUpdateView, DepartmentDeleteView, \
    PositionCreateView, PositionUpdateView, PositionDeleteView, safety_info_edit, SiteCreateView, SiteUpdateView, \
    SiteDeleteView

app_name = 'organization'

urlpatterns = [
    path('', organization_info, name='organization_info'),
    path('safety-info/edit/', safety_info_edit, name='safety_info_edit'),

    path('department/create/', DepartmentCreateView.as_view(), name='department_create'),
    path('department/<int:pk>/update/', DepartmentUpdateView.as_view(), name='department_update'),
    path('department/<int:pk>/delete/', DepartmentDeleteView.as_view(), name='department_delete'),

    path('position/create/', PositionCreateView.as_view(), name='position_create'),
    path('position/<int:pk>/update/', PositionUpdateView.as_view(), name='position_update'),
    path('position/<int:pk>/delete/', PositionDeleteView.as_view(), name='position_delete'),

    path('site/create/', SiteCreateView.as_view(), name='site_create'),
    path('site/<int:pk>/update/', SiteUpdateView.as_view(), name='site_update'),
    path('site/<int:pk>/delete/', SiteDeleteView.as_view(), name='site_delete'),
]
